import math
import numpy as np


def clamp(value, min_value, max_value):
    """Clamp a value between min_value and max_value."""
    return max(min(value, max_value), min_value)


class MapManager:
    def __init__(
        self,
        name: str,
        corner_coords: list,
        file_path: str,
        camera_geocoords: dict[tuple] = None,
    ):
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
        self.name = name
        self.corner_coords = corner_coords  # [(lat, lon), ...] in order TL, BL, TR, BR
        self.file_path = file_path
        self.camera_geocoords = camera_geocoords  # {camera_id: (x, y)}
        # Compute relative coordinates for each camera using convert_to_relative
        if self.camera_geocoords:
            self.camera_relative_coords = {
                cam_id: self.convert_to_relative(coords)
                for cam_id, coords in self.camera_geocoords.items()
            }
        else:
            self.camera_relative_coords = {}

    def __str__(self):
        return f"Map(name={self.name}, corner_coords={self.corner_coords}, file_path={self.file_path})"

    def convert_to_relative(self, coords: tuple) -> tuple:
        """Convert absolute geocoordinates to relative coordinates on the map.

        Args:
            coords (tuple): geocoordinates (lat, lon) of the point

        Returns:
            tuple: (u, v) relative coordinates in [0..100] for x and y,
                where (0,0)=TL, (100,100)=BR
        """
        tl, bl, tr, br = self.corner_coords
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

    def create_corners(self, camera_geocoords: tuple):
        """Creates corners from camera position.
        for now creates a square infront of the camera of 5 x 5 m eg
        |-----|
        |     |
        |--*--| where * is the camera position
        and the corners are the four corners of the square.
        """
        M_PER_DEG_LAT = 110_574  # approx meters per degree latitude
        M_PER_DEG_LON = 111_320 * math.cos(
            math.radians(camera_geocoords[0])
        )  # adjust by cos(lat)
        lat0, lon0 = camera_geocoords
        # 5 m in lat/lon degrees
        lat_offset = 2.5 / M_PER_DEG_LAT
        lon_offset = 2.5 / M_PER_DEG_LON
        # Create corners
        tl = (lat0 + lat_offset, lon0 - lon_offset)
        bl = (lat0 - lat_offset, lon0 - lon_offset)
        tr = (lat0 + lat_offset, lon0 + lon_offset)
        br = (lat0 - lat_offset, lon0 + lon_offset)

        self.corner_coords = [tl, bl, tr, br]

    def return_map(self):
        """Return the map object."""
        return self


if __name__ == "__main__":
    # Test conversion for three cameras on a unit square map
    corners = [(0, 0), (1, 0), (0, 1), (1, 1)]
    camera_geocoords = {
        "cam_tl": (0, 0),  # top-left
        "cam_br": (1, 1),  # bottom-right
        "cam_center": (0.5, 0.5),  # center
    }
    mm = MapManager("test_map", corners, "dummy_path", camera_geocoords)
    expected = {
        "cam_tl": (0.0, 0.0),
        "cam_br": (100.0, 100.0),
        "cam_center": (50.0, 50.0),
    }
    for cam_id, exp in expected.items():
        rel = mm.camera_relative_coords.get(cam_id)
        print(f"{cam_id}: computed {rel}, expected {exp}")
        assert rel is not None, f"No relative coords for {cam_id}"
        assert (
            abs(rel[0] - exp[0]) < 1e-2 and abs(rel[1] - exp[1]) < 1e-2
        ), f"For {cam_id}, expected {exp}, got {rel}"
    print("MapManager conversion tests passed.")
