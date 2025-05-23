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
        """Add an observation and update associated cameras, only if newer and position changed."""
        last_obs = self.observations[-1]
        last_obs_time = last_obs.get("timestamp")
        new_obs_time = observation.get("timestamp")
        if new_obs_time is not None and last_obs_time is not None:
            if new_obs_time <= last_obs_time:
                return  # Do not add if not newer

        # Only add if geoposition has changed
        last_geo = last_obs.get("geoposition", {})
        new_geo = observation.get("geoposition", {})
        if (
            last_geo.get("latitude") == new_geo.get("latitude")
            and last_geo.get("longitude") == new_geo.get("longitude")
        ):
            return  # Do not add if position is unchanged

        self.observations.append(observation)
        self.cameras.add(camera_id)


class ObjectManager:
    """Manages global object tracking across cameras, handling observations and geopositions.

    Matches observations to existing objects, uses last known geopositions when missing,
    and archives objects no longer observed. Buffers heatmap observations to reduce disk I/O.

    Attributes:
        objects: List of currently tracked GlobalObject instances.
        map_manager: MapManager instance for coordinate conversions.
        alarm_manager: AlarmManager instance for triggering alarms.
        heatmap_data_file: Path to heatmap data file.
        _observation_buffer: Buffer for batching heatmap observations.
        _last_flush_time: Timestamp of last buffer flush.
    """

    def __init__(self, map_manager, alarm_manager: AlarmManager):
        """Initialize with map and alarm managers."""
        self.objects: List[GlobalObject] = []
        self.map_manager = map_manager
        self.alarm_manager = alarm_manager
        self.heatmap_data_file = os.path.join(
            os.path.dirname(__file__), "..", "heatmap", "heatmap_data.json"
        )
        self._observation_buffer: List[Dict] = []
        self._last_flush_time: float = time.time()

    @staticmethod
    def check_if_same_observation(obs1: dict, obs2: dict) -> bool:
        """Checks if two different observations are of the same object.
        Same if geocoords are max 1 m apart and clothing colors match.
        """
        max_distance = 1 # meters

        obs1_coords = obs1.get("geoposition", {})
        obs2_coords = obs2.get("geoposition", {})

        obs1_coords = (obs1_coords.get("latitude"), obs1_coords.get("longitude"))
        obs2_coords = (obs2_coords.get("latitude"), obs2_coords.get("longitude"))

        geodesic_distance = geodesic(obs1_coords, obs2_coords).meters

        if geodesic_distance > max_distance:
            return False

        return True

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
        prev_seen = {obj.id: obj for obj in self.objects if camera_id in obj.cameras}
        matched_ids = set()
        new_observations = []

        for observation in observations:
            observation = observation.copy()
            observation["camera_id"] = camera_id  # Add for potential use
            geoposition = observation.get("geoposition", {})

            # Only match with existing objects
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
        """Get all unique objects across all cameras.

        Returns:
            List of dictionaries with camera ID, object ID, and geoposition.
        """
        result = []
        for obj in self.objects:
            last_obs = obj.observations[-1]
            result.append({
                "camera_id": last_obs.get("camera_id"),
                "id": obj.id,
                "geoposition": last_obs.get("geoposition", {}),
            })
        return result

    def __del__(self):
        """Ensure buffer is flushed when ObjectManager is destroyed."""
        self._flush_buffer()
