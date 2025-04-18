import math


class Map:
    def __init__(self, name: str, corner_coords: list, file_path: str):
        """Holds the current map used in the frontend to convert to relative xy coordinates
        instead of absolute geocoordinates.

        Args:
            name (str): name of the map
            corner_coords (list): list of corner coordinates of the map in the format [tl, bl, tr, br]
                where tl = top left, bl = bottom left, tr = top right, br = bottom right. Example:
                corner_coords = [(lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4)]
            file_path (str): filepath of the image file of the map
        """
        self.name = name
        self.corner_coords = corner_coords  # [(lat, lon), ...] in order TL, BL, TR, BR
        self.file_path = file_path

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
            return dx, dy

        tr_x, tr_y = to_xy(*tr)
        bl_x, bl_y = to_xy(*bl)
        p_x, p_y = to_xy(*coords)

        b_x, b_y = tr_x, tr_y
        d_x, d_y = bl_x, bl_y

        denom = b_x * d_y - b_y * d_x
        if abs(denom) < 1e-8:
            raise ValueError(
                "Invalid corner coordinates: area too small or corners are collinear."
            )

        x = (p_x * d_y - p_y * d_x) / denom
        y = (b_x * p_y - b_y * p_x) / denom
        x = round(x * 100, 2)  # scale to [0..100]
        y = round(y * 100, 2)

        return (x, y)
