import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Set

from geopy.distance import geodesic

from app.alarms.alarm import AlarmManager
from app.logger import get_logger

logger = get_logger("CAMERA")

# Configuration for heatmap_data.json write optimization
BATCH_SIZE = 100  # Number of observations to buffer before writing
FLUSH_INTERVAL = 5.0  # Seconds between forced buffer flushes
MIN_HEATMAP_INTERVAL = 0.1  # Minimum seconds between writes per object


class GlobalObject:
    """Represents an object tracked across multiple cameras with a unique ID."""

    def __init__(self, initial_observation: Dict, camera_id: int):
        """Initialize with an observation and camera ID."""
        self.id = str(uuid.uuid4())
        self.observations: List[Dict] = [initial_observation]
        self.cameras: Set[int] = {camera_id}
        self.last_heatmap_write: float = 0.0  # Timestamp of last heatmap write

    def add_observation(self, observation: Dict, camera_id: int) -> None:
        """Add an observation and update associated cameras."""
        self.observations.append(observation)
        self.cameras.add(camera_id)


class ObjectManager:
    """Manages global object tracking across cameras, handling observations and geopositions.

    Matches observations to existing objects, uses last known geopositions when missing,
    and archives objects no longer observed. Buffers heatmap observations to reduce disk I/O.

    Attributes:
        objects: List of currently tracked GlobalObject instances.
        history: List of archived GlobalObject instances.
        map_manager: MapManager instance for coordinate conversions.
        alarm_manager: AlarmManager instance for triggering alarms.
        heatmap_data_file: Path to heatmap data file.
        _observation_buffer: Buffer for batching heatmap observations.
        _last_flush_time: Timestamp of last buffer flush.
    """

    def __init__(self, map_manager, alarm_manager: AlarmManager):
        """Initialize with map and alarm managers."""
        self.objects: List[GlobalObject] = []
        self.history: List[GlobalObject] = []
        self.map_manager = map_manager
        self.alarm_manager = alarm_manager
        self.heatmap_data_file = os.path.join(
            os.path.dirname(__file__), "..", "heatmap", "heatmap_data.json"
        )
        self._observation_buffer: List[Dict] = []
        self._last_flush_time: float = time.time()

    @staticmethod
    def parse_timestamp(timestamp: str) -> datetime:
        """Parse ISO 8601 timestamp to datetime object.

        Args:
            timestamp: ISO 8601 string (e.g., '2025-05-16T21:10:16.005609Z').

        Returns:
            Datetime object in UTC.
        """
        try:
            return datetime.fromisoformat(timestamp.rstrip("Z")).replace(
                tzinfo=timezone.utc
            )
        except ValueError as e:
            logger.warning(f"Invalid timestamp format: {timestamp}, error: {e}")
            raise

    @staticmethod
    def compute_overlap(bb1: Dict, bb2: Dict) -> float:
        """Compute Intersection over Union (overlap) for two bounding boxes.

        Args:
            bb1: Bounding box with 'left', 'right', 'top', 'bottom' in [0, 1].
            bb2: Second bounding box.

        Returns:
            Overlap score [0, 1].
        """
        x_left = max(bb1["left"], bb2["left"])
        x_right = min(bb1["right"], bb2["right"])
        y_top = max(bb1["top"], bb2["top"])
        y_bottom = min(bb1["bottom"], bb2["bottom"])

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = (bb1["right"] - bb1["left"]) * (bb1["bottom"] - bb1["top"])
        area2 = (bb2["right"] - bb2["left"]) * (bb2["bottom"] - bb2["top"])
        union_area = area1 + area2 - intersection_area

        return intersection_area / union_area if union_area > 0 else 0.0
    
    @staticmethod
    def check_if_same_observation(obs1: Dict, obs2: Dict) -> bool:
        """Check if two observations from different cameras represent the same object.

        Compares timestamp, geoposition, class, colors (exact match), and bounding box (overlap).
        Handles partial data by adjusting weights dynamically.

        Args:
            obs1: First observation dictionary (e.g., {"bounding_box": {...}, "timestamp": "..."}).
            obs2: Second observation dictionary.

        Returns:
            bool: True if observations are likely the same object.
        """
        # Configuration
        THRESHOLD = 0.75  # Similarity score threshold
        WEIGHTS = {
            "timestamp": 0.25,  # Temporal proximity
            "geoposition": 0.35,  # Most reliable when available
            "class": 0.20,  # Object type
            "colors": 0.15,  # Clothing colors (exact match)
            "bounding_box": 0.05,  # Overlap-based
        }
        MAX_TIME_DELTA = 1.0  # Max time difference (seconds)
        MAX_GEO_DISTANCE = 1.5  # Max geolocation distance (meters)
        MIN_OVERLAP = 0.2  # Minimum overlap for bounding box match

        score = 0.0
        total_weight = 0.0

        # Timestamp comparison
        try:
            ts1 = ObjectManager.parse_timestamp(obs1.get("timestamp"))
            ts2 = ObjectManager.parse_timestamp(obs2.get("timestamp"))
            time_delta = abs((ts1 - ts2).total_seconds())
            time_score = max(0.0, 1.0 - time_delta / MAX_TIME_DELTA)
            score += WEIGHTS["timestamp"] * time_score
            total_weight += WEIGHTS["timestamp"]
        except Exception as e:
            logger.debug(f"Timestamp comparison failed: {e}")

        # Geoposition comparison
        geo1 = obs1.get("geoposition", {})
        geo2 = obs2.get("geoposition", {})
        if (
            geo1.get("latitude") is not None
            and geo1.get("longitude") is not None
            and geo2.get("latitude") is not None
            and geo2.get("longitude") is not None
        ):
            try:
                dist = geodesic(
                    (geo1["latitude"], geo1["longitude"]),
                    (geo2["latitude"], geo2["longitude"]),
                ).meters
                geo_score = max(0.0, 1.0 - dist / MAX_GEO_DISTANCE)
                score += WEIGHTS["geoposition"] * geo_score
                total_weight += WEIGHTS["geoposition"]
            except Exception as e:
                logger.warning(f"Geolocation comparison failed: {e}")
        else:
            logger.debug("Missing geoposition in one or both observations")

        # Class comparison
        class1 = obs1.get("class", {}).get("type")
        class2 = obs2.get("class", {}).get("type")
        if class1 and class2:
            class_score = 1.0 if class1 == class2 else 0.0
            score += WEIGHTS["class"] * class_score
            total_weight += WEIGHTS["class"]
        else:
            logger.debug("Missing class in one or both observations")

        # Color comparison (exact match)
        color_score = 0.0
        color_count = 0
        for field in ["upper_clothing_colors", "lower_clothing_colors"]:
            colors1 = obs1.get("class", {}).get(field, [])
            colors2 = obs2.get("class", {}).get(field, [])
            if colors1 and colors2:
                name1 = colors1[0]["name"] if colors1 else ""
                name2 = colors2[0]["name"] if colors2 else ""
                similarity = 1.0 if name1.lower() == name2.lower() else 0.0
                color_score += similarity
                color_count += 1
        if color_count > 0:
            score += WEIGHTS["colors"] * (color_score / color_count)
            total_weight += WEIGHTS["colors"]
        else:
            logger.debug("No matching colors available")

        # Bounding box comparison (overlap)
        bb1 = obs1.get("bounding_box")
        bb2 = obs2.get("bounding_box")
        if bb1 and bb2:
            try:
                overlap = ObjectManager.compute_overlap(bb1, bb2)
                bb_score = 1.0 if overlap >= MIN_OVERLAP else 0.0
                score += WEIGHTS["bounding_box"] * bb_score
                total_weight += WEIGHTS["bounding_box"]
            except Exception as e:
                logger.warning(f"Bounding box comparison failed: {e}")
        else:
            logger.debug("Missing bounding box in one or both observations")

        # Normalize score
        final_score = score / total_weight if total_weight > 0 else 0.0
        is_same = final_score >= THRESHOLD
        logger.debug(
            f"Observation comparison: score={final_score:.3f}, threshold={THRESHOLD}, same={is_same}"
        )
        return is_same


    def _prune_history(self) -> None:
        """Remove archived objects older than 15 seconds."""
        current_time = time.time()
        self.history = [
            obj
            for obj in self.history
            if hasattr(obj, "archived_at") and (current_time - obj.archived_at) <= 15
        ]

    def _flush_buffer(self) -> None:
        """Write buffered observations to heatmap_data.json and clear buffer."""
        if not self._observation_buffer:
            return

        try:
            with open(self.heatmap_data_file, "a", encoding="utf-8") as file:
                for observation in self._observation_buffer:
                    file.write(json.dumps(observation, ensure_ascii=False) + "\n")
            logger.debug(
                f"Flushed {len(self._observation_buffer)} observations to {self.heatmap_data_file}"
            )
        except IOError as e:
            logger.error(f"Error flushing buffer to {self.heatmap_data_file}: {e}")
        finally:
            self._observation_buffer.clear()
            self._last_flush_time = time.time()

    def _save_observations(
        self, observations: List[Dict], obj: GlobalObject | None = None
    ) -> None:
        """Buffer observations for heatmap, writing when batch size or time interval is reached.

        Args:
            observations: List of observation dictionaries.
            obj: Associated GlobalObject for time-based sampling (optional).
        """
        current_time = time.time()

        for observation in observations:
            # Skip if observation lacks valid geoposition
            if not self._is_valid_geoposition(observation.get("geoposition", {})):
                continue

            # Apply time-based sampling if associated with a GlobalObject
            if obj and (current_time - obj.last_heatmap_write) < MIN_HEATMAP_INTERVAL:
                continue

            self._observation_buffer.append(observation)
            if obj:
                obj.last_heatmap_write = current_time

        # Flush buffer if size or time interval exceeded
        if (
            len(self._observation_buffer) >= BATCH_SIZE
            or (current_time - self._last_flush_time) >= FLUSH_INTERVAL
        ):
            self._flush_buffer()

    def _is_valid_geoposition(self, geoposition: Dict) -> bool:
        """Check if geoposition has non-null latitude and longitude."""
        return (
            isinstance(geoposition, dict)
            and geoposition.get("latitude") is not None
            and geoposition.get("longitude") is not None
        )

    def _get_last_geoposition(self, obj: GlobalObject) -> Dict | None:
        """Retrieve the most recent valid geoposition from an object's observations."""
        for observation in reversed(obj.observations):
            if self._is_valid_geoposition(observation.get("geoposition", {})):
                return observation["geoposition"]
        return None

    def _trigger_alarms(self, geoposition: Dict) -> None:
        """Convert geoposition to relative coordinates and check alarms."""
        try:
            relative_pos = self.map_manager.convert_to_relative(
                (geoposition["latitude"], geoposition["longitude"])
            )
            self.alarm_manager.check_alarms(relative_pos)
        except Exception as e:
            logger.error(f"Error triggering alarms for geoposition {geoposition}: {e}")

    def add_observations(self, camera_id: int, observations: List[Dict]) -> None:
        """Add camera observations, matching to existing objects or creating new ones.

        Uses last known geoposition for matched observations lacking valid geoposition.
        Buffers observations for heatmap with time-based sampling.

        Args:
            camera_id: ID of the observing camera.
            observations: List of observation dictionaries.
        """
        self._prune_history()
        prev_seen = {obj.id: obj for obj in self.objects if camera_id in obj.cameras}
        matched_ids = set()
        new_observations = []

        for observation in observations:
            observation = observation.copy()
            observation["camera_id"] = camera_id  # Add for potential use
            geoposition = observation.get("geoposition", {})

            # Try to resurrect from history
            for hist_obj in self.history[:]:
                if ObjectManager.check_if_same_observation(
                    hist_obj.observations[-1], observation
                ):
                    if not self._is_valid_geoposition(geoposition):
                        geoposition = (
                            self._get_last_geoposition(hist_obj) or geoposition
                        )
                        observation["geoposition"] = geoposition
                    hist_obj.add_observation(observation, camera_id)
                    self.history.remove(hist_obj)
                    self.objects.append(hist_obj)
                    matched_ids.add(hist_obj.id)
                    if self._is_valid_geoposition(observation["geoposition"]):
                        self._save_observations(
                            [observation], hist_obj
                        )  # Buffer with sampling
                        self._trigger_alarms(observation["geoposition"])
                    break
            else:
                # Match with existing objects
                for obj in self.objects:
                    if ObjectManager.check_if_same_observation(
                        obj.observations[-1], observation
                    ):
                        if not self._is_valid_geoposition(geoposition):
                            geoposition = self._get_last_geoposition(obj) or geoposition
                            observation["geoposition"] = geoposition
                        obj.add_observation(observation, camera_id)
                        matched_ids.add(obj.id)
                        if self._is_valid_geoposition(observation["geoposition"]):
                            self._save_observations(
                                [observation], obj
                            )  # Buffer with sampling
                            self._trigger_alarms(observation["geoposition"])
                        break
                else:
                    # Create new object if geoposition is valid
                    if self._is_valid_geoposition(geoposition):
                        new_observations.append(observation)
                        new_obj = GlobalObject(observation, camera_id)
                        self.objects.append(new_obj)
                        matched_ids.add(new_obj.id)
                        self._save_observations(
                            [observation], new_obj
                        )  # Buffer with sampling
                        self._trigger_alarms(geoposition)
                    else:
                        logger.debug(
                            f"Skipping observation without valid geoposition: {observation}"
                        )
                        continue

        # Archive objects no longer observed by this camera
        for obj_id, obj in prev_seen.items():
            if obj_id not in matched_ids:
                obj.cameras.discard(camera_id)
                if not obj.cameras:
                    self.objects.remove(obj)
                    obj.archived_at = time.time()
                    self.history.append(obj)

        # Flush remaining buffer if new observations were added
        if new_observations:
            self._flush_buffer()

    def get_objects_by_camera(self, camera_id: int) -> List[Dict]:
        """Get objects observed by a specific camera.

        Args:
            camera_id: ID of the camera.

        Returns:
            List of dictionaries with object ID, class, geoposition, and bounding box.
        """
        return [
            {
                "id": obj.id,
                "class": obj.observations[-1].get("class", {}),
                "geoposition": obj.observations[-1].get("geoposition", {}),
                "bounding_box": obj.observations[-1].get("bounding_box", {}),
            }
            for obj in self.objects
            if camera_id in obj.cameras
        ]

    def get_all_objects(self) -> List[Dict]:
        """Get all objects across all cameras.

        Returns:
            List of dictionaries with camera ID, object ID, and geoposition.
        """
        return [
            {
                "camera_id": camera_id,
                "id": obj.id,
                "geoposition": obj.observations[-1].get("geoposition", {}),
            }
            for obj in self.objects
            for camera_id in obj.cameras
        ]

    def get_objects_geoposition(self, camera_id: int) -> List[Dict]:
        """Get geopositions of objects observed by a specific camera.

        Args:
            camera_id: ID of the camera.

        Returns:
            List of dictionaries with object ID and geoposition.
        """
        return [
            {
                "id": obj.id,
                "geoposition": obj.observations[-1].get("geoposition", {}),
            }
            for obj in self.objects
            if camera_id in obj.cameras
        ]

    def get_history(self) -> List[Dict]:
        """Get archived objects no longer in view.

        Returns:
            List of dictionaries with object ID, observations, and cameras.
        """
        self._prune_history()
        return [
            {
                "id": obj.id,
                "observations": obj.observations,
                "cameras": list(obj.cameras),
            }
            for obj in self.history
        ]

    def __del__(self):
        """Ensure buffer is flushed when ObjectManager is destroyed."""
        self._flush_buffer()
