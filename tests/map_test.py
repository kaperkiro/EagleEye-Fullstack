    """
    Unit tests for the Map class in the map module. Doesnt work in current folder... 
    """
import unittest
from map import Map


class TestMapConverter(unittest.TestCase):
    def setUp(self):
        # Define a map with known corners (TL, BL, TR, BR)
        self.test_map = Map(
            name="Test Room",
            corner_coords=[
                (59.3250, 18.0700),  # top-left
                (59.3240, 18.0700),  # bottom-left
                (59.3250, 18.0710),  # top-right
                (59.3240, 18.0710),  # bottom-right
            ],
            file_path="test_map.png",
        )

    def test_center_point(self):
        # Point roughly in the center of the map
        point = (59.3245, 18.0705)
        u, v = self.test_map.convert_to_relative(point)
        self.assertAlmostEqual(u, 50.0, places=1)
        self.assertAlmostEqual(v, 50.0, places=1)

    def test_top_left(self):
        point = (59.3250, 18.0700)
        u, v = self.test_map.convert_to_relative(point)
        self.assertAlmostEqual(u, 0.0, places=1)
        self.assertAlmostEqual(v, 0.0, places=1)

    def test_bottom_right(self):
        point = (59.3240, 18.0710)
        u, v = self.test_map.convert_to_relative(point)
        self.assertAlmostEqual(u, 100.0, places=1)
        self.assertAlmostEqual(v, 100.0, places=1)

    def test_top_right(self):
        point = (59.3250, 18.0710)
        u, v = self.test_map.convert_to_relative(point)
        self.assertAlmostEqual(u, 100.0, places=1)
        self.assertAlmostEqual(v, 0.0, places=1)

    def test_bottom_left(self):
        point = (59.3240, 18.0700)
        u, v = self.test_map.convert_to_relative(point)
        self.assertAlmostEqual(u, 0.0, places=1)
        self.assertAlmostEqual(v, 100.0, places=1)


if __name__ == "__main__":
    unittest.main()
