# New file for managing global object tracking
import uuid
from typing import List, Dict
from app.utils.helper import check_if_same_observation
import time
import json


class GlobalObject:
    """ "Represents a global object observed by multiple cameras.
    Each object has a unique ID and can have multiple observations from different cameras.
    """

    def __init__(self, initial_obs: Dict, camera_id: int):
        self.id = str(uuid.uuid4())
        self.observations: List[Dict] = []
        self.cameras: set = set()
        self.add_observation(initial_obs, camera_id)

    def add_observation(self, obs: Dict, camera_id: int):
        self.observations.append(obs)
        self.cameras.add(camera_id)


class ObjectManager:
    """
    Manages global object tracking across multiple cameras.
    Each camera can add observations, and the manager will track the objects
    Will always check if the observations are the same if the same the are not added.
    """

    def __init__(self):
        self.objects: List[GlobalObject] = []
        # archive of objects no longer in any camera view
        self.history: List[GlobalObject] = []

    def _prune_history(self):
        """Remove archived objects older than 15 seconds"""
        now = time.time()
        self.history = [
            obj
            for obj in self.history
            if hasattr(obj, "archived_at") and (now - obj.archived_at) <= 15
        ]

    def save_obj(self, obj):
        """
        * saves object to a json file.
        """

        def append_json_line(entry: dict):
            with open("heatmap_data.jl", "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if obj:
            append_json_line(obj)

    def add_observations(self, camera_id: int, obs_list: List[Dict]) -> None:
        """Add observations from a camera to the global object list.
        If the observation is similar to an existing one, it will be added to that object.

        Args:
            camera_id (int): ID of the camera
            obs_list (List[Dict]): List of observations from the camera, each represented as a dictionary
        """
        # list of object to save
        save_obj_list = []
        # prune old history entries
        self._prune_history()
        # track objects previously seen by this camera
        prev_seen = [obj for obj in self.objects if camera_id in obj.cameras]
        matched_ids = set()
        for obs in obs_list:
            # resurrect archived object if same observation appears
            resurrected = False
            for hist_obj in list(self.history):
                last_hist = hist_obj.observations[-1]
                if check_if_same_observation(last_hist, obs):
                    hist_obj.add_observation(obs, camera_id)
                    matched_ids.add(hist_obj.id)
                    self.history.remove(hist_obj)
                    self.objects.append(hist_obj)
                    resurrected = True
                    break
            if resurrected:
                continue
            matched = False
            for obj in self.objects:
                last_obs = obj.observations[-1]
                if check_if_same_observation(last_obs, obs):
                    obj.add_observation(obs, camera_id)
                    matched_ids.add(obj.id)
                    matched = True
                    break
            if not matched:
                save_obj_list.append(obs)
                globa_obj = GlobalObject(obs, camera_id)
                self.objects.append(globa_obj)
                matched_ids.add(self.objects[-1].id)
        # remove camera from objects no longer observed
        for obj in prev_seen:
            if obj.id not in matched_ids:
                obj.cameras.discard(camera_id)
                # if no cameras left, archive object
                if not obj.cameras:
                    self.objects.remove(obj)
                    obj.archived_at = time.time()
                    self.history.append(obj)
        self.save_obj(save_obj_list)

    def get_objects_by_camera(self, camera_id: int) -> List[Dict]:
        """Get all objects observed by a specific camera.

        Args:
            camera_id (int): ID of the camera

        Returns:
            List[Dict]: List of objects observed by the camera, each represented as a dictionary
            eg [{"id": "1", "class": {...}, "geoposition": {...}, "bounding_box": {...}]
        """
        result = []
        for obj in self.objects:
            if camera_id in obj.cameras:
                last_obs = obj.observations[-1]
                result.append(
                    {
                        "id": obj.id,
                        "class": last_obs.get("class", {}),
                        "geoposition": last_obs.get("geoposition", {}),
                        "bounding_box": last_obs.get("bounding_box", {}),
                    }
                )
        return result

    def get_all_objects(self) -> List[Dict]:
        """Returns all cameras and their observations.
        in the form of [{"camera_id": 1, "id", "geoposition": {...}}]

        Returns:
            List[Dict]: _description_
        """
        result = []
        for obj in self.objects:
            for camera_id in obj.cameras:
                last_obs = obj.observations[-1]
                result.append(
                    {
                        "camera_id": camera_id,
                        "id": obj.id,
                        "geoposition": last_obs.get("geoposition", {}),
                    }
                )
        return result

    def get_objects_geoposition(self, camera_id: int) -> List[Dict]:
        """Get all objects observed by a specific camera with only their geocoordinates.

        Args:
            camera_id (int): ID of the camera

        Returns:
            List[Dict]: List of objects observed by the camera, each represented as a dictionary
            eg [{"id": "1", "geoposition": {...}]
        """
        result = []
        for obj in self.objects:
            if camera_id in obj.cameras:
                last_obs = obj.observations[-1]
                result.append(
                    {
                        "id": obj.id,
                        "geoposition": last_obs.get("geoposition", {}),
                    }
                )
        return result

    def get_history(self) -> List[Dict]:
        """Return archived objects no longer in view."""
        # prune old history entries before returning
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
