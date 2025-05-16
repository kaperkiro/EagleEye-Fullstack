import json
import os
import time
import uuid
from typing import Dict, List

from app.alarms.alarm import AlarmManager
from app.utils.helper import check_if_same_observation


class GlobalObject:
    """Represents an object tracked across multiple cameras with a unique ID."""

    def __init__(self, initial_observation: Dict, camera_id: int):
        self.id = str(uuid.uuid4())
        self.observations: List[Dict] = [initial_observation]
        self.cameras: set = {camera_id}

    def add_observation(self, observation: Dict, camera_id: int) -> None:
        """Add an observation and update associated cameras."""
        self.observations.append(observation)
        self.cameras.add(camera_id)


class ObjectManager:
    """Manages global object tracking across cameras, handling observations and geopositions.

    Matches observations to existing objects, uses last known geopositions when missing,
    and archives objects no longer observed.
    """

    def __init__(self, map_manager, alarm_manager: AlarmManager):
        self.objects: List[GlobalObject] = []
        self.history: List[GlobalObject] = []
        self.map_manager = map_manager
        self.alarm_manager = alarm_manager

    def _prune_history(self) -> None:
        """Remove archived objects older than 15 seconds."""
        current_time = time.time()
        self.history = [
            obj for obj in self.history
            if hasattr(obj, "archived_at") and (current_time - obj.archived_at) <= 15
        ]

    def _save_observations(self, observations: List[Dict]) -> None:
        """Append observations to heatmap_data.jl."""
        if not observations:
            return
        here = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(here, "heatmap_data.jl")
        with open(data_file, "a") as file:
            for observation in observations:
                file.write(json.dumps(observation, ensure_ascii=False) + "\n")

    def _is_valid_geoposition(self, geoposition: Dict) -> bool:
        """Check if geoposition has non-null latitude and longitude."""
        return (
            isinstance(geoposition, dict) and
            geoposition.get("latitude") is not None and
            geoposition.get("longitude") is not None
        )

    def _get_last_geoposition(self, obj: GlobalObject) -> Dict | None:
        """Retrieve the most recent valid geoposition from an object's observations."""
        for observation in reversed(obj.observations):
            if self._is_valid_geoposition(observation.get("geoposition", {})):
                return observation["geoposition"]
        return None

    def _trigger_alarms(self, geoposition: Dict) -> None:
        """Convert geoposition to relative coordinates and check alarms."""
        relative_pos = self.map_manager.convert_to_relative(
            (geoposition["latitude"], geoposition["longitude"])
        )
        self.alarm_manager.check_alarms(relative_pos)

    def add_observations(self, camera_id: int, observations: List[Dict]) -> None:
        """Add camera observations, matching to existing objects or creating new ones.

        Uses last known geoposition for matched observations lacking valid geoposition.
        Skips new observations without valid geoposition.

        Args:
            camera_id: ID of the observing camera.
            observations: List of observation dictionaries.
        """
        self._prune_history()
        prev_seen = {obj.id: obj for obj in self.objects if camera_id in obj.cameras}
        matched_ids = set()
        new_observations = []

        for observation in observations:
            observation = observation.copy()  # Avoid modifying input
            geoposition = observation.get("geoposition", {})

            # Try to resurrect from history
            for hist_obj in self.history[:]:
                if check_if_same_observation(hist_obj.observations[-1], observation):
                    if not self._is_valid_geoposition(geoposition):
                        geoposition = self._get_last_geoposition(hist_obj) or geoposition
                        observation["geoposition"] = geoposition
                    hist_obj.add_observation(observation, camera_id)
                    self.history.remove(hist_obj)
                    self.objects.append(hist_obj)
                    matched_ids.add(hist_obj.id)
                    if self._is_valid_geoposition(observation["geoposition"]):
                        self._trigger_alarms(observation["geoposition"])
                    break
            else:
                # Match with existing objects
                for obj in self.objects:
                    if check_if_same_observation(obj.observations[-1], observation):
                        if not self._is_valid_geoposition(geoposition):
                            geoposition = self._get_last_geoposition(obj) or geoposition
                            observation["geoposition"] = geoposition
                        obj.add_observation(observation, camera_id)
                        matched_ids.add(obj.id)
                        if self._is_valid_geoposition(observation["geoposition"]):
                            self._trigger_alarms(observation["geoposition"])
                        break
                else:
                    # Create new object if geoposition is valid
                    if self._is_valid_geoposition(geoposition):
                        new_observations.append(observation)
                        new_obj = GlobalObject(observation, camera_id)
                        self.objects.append(new_obj)
                        matched_ids.add(new_obj.id)
                        self._trigger_alarms(geoposition)
                    else:
                        print(f"Warning: Skipping new observation without valid geoposition: {observation}")

        # Archive objects no longer observed by this camera
        for obj_id, obj in prev_seen.items():
            if obj_id not in matched_ids:
                obj.cameras.discard(camera_id)
                if not obj.cameras:
                    self.objects.remove(obj)
                    obj.archived_at = time.time()
                    self.history.append(obj)

        self._save_observations(new_observations)

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


