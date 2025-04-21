import unittest
from object_manager import ObjectManager
from helper import check_if_same_observation


class TestObjectManager(unittest.TestCase):
    def setUp(self):
        self.om = ObjectManager()
        # two observations that differ only by tiny geoposition — considered "same"
        self.obs1 = {
            "geoposition": {"latitude": 10.0, "longitude": 20.0},
            "class": {
                "lower_clothing_colors": [{"name": "Black", "score": 0.6}],
                "score": 0.92,
                "type": "Human",
                "upper_clothing_colors": [{"name": "Gray", "score": 0.71}],
            },
            "bounding_box": {"x": 1, "y": 2, "w": 3, "h": 4},
        }
        self.obs1_similar = {
            "geoposition": {"latitude": 10.00001, "longitude": 20.00001},
            "class": {
                "lower_clothing_colors": [{"name": "Black", "score": 0.6}],
                "score": 0.92,
                "type": "Human",
                "upper_clothing_colors": [{"name": "Gray", "score": 0.71}],
            },
            "bounding_box": {"x": 1, "y": 2, "w": 3, "h": 4},
        }
        # clearly different observation
        self.obs2 = {
            "geoposition": {"latitude": 30.0, "longitude": 40.0},
            "class": {
                "lower_clothing_colors": [{"name": "Red", "score": 0.7}],
                "score": 0.95,
                "type": "Animal",
                "upper_clothing_colors": [{"name": "Brown", "score": 0.65}],
            },
            "bounding_box": {"x": 5, "y": 6, "w": 7, "h": 8},
        }

    def test_add_single_observation(self):
        self.om.add_observations(camera_id=1, obs_list=[self.obs1])
        # debug print
        print("=== test_add_single_observation ===")
        print(
            "Objects:",
            [(o.id, len(o.observations), o.cameras) for o in self.om.objects],
        )
        objs = self.om.get_objects_by_camera(1)
        print("get_objects_by_camera(1):", objs)

        self.assertEqual(len(objs), 1)
        obj = objs[0]
        self.assertIn("id", obj)
        self.assertEqual(obj["class"], self.obs1["class"])
        self.assertEqual(obj["geoposition"], self.obs1["geoposition"])
        self.assertEqual(obj["bounding_box"], self.obs1["bounding_box"])

    def test_merge_similar_observations(self):
        self.om.add_observations(1, [self.obs1])
        self.om.add_observations(1, [self.obs1_similar])
        # debug print
        print("=== test_merge_similar_observations ===")
        print(
            "Objects:",
            [(o.id, len(o.observations), o.cameras) for o in self.om.objects],
        )

        self.assertEqual(len(self.om.objects), 1)
        global_obj = self.om.objects[0]
        self.assertEqual(len(global_obj.observations), 2)
        self.assertTrue(
            check_if_same_observation(
                global_obj.observations[0], global_obj.observations[1]
            )
        )

    def test_create_new_for_different_observation(self):
        self.om.add_observations(1, [self.obs1])
        self.om.add_observations(1, [self.obs2])
        # debug print
        print("=== test_create_new_for_different_observation ===")
        print(
            "Objects:",
            [(o.id, len(o.observations), o.cameras) for o in self.om.objects],
        )

        self.assertEqual(len(self.om.objects), 2)

    def test_multiple_cameras_tracking(self):
        self.om.add_observations(1, [self.obs1])
        self.om.add_observations(2, [self.obs1_similar])
        # debug print
        print("=== test_multiple_cameras_tracking ===")
        print(
            "Objects:",
            [(o.id, len(o.observations), o.cameras) for o in self.om.objects],
        )
        print("-------------------------------------------------------")

        print("get_objects_by_camera(1):", self.om.get_objects_by_camera(1))
        print("-------------------------------------------------------")
        print("get_objects_by_camera(2):", self.om.get_objects_by_camera(2))

        self.assertEqual(len(self.om.objects), 1)
        go = self.om.objects[0]
        self.assertEqual(go.cameras, {1, 2})
        self.assertEqual(len(self.om.get_objects_by_camera(1)), 1)
        self.assertEqual(len(self.om.get_objects_by_camera(2)), 1)


if __name__ == "__main__":
    unittest.main()
