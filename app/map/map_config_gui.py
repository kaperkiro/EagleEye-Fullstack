import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import json
import math
from geopy.distance import geodesic
import os
import logging

logger = logging.getLogger(__name__)

class MapConfigGUI:
    """Graphical interface for configuring geopositions on a floor plan map.

    Allows users to define a room by setting four corners, place cameras with
    geocoordinates, and save the configuration to a JSON file.
    """

    def __init__(self, floor_plan_path="../assets/floor_plan.png", output_path="map_config.json"):
        """Initialize the GUI and set up state variables.

        Args:
            floor_plan_path (str): Path to the floor plan image (default: "../assets/floor_plan.png").
            output_path (str): Path to save the configuration JSON (default: "map_config.json").
        """
        # Create main window
        self.root = tk.Tk()
        self.root.title("EagleEye Map Configuration")
        self.root.configure(bg="#333333")

        # Set window icon
        try:
            icon_image = Image.open(os.path.join(os.path.dirname(__file__), "..", "assets", "logo_no_text.png"))
            icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
            self.icon = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(False, self.icon)
        except FileNotFoundError:
            logger.error("Icon file not found. Using default icon.")
            

        # Set file paths
        self.floor_plan_path = os.path.join(os.path.dirname(__file__), floor_plan_path)
        self.output_path = os.path.join(os.path.dirname(__file__), output_path)

        # Room configuration state
        self.corners = []  # Pixel coordinates of room corners
        self.corner_circles = []  # Canvas IDs for corner markers
        self.room_length = None  # Length of selected side in meters
        self.meters_per_pixel = None  # Conversion factor from pixels to meters
        self.room_corners_relative = []  # Room corners in meters relative to origin
        self.room_corners_geo = []  # Geocoordinates of room corners
        self.image_corners_geo = []  # Geocoordinates of image corners
        self.origin_geo = None  # (lat, lon) of top-left corner
        self.side_lengths = {}  # Lengths of room sides in meters
        self.side_label_ids = []  # Canvas IDs for side length labels
        self.side_label_map = {}  # Maps label IDs to side names
        self.origin_label_id = None  # Canvas ID for origin label
        self.camera_positions = {}  # Camera IDs mapped to their positions
        self.camera_circles = []  # Canvas IDs for camera markers
        self.camera_labels = []  # Canvas IDs for camera ID labels
        self.camera_arrows = []  # Canvas IDs for camera heading arrows

        # Hover text and crosshair state
        self.hover_text_id = None  # Canvas ID for hover text
        self.crosshair_h_id = None  # Canvas ID for horizontal crosshair
        self.crosshair_v_id = None  # Canvas ID for vertical crosshair

        # Grid configuration
        self.grid_spacing = 50  # Pixel spacing for canvas grid

        # Camera rotation state
        self.rotating_camera_id = None  # ID of camera being rotated
        self.arrow_hitbox_radius = 10  # Click radius for arrow endpoints

        # Load camera IDs from cameras.json
        self.camera_ids = []
        self.camera_display_map = {}  # Maps display string to camera ID
        try:
            json_path = os.path.join(os.path.dirname(__file__), "../camera/cameras.json")
            with open(json_path, 'r') as f:
                cameras = json.load(f)
                for camera in cameras:
                    if "ID" in camera and "IP Address" in camera:
                        camera_id = str(camera["ID"])
                        display_str = f"{camera_id} - {camera['IP Address']}"
                        self.camera_ids.append(display_str)
                        self.camera_display_map[display_str] = camera_id
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            messagebox.showwarning("Warning", "Could not load camera IDs from cameras.json. Please run ARP scan first.")

        # Setup GUI elements
        self.setup_frame = tk.Frame(self.root, bg="#333333")
        self.setup_frame.pack(pady=5)
        tk.Label(self.setup_frame, text="Map Name:", bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack(side=tk.LEFT)
        self.map_name = tk.Entry(self.setup_frame, width=20, bg="#444444", fg="#DEDEDE", insertbackground="#DEDEDE")
        self.map_name.insert(0, "Local House")
        self.map_name.pack(side=tk.LEFT, padx=5)
        tk.Label(self.setup_frame, text="Origin Lat:", bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack(side=tk.LEFT)
        self.origin_lat = tk.Entry(self.setup_frame, width=10, bg="#444444", fg="#DEDEDE", insertbackground="#DEDEDE")
        self.origin_lat.insert(0, "59.3240")
        self.origin_lat.pack(side=tk.LEFT, padx=5)
        tk.Label(self.setup_frame, text="Origin Lon:", bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack(side=tk.LEFT)
        self.origin_lon = tk.Entry(self.setup_frame, width=10, bg="#444444", fg="#DEDEDE", insertbackground="#DEDEDE")
        self.origin_lon.insert(0, "18.0700")
        self.origin_lon.pack(side=tk.LEFT, padx=5)

        # Setup canvas for floor plan
        self.canvas_frame = tk.Frame(self.root, bg="#333333")
        self.canvas_frame.pack(pady=10)
        self.canvas_label = tk.Label(self.canvas_frame, text="Floor Plan", bg="#333333", fg="white", font=("Arial", 12))
        self.canvas_label.pack()
        self.canvas = tk.Canvas(self.canvas_frame, width=800, height=600, bg="#444444", highlightthickness=2, highlightbackground="#666666")
        self.canvas.pack()

        # Instruction and coordinate display
        self.instruction_var = tk.StringVar(value="Click 4 corners of the room (top-left, top-right, bottom-right, bottom-left)")
        self.instruction_label = tk.Label(self.root, textvariable=self.instruction_var, bg="#333333", fg="#DEDEDE", font=("Arial", 15))
        self.instruction_label.pack(pady=5)

        self.coord_var = tk.StringVar(value="Coordinates: N/A")
        tk.Label(self.root, textvariable=self.coord_var, bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack()

        # Setup buttons for corner actions
        self.length_frame = tk.Frame(self.root, bg="#333333")
        self.length_frame.pack(pady=5)
        tk.Button(self.length_frame, text="Undo Corner", command=self.undo_corner, bg="#333333", fg="#DEDEDE", activebackground="#666666", font=("Arial", 12), width=15, height=1, relief=tk.RIDGE, borderwidth=3).pack(side=tk.LEFT, padx=5)
        tk.Button(self.length_frame, text="Reset All", command=self.reset_all, bg="#333333", fg="#DEDEDE", activebackground="#666666", font=("Arial", 12), width=15, height=1, relief=tk.RIDGE, borderwidth=3).pack(side=tk.LEFT, padx=5)

        # Setup camera placement controls
        self.camera_frame = tk.Frame(self.root, bg="#333333")
        self.camera_frame.pack(pady=5)
        tk.Label(self.camera_frame, text="Camera ID:", bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack(side=tk.LEFT)
        self.camera_id = ttk.Combobox(self.camera_frame, width=20, values=self.camera_ids, state="readonly")
        self.camera_id.pack(side=tk.LEFT, padx=5)

        # Style Combobox to match dark theme
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground="#444444", background="#444444", foreground="#DEDEDE", arrowcolor="#DEDEDE")
        style.map("TCombobox", fieldbackground=[('readonly', '#444444')], selectbackground=[('readonly', '#444444')], selectforeground=[('readonly', '#DEDEDE')])
        tk.Label(self.camera_frame, text="Height (m):", bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack(side=tk.LEFT)
        self.camera_height = tk.Entry(self.camera_frame, width=5, bg="#444444", fg="#DEDEDE", insertbackground="#DEDEDE")
        self.camera_height.pack(side=tk.LEFT, padx=5)
        tk.Label(self.camera_frame, text="Heading (deg):", bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack(side=tk.LEFT)
        self.camera_heading = tk.Entry(self.camera_frame, width=5, bg="#444444", fg="#DEDEDE", insertbackground="#DEDEDE")
        self.camera_heading.pack(side=tk.LEFT, padx=5)
        tk.Button(self.camera_frame, text="Place Camera", command=self.start_camera_placement, bg="#333333", fg="#DEDEDE", activebackground="#666666", font=("Arial", 12), width=15, height=1, relief=tk.RIDGE, borderwidth=3).pack(side=tk.LEFT, padx=5)
        tk.Button(self.camera_frame, text="Undo Camera", command=self.undo_camera, bg="#333333", fg="#DEDEDE", activebackground="#666666", font=("Arial", 12), width=15, height=1, relief=tk.RIDGE, borderwidth=3).pack(side=tk.LEFT, padx=5)

        # Save button
        tk.Button(self.root, text="Save Configuration", command=self.save_configuration, bg="#333333", fg="#DEDEDE", activebackground="#666666", font=("Arial", 12), width=15, height=1, relief=tk.RIDGE, borderwidth=3).pack(pady=10)

        # Bind mouse events to canvas
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<B1-Motion>", self.handle_drag)
        self.canvas.bind("<ButtonRelease-1>", self.handle_release)
        self.canvas.bind("<Motion>", self.preview_coordinates)
        self.mode = "room"

        # Load and display floor plan
        self.load_floor_plan()
        self.root.mainloop()

    def reset_all(self):
        """Reset all configurations and restart the GUI."""
        # Clear canvas and destroy window
        self.canvas.delete("all")
        self.root.destroy()
        # Reinitialize the GUI
        self.__init__(self.floor_plan_path, self.output_path)

    def load_floor_plan(self):
        """Load and display the floor plan image on the canvas.

        Resizes the image to fit the canvas while maintaining aspect ratio.
        Draws a grid on the canvas for reference.

        Raises:
            FileNotFoundError: If the floor plan image is not found.
        """
        try:
            img = Image.open(self.floor_plan_path)
            orig_width, orig_height = img.size
            aspect_ratio = orig_width / orig_height
            canvas_width, canvas_height = 800, 600

            # Resize image to fit canvas
            if aspect_ratio > canvas_width / canvas_height:
                new_width = canvas_width
                new_height = int(canvas_width / aspect_ratio)
            else:
                new_height = canvas_height
                new_width = int(canvas_height * aspect_ratio)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.floor_plan = ImageTk.PhotoImage(img)

            # Center image on canvas
            x_offset = (canvas_width - new_width) // 2
            y_offset = (canvas_height - new_height) // 2
            self.canvas.create_image(x_offset, y_offset, image=self.floor_plan, anchor="nw")
            self.image_size = (new_width, new_height)
            self.image_offset = (x_offset, y_offset)
            self.draw_grid()
        except FileNotFoundError:
            messagebox.showerror("Error", f"Floor plan image {self.floor_plan_path} not found")
            self.root.quit()

    def draw_grid(self):
        """Draw a grid on the canvas for reference."""
        canvas_width, canvas_height = 800, 600
        for x in range(0, canvas_width, self.grid_spacing):
            self.canvas.create_line(x, 0, x, canvas_height, fill="#666666", dash=(2, 2))
        for y in range(0, canvas_height, self.grid_spacing):
            self.canvas.create_line(0, y, canvas_width, y, fill="#666666", dash=(2, 2))

    def is_convex_quadrilateral(self, points):
        """Check if four points form a convex quadrilateral.

        Args:
            points (list): List of (x, y) tuples representing the four corners.

        Returns:
            bool: True if points form a convex quadrilateral, False otherwise.
        """
        if len(points) != 4:
            return False
        def cross_product(p1, p2, p3):
            return (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])
        signs = []
        for i in range(4):
            cp = cross_product(points[i], points[(i+1)%4], points[(i+2)%4])
            signs.append(1 if cp > 0 else -1 if cp < 0 else 0)
        return all(s == signs[0] and s != 0 for s in signs)

    def handle_click(self, event):
        """Handle mouse click events on the canvas.

        In 'room' mode, adds a corner. In 'camera' mode, places a camera.
        If clicking near a camera arrow, switches to 'rotate_heading' mode.

        Args:
            event: Tkinter event object with x, y coordinates.
        """
        x, y = event.x - self.image_offset[0], event.y - self.image_offset[1]
        canvas_x, canvas_y = event.x, event.y

        # Check if clicking near a camera arrow endpoint
        if self.mode == "camera" and self.camera_positions:
            for camera_id, config in self.camera_positions.items():
                pixel_x = (config["pixel_percent"][0] / 100) * self.image_size[0]
                pixel_y = (config["pixel_percent"][1] / 100) * self.image_size[1]
                display_x = pixel_x + self.image_offset[0]
                display_y = pixel_y + self.image_offset[1]
                heading = config["heading"]
                arrow_length = 30
                rad = math.radians(heading)
                arrow_end_x = display_x + arrow_length * math.sin(rad)
                arrow_end_y = display_y - arrow_length * math.cos(rad)
                dist = math.hypot(canvas_x - arrow_end_x, canvas_y - arrow_end_y)
                if dist <= self.arrow_hitbox_radius:
                    self.mode = "rotate_heading"
                    self.rotating_camera_id = camera_id
                    self.instruction_var.set(f"Rotate Camera ID {camera_id} heading")
                    return

        # Handle clicks within the image
        if 0 <= x <= self.image_size[0] and 0 <= y <= self.image_size[1]:
            if self.mode == "room":
                self.add_corner(x, y)
            elif self.mode == "camera":
                self.place_camera(x, y)

    def handle_drag(self, event):
        """Handle mouse drag events for rotating camera heading.

        Updates the heading of the selected camera based on mouse position.

        Args:
            event: Tkinter event object with x, y coordinates.
        """
        if self.mode != "rotate_heading" or not self.rotating_camera_id:
            return

        canvas_x, canvas_y = event.x, event.y
        config = self.camera_positions[self.rotating_camera_id]
        pixel_x = (config["pixel_percent"][0] / 100) * self.image_size[0]
        pixel_y = (config["pixel_percent"][1] / 100) * self.image_size[1]
        display_x = pixel_x + self.image_offset[0]
        display_y = pixel_y + self.image_offset[1]

        # Calculate heading (0° is north, clockwise)
        dx = canvas_x - display_x
        dy = -(canvas_y - display_y)  # Flip y for standard coordinates
        heading = math.degrees(math.atan2(dx, dy)) % 360

        # Update camera heading
        config["heading"] = heading
        self.camera_heading.delete(0, tk.END)
        self.camera_heading.insert(0, f"{heading:.1f}")

        # Redraw camera arrow
        self.redraw_camera_arrow(self.rotating_camera_id)

    def handle_release(self, event):
        """Handle mouse release events.

        Exits 'rotate_heading' mode and returns to 'camera' mode.

        Args:
            event: Tkinter event object.
        """
        if self.mode == "rotate_heading":
            self.mode = "camera"
            self.rotating_camera_id = None
            self.instruction_var.set("Select camera ID, enter height and heading, then click to place")

    def redraw_camera_arrow(self, camera_id):
        """Redraw the heading arrow for a camera.

        Args:
            camera_id (str): ID of the camera to redraw.
        """
        # Delete existing arrow
        idx = next(i for i, (cid, _) in enumerate(zip(self.camera_positions.keys(), self.camera_arrows)) if cid == camera_id)
        self.canvas.delete(self.camera_arrows[idx])

        # Draw new arrow
        config = self.camera_positions[camera_id]
        pixel_x = (config["pixel_percent"][0] / 100) * self.image_size[0]
        pixel_y = (config["pixel_percent"][1] / 100) * self.image_size[1]
        display_x = pixel_x + self.image_offset[0]
        display_y = pixel_y + self.image_offset[1]
        heading = config["heading"]
        arrow_length = 30
        rad = math.radians(heading)
        arrow_end_x = display_x + arrow_length * math.sin(rad)
        arrow_end_y = display_y - arrow_length * math.cos(rad)
        arrow_id = self.canvas.create_line(display_x, display_y, arrow_end_x, arrow_end_y, fill="blue", arrow=tk.LAST, arrowshape=(8, 10, 3), width=3)
        self.camera_arrows[idx] = arrow_id

    def add_corner(self, x, y):
        """Add a corner to the room and draw a marker.

        If four corners are added, checks for convexity and prompts for side length.

        Args:
            x (float): X-coordinate in image pixels.
            y (float): Y-coordinate in image pixels.
        """
        self.corners.append((x, y))
        display_x = x + self.image_offset[0]
        display_y = y + self.image_offset[1]
        circle_id = self.canvas.create_oval(display_x-5, display_y-5, display_x+5, display_y+5, fill="red")
        self.corner_circles.append(circle_id)
        if len(self.corners) == 4:
            if not self.is_convex_quadrilateral(self.corners):
                messagebox.showerror("Error", "Corners do not form a convex quadrilateral")
                self.undo_corner()
                return
            tl_x, tl_y = self.corners[0]
            display_x = tl_x + self.image_offset[0] - 15
            display_y = tl_y + self.image_offset[1] + 15
            self.origin_label_id = self.canvas.create_text(display_x, display_y, text="Origin", fill="red", font=("Arial", 12, "bold"))
            self.instruction_var.set("Click a side label to set its length")
            self.mode = "set_length"
            self.display_side_lengths(use_pixels=True)
            self.bind_side_labels()
        else:
            self.instruction_var.set(f"Click corner {len(self.corners) + 1} of 4")

    def undo_corner(self):
        """Remove the last added corner and its marker."""
        if self.corners:
            self.corners.pop()
            self.canvas.delete(self.corner_circles.pop())
            if self.origin_label_id:
                self.canvas.delete(self.origin_label_id)
                self.origin_label_id = None
            self.instruction_var.set(f"Click corner {len(self.corners) + 1} of 4")
            self.mode = "room" if len(self.corners) < 4 else "set_length"
            if len(self.corners) < 4:
                for label_id in self.side_label_ids:
                    self.canvas.delete(label_id)
                self.side_label_ids = []
                self.side_label_map = {}

    def bind_side_labels(self):
        """Bind click events to side length labels."""
        for label_id in self.side_label_ids:
            self.canvas.tag_bind(label_id, "<Button-1>", lambda event, lid=label_id: self.set_side_length(lid))

    def set_side_length(self, label_id):
        """Set the length of a room side and calculate geocoordinates.

        Args:
            label_id: Canvas ID of the side label clicked.

        Raises:
            ValueError: If latitude or longitude is invalid.
        """
        side_name = self.side_label_map.get(label_id)
        if not side_name:
            return
        length = simpledialog.askfloat("Input", f"Enter length for {side_name} (meters):", parent=self.root, minvalue=0.01)
        if length is None:
            return
        try:
            self.room_length = length
            self.origin_geo = (float(self.origin_lat.get()), float(self.origin_lon.get()))
            if not (-90 <= self.origin_geo[0] <= 90 and -180 <= self.origin_geo[1] <= 180):
                raise ValueError("Invalid latitude or longitude")

            # Calculate meters per pixel
            side_indices = {"top-left_to_top-right": (0, 1), "top-right_to_bottom-right": (1, 2), "bottom-right_to_bottom-left": (2, 3), "bottom-left_to_top-left": (3, 0)}
            idx1, idx2 = side_indices[side_name]
            p1, p2 = self.corners[idx1], self.corners[idx2]
            pixel_dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            self.meters_per_pixel = length / pixel_dist

            # Calculate room corners relative to origin
            self.room_corners_relative = []
            self.room_corners_geo = [None] * 4
            tl_geo = self.origin_geo
            self.room_corners_geo[0] = tl_geo
            tl = self.corners[0]

            for idx in [1, 2, 3]:
                px, py = self.corners[idx]
                x_meters = (px - tl[0]) * self.meters_per_pixel
                y_meters = (py - tl[1]) * self.meters_per_pixel
                dist = math.hypot(x_meters, y_meters)
                bearing = math.degrees(math.atan2(x_meters, -y_meters)) % 360
                geo_point = geodesic(meters=dist).destination(tl_geo, bearing)
                self.room_corners_geo[idx] = (geo_point.latitude, geo_point.longitude)
                self.room_corners_relative.append([x_meters, y_meters, 0])

            self.room_corners_relative.insert(0, [0, 0, 0])

            # Calculate image corners geocoordinates
            self.image_corners_geo = []
            image_corners_pixels = [(0, 0), (self.image_size[0], 0), (self.image_size[0], self.image_size[1]), (0, self.image_size[1])]
            for px, py in image_corners_pixels:
                x_meters = (px - tl[0]) * self.meters_per_pixel
                y_meters = (py - tl[1]) * self.meters_per_pixel
                dist = math.hypot(x_meters, y_meters)
                bearing = math.degrees(math.atan2(x_meters, -y_meters)) % 360
                geo_point = geodesic(meters=dist).destination(tl_geo, bearing)
                self.image_corners_geo.append([geo_point.latitude, geo_point.longitude])

            # Store side lengths
            self.side_lengths = {"top-left_to_top-right": self.calculate_side_length(0, 1), "top-right_to_bottom-right": self.calculate_side_length(1, 2), "bottom-right_to_bottom-left": self.calculate_side_length(2, 3),"bottom-left_to_top-left": self.calculate_side_length(3, 0)}

            # Draw room outline
            adjusted_corners = [(x + self.image_offset[0], y + self.image_offset[1]) for x, y in self.corners]
            self.canvas.create_polygon([c for corner in adjusted_corners for c in corner], outline="red", dash=(10, 10), fill="", width=2, tags="room_outline")

            # Update side labels
            for label_id in self.side_label_ids:
                self.canvas.delete(label_id)
            self.side_label_ids = []
            self.side_label_map = {}
            self.display_side_lengths(use_pixels=False)

            self.instruction_var.set("Select camera ID, enter height and heading, then click to place")
            self.mode = "camera"
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def calculate_side_length(self, idx1, idx2):
        """Calculate the length of a side in meters or pixels.

        Args:
            idx1 (int): Index of the first corner.
            idx2 (int): Index of the second corner.

        Returns:
            float: Length in meters if meters_per_pixel is set, else in pixels.
        """
        p1, p2 = self.corners[idx1], self.corners[idx2]
        pixel_dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        if self.meters_per_pixel is None:
            return pixel_dist
        return round(pixel_dist * self.meters_per_pixel, 3)

    def display_side_lengths(self, use_pixels=False):
        """Display side lengths on the canvas.

        Args:
            use_pixels (bool): If True, show "Click to set length"; else show meters.
        """
        for label_id in self.side_label_ids:
            self.canvas.delete(label_id)
        self.side_label_ids = []
        self.side_label_map = {}

        sides = [(0, 1, "top-left_to_top-right"), (1, 2, "top-right_to_bottom-right"), (2, 3, "bottom-right_to_bottom-left"), (3, 0, "bottom-left_to_top-left")]

        for idx1, idx2, side_name in sides:
            x1, y1 = self.corners[idx1]
            x2, y2 = self.corners[idx2]
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            mid_x += self.image_offset[0]
            mid_y += self.image_offset[1]

            if use_pixels:
                text = "Click to\nset length"
            else:
                length = self.calculate_side_length(idx1, idx2)
                text = f"{length:.2f}m"

            # Adjust label position
            offset_x, offset_y = 0, 0
            if side_name == "top-left_to_top-right":
                offset_y = -10
            elif side_name == "top-right_to_bottom-right":
                offset_x = -25
            elif side_name == "bottom-right_to_bottom-left":
                offset_y = 10
            elif side_name == "bottom-left_to_top-left":
                offset_x = 25

            label_id = self.canvas.create_text(mid_x + offset_x, mid_y + offset_y, text=text, fill="red", font=("Arial", 12, "bold"))
            self.side_label_ids.append(label_id)
            self.side_label_map[label_id] = side_name

    def start_camera_placement(self):
        """Validate camera placement inputs and prepare for placement.

        Raises:
            ValueError: If inputs are invalid or room is not defined.
        """
        if not self.room_length or len(self.corners) != 4:
            messagebox.showerror("Error", "Please define room first")
            return
        if not self.camera_id.get():
            messagebox.showerror("Error", "Please select a camera ID")
            return
        try:
            selected_display = self.camera_id.get()
            camera_id = int(self.camera_display_map[selected_display])
            if camera_id < 1:
                raise ValueError("Camera ID must be a positive integer")
            z = float(self.camera_height.get())
            heading = float(self.camera_heading.get() or 0)  # Default to 0 if empty
            if z < 0:
                raise ValueError("Height must be non-negative")
            if not 0 <= heading <= 360:
                raise ValueError("Heading must be 0-360 degrees")
            self.current_camera = {"id": camera_id, "z": z, "heading": heading}
        except (KeyError, ValueError) as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def place_camera(self, x, y):
        """Place a camera at the specified position and calculate its geocoordinates.

        Args:
            x (float): X-coordinate in image pixels.
            y (float): Y-coordinate in image pixels.
        """
        if not hasattr(self, "current_camera"):
            # messagebox.showerror("Error", "Please set camera details first")
            return

        tl = self.corners[0]
        x_rel = (x - tl[0]) * self.meters_per_pixel
        y_rel = (y - tl[1]) * self.meters_per_pixel
        z = self.current_camera["z"]

        x_percent = (x / self.image_size[0]) * 100
        y_percent = (y / self.image_size[1]) * 100

        tl_geo = self.room_corners_geo[0]
        dist = math.hypot(x_rel, y_rel)
        bearing = math.degrees(math.atan2(x_rel, -y_rel)) % 360
        geo_point = geodesic(meters=dist).destination(tl_geo, bearing)
        lat, lon = geo_point.latitude, geo_point.longitude

        camera_id = str(self.current_camera["id"])
        self.camera_positions[camera_id] = {"geocoordinates": [lat, lon], "relative_pos": [x_rel, y_rel, z], "pixel_percent": [x_percent, y_percent], "height": z, "heading": self.current_camera["heading"]}

        # Draw camera marker, label, and arrow
        display_x = x + self.image_offset[0]
        display_y = y + self.image_offset[1]
        circle_id = self.canvas.create_oval(display_x-5, display_y-5, display_x+5, display_y+5, fill="blue")
        label_id = self.canvas.create_text(display_x, display_y-10, text=f"ID {camera_id}", fill="blue")

        arrow_length = 30
        heading = self.current_camera["heading"]
        rad = math.radians(heading)
        arrow_end_x = display_x + arrow_length * math.sin(rad)
        arrow_end_y = display_y - arrow_length * math.cos(rad)
        arrow_id = self.canvas.create_line(display_x, display_y, arrow_end_x, arrow_end_y, fill="blue", arrow=tk.LAST, arrowshape=(8, 10, 3), width=3)

        self.camera_circles.append(circle_id)
        self.camera_labels.append(label_id)
        self.camera_arrows.append(arrow_id)
        messagebox.showinfo("Success", f"Camera ID {camera_id} placed at ({x_rel:.2f}, {y_rel:.2f}, {z})")
        del self.current_camera

    def undo_camera(self):
        """Remove the last placed camera and its visual elements."""
        if self.camera_positions:
            last_id = max(self.camera_positions.keys(), key=int)
            self.camera_positions.pop(last_id)
            self.canvas.delete(self.camera_circles.pop())
            self.canvas.delete(self.camera_labels.pop())
            self.canvas.delete(self.camera_arrows.pop())
            self.instruction_var.set("Select camera ID, enter height and heading, then click to place")

    def preview_coordinates(self, event):
        """Display geocoordinates or pixel coordinates under the mouse cursor.

        Args:
            event: Tkinter event object with x, y coordinates.
        """
        x = event.x - self.image_offset[0]
        y = event.y - self.image_offset[1]

        within_image = 0 <= x <= self.image_size[0] and 0 <= y <= self.image_size[1]

        # Update coordinate display
        if self.mode not in ("camera", "rotate_heading") or not self.room_length or len(self.corners) != 4:
            self.coord_var.set("Coordinates: N/A")
        else:
            if within_image:
                tl = self.corners[0]
                x_rel = (x - tl[0]) * self.meters_per_pixel
                y_rel = (y - tl[1]) * self.meters_per_pixel
                tl_geo = self.room_corners_geo[0]
                dist = math.hypot(x_rel, y_rel)
                bearing = math.degrees(math.atan2(x_rel, -y_rel)) % 360
                geo_point = geodesic(meters=dist).destination(tl_geo, bearing)
                lat, lon = geo_point.latitude, geo_point.longitude
                self.coord_var.set(f"Coordinates: ({lat:.6f}, {lon:.6f})")
            else:
                self.coord_var.set("Coordinates: N/A")

        # Update hover text
        if within_image:
            if self.mode == "room" and len(self.corners) < 4:
                corner_names = ["TL point", "TR point", "BR point", "BL point"]
                hover_text = f"Set {corner_names[len(self.corners)]}"
            elif self.mode not in ("camera", "rotate_heading") or not self.room_length or len(self.corners) != 4:
                hover_text = f"Pixel: ({x:.0f}, {y:.0f})"
            else:
                tl = self.corners[0]
                x_rel = (x - tl[0]) * self.meters_per_pixel
                y_rel = (y - tl[1]) * self.meters_per_pixel
                tl_geo = self.room_corners_geo[0]
                dist = math.hypot(x_rel, y_rel)
                bearing = math.degrees(math.atan2(x_rel, -y_rel)) % 360
                geo_point = geodesic(meters=dist).destination(tl_geo, bearing)
                lat, lon = geo_point.latitude, geo_point.longitude
                hover_text = f"Geo: ({lat:.6f}, {lon:.6f})"

            if self.hover_text_id is None:
                self.hover_text_id = self.canvas.create_text(event.x + 10, event.y + 10, text=hover_text, fill="#FF0000", font=("Arial", 12), tags="hover_text", anchor="nw")
            else:
                self.canvas.itemconfig(self.hover_text_id, text=hover_text)
                self.canvas.coords(self.hover_text_id, event.x + 10, event.y + 10)
        else:
            if self.hover_text_id is not None:
                self.canvas.delete("hover_text")
                self.hover_text_id = None

        # Update crosshair
        if within_image:
            if self.crosshair_h_id is None:
                self.crosshair_h_id = self.canvas.create_line(0, event.y, 800, event.y, fill="#FF0000", dash=(8, 8), tags="crosshair")
            else:
                self.canvas.coords(self.crosshair_h_id, 0, event.y, 800, event.y)

            if self.crosshair_v_id is None:
                self.crosshair_v_id = self.canvas.create_line(event.x, 0, event.x, 600, fill="#FF0000", dash=(8, 8), tags="crosshair")
            else:
                self.canvas.coords(self.crosshair_v_id, event.x, 0, event.x, 600)
        else:
            self.canvas.delete("crosshair")
            self.crosshair_h_id = None
            self.crosshair_v_id = None

    def save_configuration(self):
        """Save the map configuration to a JSON file.

        Includes room corners, image corners, side lengths, and camera positions.

        Raises:
            Exception: If saving to file fails.
        """
        config = {
            "name": self.map_name.get(),
            "corners": self.room_corners_geo,
            "image_corners": self.image_corners_geo,
            "room": {
                "length": self.room_length,
                "side_lengths": self.side_lengths
            },
            "cameras": {
                k: {
                    "geocoordinates": v["geocoordinates"],
                    "pixel_percent": v["pixel_percent"],
                    "height": v["height"],
                    "heading": v["heading"]
                } for k, v in self.camera_positions.items()
            }
        }
        try:
            with open(self.output_path, "w") as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Success", f"Configuration saved to {self.output_path}")
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")