def test_global_object():
    # Example usage
    obs1 = {
        "geoposition": {"latitude": 59.3250, "longitude": 18.0700},
        "class": {
            "type": "Human",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Blue", "score": 0.7}],
        },
    }

    obs2 = {
        "geoposition": {"latitude": 59.32501, "longitude": 18.07001},
        "class": {
            "type": "Human",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Blue", "score": 0.7}],
        },
    }

    obj = GlobalObject(obs1, camera_id=1)
    obj.add_observation(obs2, camera_id=2)

    print("Global Object ID:", obj.id)
    print("Observations:", obj.observations)
    print("Cameras:", obj.cameras)


def test_object_manager():
    om = ObjectManager()
    obs1 = {
        "geoposition": {"latitude": 59.3250, "longitude": 18.0700},
        "class": {
            "type": "Human",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Blue", "score": 0.7}],
        },
    }

    obs2 = {
        "geoposition": {"latitude": 59.32501, "longitude": 18.07001},
        "class": {
            "type": "Human",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Blue", "score": 0.7}],
        },
    }

    # clearly different observation
    obs3 = {
        "geoposition": {"latitude": 30.0, "longitude": 40.0},
        "class": {
            "lower_clothing_colors": [{"name": "Red", "score": 0.7}],
            "score": 0.95,
            "type": "Animal",
            "upper_clothing_colors": [{"name": "Brown", "score": 0.65}],
        },
        "bounding_box": {"x": 5, "y": 6, "w": 7, "h": 8},
    }
    om.add_observations(camera_id=1, obs_list=[obs1, obs3])
    om.add_observations(camera_id=2, obs_list=[obs2])

    print("Global Objects:", om.objects)
    print("Objects by Camera ID 1:", om.get_objects_by_camera(1))
    print("Objects by Camera ID 2:", om.get_objects_by_camera(2))
    print("Archived Objects:", om.get_history())


def test_getting_all():
    om = ObjectManager()
    obs1 = {
        "geoposition": {"latitude": 59.3250, "longitude": 18.0700},
        "class": {
            "type": "Human",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Blue", "score": 0.7}],
        },
    }

    obs2 = {
        "geoposition": {"latitude": 59.32501, "longitude": 18.07001},
        "class": {
            "type": "Human",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Blue", "score": 0.7}],
        },
    }

    # clearly different observation
    obs3 = {
        "geoposition": {"latitude": 30.0, "longitude": 40.0},
        "class": {
            "lower_clothing_colors": [{"name": "Red", "score": 0.7}],
            "score": 0.95,
            "type": "Animal",
            "upper_clothing_colors": [{"name": "Brown", "score": 0.65}],
        },
        "bounding_box": {"x": 5, "y": 6, "w": 7, "h": 8},
    }
    om.add_observations(camera_id=1, obs_list=[obs1, obs3])
    om.add_observations(camera_id=2, obs_list=[obs2])

    print("All Objects:", om.get_all_objects())


if __name__ == "__main__":
    # test_global_object()
    # print("<------Testing ObjectManager------>")
    # test_object_manager()
    test_getting_all()
