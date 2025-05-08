import math
import numpy as np
import os
import json

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
        self.map_config = json.load(open(os.path.join(os.path.dirname(__file__), "map_config.json"), "r"))
        self.name = self.map_config["name"]
        self.corner_coords = [(lat, lon) for lat, lon in self.map_config["corners"]] # [(lat, lon), ...] in order TL, BL, TR, BR
        self.file_path = self._get_floor_plan()  # Get the floor plan image file path
        self.camera_geocoords = {}
        self.camera_relative_coords = {}
        for camera_id, camera_data in self.map_config["cameras"].items():
            coords = camera_data["geocoordinates"]
            self.camera_geocoords[int(camera_id)] = (coords[0], coords[1])
            relative_coords = camera_data["pixel_percent"]
            self.camera_relative_coords[int(camera_id)] = (relative_coords[0], relative_coords[1])
        
        print(f"camera_geocoords: {self.camera_geocoords}")
        print(f"camera_relative_coords: {self.camera_relative_coords}")

    def _get_floor_plan(self):
        """Get the floor plan of the map."""
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets")) # get the assets dir
        for ext in ("png", "jpg"):
            floor_plan = os.path.join(assets_dir, f"floor_plan.{ext}")
            if os.path.exists(floor_plan):
                return floor_plan
        raise FileNotFoundError(f"Floor plan not found in {assets_dir}. Please add a floor_plan.png or floor_plan.jpg.")

    def convert_to_relative(self, coords: tuple) -> tuple:
        """Convert absolute geocoordinates to relative coordinates on the map.

        Args:
            coords (tuple): geocoordinates (lat, lon) of the point

        Returns:
            tuple: (u, v) relative coordinates in [0..100] for x and y,
                where (0,0)=TL, (100,100)=BR
        """
        tr, br, bl, tl = self.corner_coords
        lat0, lon0 = tl  # origin at top-left

        M_PER_DEG_LAT = 110_574  # approx meters per degree latitude
        M_PER_DEG_LON = 111_320 * math.cos(math.radians(lat0))  # adjust by cos(lat)

        def to_xy(lat, lon):
            """Project lat/lon to local x,y in meters."""
            dx = (lon - lon0) * M_PER_DEG_LON
            dy = (lat - lat0) * M_PER_DEG_LAT
            return np.array([dx, dy])

        vec_p = to_xy(*coords)
        vec_tr = to_xy(*tr)
        vec_bl = to_xy(*bl)

        basis = np.column_stack([vec_tr, vec_bl])

        if np.abs(np.linalg.det(basis)) < 1e-8:
            raise ValueError(
                "Invalid corner coordinates: area too small or corners are collinear."
            )

        # Solve for the relative coordinates in the new basis
        uv = np.linalg.solve(basis, vec_p)

        # Scale to [0, 100] and round
        u, v = np.round(uv * 100, 2)

        return (u, v)

    def return_map(self):
        """Return the map object."""
        return self

    def __str__(self):
        return f"Map(name={self.name}, corner_coords={self.corner_coords}, file_path={self.file_path})"
