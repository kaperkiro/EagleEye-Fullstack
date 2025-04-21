# New file for managing global object tracking
import uuid
from typing import List, Dict
from helper import check_if_same_observation


class GlobalObject:
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

    def add_observations(self, camera_id: int, obs_list: List[Dict]) -> None:
        for obs in obs_list:
            matched = False
            for obj in self.objects:
                last_obs = obj.observations[-1]
                if check_if_same_observation(last_obs, obs):
                    obj.add_observation(obs, camera_id)
                    matched = True
                    break
            if not matched:
                self.objects.append(GlobalObject(obs, camera_id))

    def get_objects_by_camera(self, camera_id: int) -> List[Dict]:
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


if __name__ == "__main__":
    test_global_object()
    print("<------Testing ObjectManager------>")
    test_object_manager()
