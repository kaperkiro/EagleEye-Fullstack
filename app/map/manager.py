import math
import os
import json
import logging
from app.map.map_config_gui import MapConfigGUI

logger = logging.getLogger(__name__)

class MapManager:
    def __init__(self):
        """Holds the current map used in the frontend to convert to relative xy coordinates
        instead of absolute geocoordinates.

        Args:
            name (str): name of the map
            corner_coords (list): list of corner coordinates of the map in the format [tl, bl, tr, br]
                where tl = top left, bl = bottom left, tr = top right, br = bottom right. Example:
                corner_coords = [(lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4)]
                Technically br is not needed
            file_path (str): filepath of the image file of the map
            camera_geocoords (dict): dictionary of camera geocoordinates in the format {camera_id: (lat, lon)}
        """
        self.map_config = self.load_map_config()
        self.name = self.map_config["name"]
        self.corner_coords = [(lat, lon) for lat, lon in self.map_config["corners"]] # [(lat, lon), ...] in order TL, TR, BR, BL
        self.file_path = self._get_floor_plan()  # Get the floor plan image file path
        self.camera_relative_coords = {}
        for camera_id, camera_data in self.map_config["cameras"].items():
            self.camera_relative_coords[int(camera_id)] = {"x": camera_data["pixel_percent"][0], 
                                                           "y": camera_data["pixel_percent"][1], 
                                                           "heading": camera_data["heading"]}

    def _get_floor_plan(self):
        """Get the floor plan of the map."""
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets")) # get the assets dir
        for ext in ("png", "jpg"):
            floor_plan = os.path.join(assets_dir, f"floor_plan.{ext}")
            if os.path.exists(floor_plan):
                return floor_plan
        raise FileNotFoundError(f"Floor plan not found in {assets_dir}. Please add a floor_plan.png or floor_plan.jpg.")

    def convert_to_relative(self, coords: tuple) -> tuple:
        map_corners = self.map_config["image_corners"]
        tl, tr, br, bl = map_corners
        lat0, lon0 = tl
        lat1, lon1 = tr
        lat2, lon2 = br
        lat3, lon3 = bl

        lat, lon = coords

        # difference in lat/lon from the top-left corner
        dlat = lat0 - lat
        dlon = lon - lon0

        # calculate the width and height of the map in degrees
        width = math.sqrt((lat1 - lat0) ** 2 + (lon1 - lon0) ** 2)
        height = math.sqrt((lat3 - lat0) ** 2 + (lon3 - lon0) ** 2)

        # calculate the relative coordinates in percentage
        u = (dlon / width) * 100
        v = (dlat / height) * 100
        return (u, v)
    
    def load_map_config(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "map_config.json")
            if os.path.exists(path):
                with open(path, "r") as json_file:
                    logger.info("Map config loaded from file")
                    return json.load(json_file)
            else:
                logger.info("Map config file not found, creating new one")
                MapConfigGUI() # Open the GUI to create a new map config
                try:
                    with open(path, "r") as json_file:
                        return json.load(json_file)
                except FileNotFoundError:
                    logger.error("Map config file not found after creating new one")
                    return None
        except Exception as e:
            logger.error(f"Error loading map config: {str(e)}")

    def get_camera_relative_positions(self):
        """Get the camera positions in relative coordinates."""
        return self.camera_relative_coords

    def __str__(self):
        return f"Map(name={self.name}, corner_coords={self.corner_coords}, file_path={self.file_path})"
