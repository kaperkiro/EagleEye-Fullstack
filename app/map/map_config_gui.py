import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import json
import math
from geopy.distance import geodesic
import os

class MapConfigGUI:
    def __init__(self, floor_plan_path="../assets/floor_plan.png", output_path="map_config.json"):
        self.root = tk.Tk()
        self.root.title("Map Geoposition Configuration")
        self.root.configure(bg="#333333")  # Dark theme background

        self.floor_plan_path = os.path.join(os.path.dirname(__file__), floor_plan_path)
        self.output_path = os.path.join(os.path.dirname(__file__), output_path)

        # Room setup
        self.corners = []
        self.corner_circles = []
        self.room_length = None
        self.meters_per_pixel = None
        self.room_corners_relative = []
        self.room_corners_geo = []
        self.origin_geo = None
        self.side_lengths = {}
        self.side_label_ids = []  # Store canvas IDs for side length labels
        self.side_label_map = {}  # Map label_id to side_name for click events
        self.origin_label_id = None  # Store canvas ID for origin label

        # Camera setup
        self.camera_positions = {}
        self.camera_circles = []
        self.camera_labels = []

        # Hover text and crosshair
        self.hover_text_id = None  # Store canvas ID for hover text
        self.crosshair_h_id = None  # Store canvas ID for horizontal crosshair
        self.crosshair_v_id = None  # Store canvas ID for vertical crosshair

        # Grid setup
        self.grid_spacing = 50

        # GUI elements
        # Frame for map name and origin inputs
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

        # Frame for canvas and label
        self.canvas_frame = tk.Frame(self.root, bg="#333333")
        self.canvas_frame.pack(pady=10)
        self.canvas_label = tk.Label(self.canvas_frame, text="Floor Plan", bg="#333333", fg="white", font=("Arial", 12))
        self.canvas_label.pack()
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=800,
            height=600,
            bg="#444444",
            highlightthickness=2,
            highlightbackground="#666666"
        )
        self.canvas.pack()

        # Instructions
        self.instruction_var = tk.StringVar(value="Click 4 corners of the room (top-left, bottom-left, top-right, bottom-right)")
        self.instruction_label = tk.Label(
            self.root,
            textvariable=self.instruction_var,
            bg="#333333",
            fg="#DEDEDE",
            font=("Arial", 15)
        )
        self.instruction_label.pack(pady=5)

        # Coordinate preview
        self.coord_var = tk.StringVar(value="Coordinates: N/A")
        tk.Label(self.root, textvariable=self.coord_var, bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack()

        # Frame for undo corner and reset all buttons
        self.length_frame = tk.Frame(self.root, bg="#333333")
        self.length_frame.pack(pady=5)
        tk.Button(
            self.length_frame,
            text="Undo Corner",
            command=self.undo_corner,
            bg="#333333",
            fg="#DEDEDE",
            activebackground="#666666",
            font=("Arial", 12),
            width=15,
            height=1,
            relief=tk.RIDGE,
            borderwidth=3
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.length_frame,
            text="Reset All",
            command=self.reset_all,
            bg="#333333",
            fg="#DEDEDE",
            activebackground="#666666",
            font=("Arial", 12),
            width=15,
            height=1,
            relief=tk.RIDGE,
            borderwidth=3
        ).pack(side=tk.LEFT, padx=5)

        # Frame for camera configuration
        self.camera_frame = tk.Frame(self.root, bg="#333333")
        self.camera_frame.pack(pady=5)
        tk.Label(self.camera_frame, text="Camera ID (number):", bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack(side=tk.LEFT)
        self.camera_id = tk.Entry(self.camera_frame, width=5, bg="#444444", fg="#DEDEDE", insertbackground="#DEDEDE")
        self.camera_id.pack(side=tk.LEFT, padx=5)
        tk.Label(self.camera_frame, text="Height (m):", bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack(side=tk.LEFT)
        self.camera_height = tk.Entry(self.camera_frame, width=5, bg="#444444", fg="#DEDEDE", insertbackground="#DEDEDE")
        self.camera_height.pack(side=tk.LEFT, padx=5)
        tk.Label(self.camera_frame, text="Heading (deg):", bg="#333333", fg="#DEDEDE", font=("Arial", 12)).pack(side=tk.LEFT)
        self.camera_heading = tk.Entry(self.camera_frame, width=5, bg="#444444", fg="#DEDEDE", insertbackground="#DEDEDE")
        self.camera_heading.pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.camera_frame,
            text="Place Camera",
            command=self.start_camera_placement,
            bg="#333333",
            fg="#DEDEDE",
            activebackground="#666666",
            font=("Arial", 12),
            width=15,
            height=1,
            relief=tk.RIDGE,
            borderwidth=3
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.camera_frame,
            text="Undo Camera",
            command=self.undo_camera,
            bg="#333333",
            fg="#DEDEDE",
            activebackground="#666666",
            font=("Arial", 12),
            width=15,
            height=1,
            relief=tk.RIDGE,
            borderwidth=3
        ).pack(side=tk.LEFT, padx=5)

        # Save button
        tk.Button(
            self.root,
            text="Save Configuration",
            command=self.save_configuration,
            bg="#333333",
            fg="#DEDEDE",
            activebackground="#666666",
            font=("Arial", 12),
            width=15,
            height=1,
            relief=tk.RIDGE,
            borderwidth=3
        ).pack(pady=10)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<Motion>", self.preview_coordinates)
        self.mode = "room"

        # Load floor plan
        self.load_floor_plan()
        self.root.mainloop()

    def reset_all(self):
        """Reset the GUI to its initial state."""
        # Clear internal state
        self.corners = []
        self.corner_circles = []
        self.room_length = None
        self.meters_per_pixel = None
        self.room_corners_relative = []
        self.room_corners_geo = []
        self.origin_geo = None
        self.side_lengths = {}
        self.side_label_ids = []
        self.side_label_map = {}
        self.origin_label_id = None
        self.camera_positions = {}
        self.camera_circles = []
        self.camera_labels = []

        # Clear hover text and crosshair
        if self.hover_text_id is not None:
            self.canvas.delete("hover_text")
            self.hover_text_id = None
        self.canvas.delete("crosshair")
        self.crosshair_h_id = None
        self.crosshair_v_id = None

        # Reset entry fields
        self.map_name.delete(0, tk.END)
        self.map_name.insert(0, "Local House")
        self.origin_lat.delete(0, tk.END)
        self.origin_lat.insert(0, "59.3240")
        self.origin_lon.delete(0, tk.END)
        self.origin_lon.insert(0, "18.0700")
        self.camera_id.delete(0, tk.END)
        self.camera_height.delete(0, tk.END)
        self.camera_heading.delete(0, tk.END)

        # Clear canvas
        self.canvas.delete("all")

        # Reset mode and instructions
        self.mode = "room"
        self.instruction_var.set("Click 4 corners of the room (top-left, bottom-left, top-right, bottom-right)")
        self.coord_var.set("Coordinates: N/A")

        # Reload floor plan and grid
        self.load_floor_plan()

    def load_floor_plan(self):
        try:
            img = Image.open(self.floor_plan_path)
            orig_width, orig_height = img.size
            aspect_ratio = orig_width / orig_height
            canvas_width, canvas_height = 800, 600

            # Calculate new dimensions to fit within 800x600 while preserving aspect ratio
            if aspect_ratio > canvas_width / canvas_height:
                new_width = canvas_width
                new_height = int(canvas_width / aspect_ratio)
            else:
                new_height = canvas_height
                new_width = int(canvas_height * aspect_ratio)

            # Resize image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.floor_plan = ImageTk.PhotoImage(img)

            # Center the image on the canvas
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
        canvas_width, canvas_height = 800, 600
        for x in range(0, canvas_width, self.grid_spacing):
            self.canvas.create_line(x, 0, x, canvas_height, fill="#666666", dash=(2, 2))
        for y in range(0, canvas_height, self.grid_spacing):
            self.canvas.create_line(0, y, canvas_width, y, fill="#666666", dash=(2, 2))

    def is_convex_quadrilateral(self, points):
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
        x, y = event.x - self.image_offset[0], event.y - self.image_offset[1]
        if 0 <= x <= self.image_size[0] and 0 <= y <= self.image_size[1]:
            if self.mode == "room":
                self.add_corner(x, y)
            elif self.mode == "camera":
                self.place_camera(x, y)

    def add_corner(self, x, y):
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
            # Add Origin label for bottom-left (index 1)
            bl_x, bl_y = self.corners[1]
            display_x = bl_x + self.image_offset[0] - 15  # 15px left
            display_y = bl_y + self.image_offset[1] + 15  # 15px down
            self.origin_label_id = self.canvas.create_text(
                display_x, display_y,
                text="Origin",
                fill="red",
                font=("Arial", 12, "bold")
            )
            self.instruction_var.set("Click a side label to set its length")
            self.mode = "set_length"
            self.display_side_lengths(use_pixels=True)
            self.bind_side_labels()
        else:
            self.instruction_var.set(f"Click corner {len(self.corners) + 1} of 4")

    def undo_corner(self):
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
        for label_id in self.side_label_ids:
            self.canvas.tag_bind(label_id, "<Button-1>", lambda event, lid=label_id: self.set_side_length(lid))

    def set_side_length(self, label_id):
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

            # Calculate meters_per_pixel based on selected side
            side_indices = {
                "top-left_to_bottom-left": (0, 1),
                "bottom-left_to_top-right": (1, 2),
                "top-right_to_bottom-right": (2, 3),
                "bottom-right_to_top-left": (3, 0)
            }
            idx1, idx2 = side_indices[side_name]
            p1, p2 = self.corners[idx1], self.corners[idx2]
            pixel_dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            self.meters_per_pixel = length / pixel_dist

            # Calculate relative and geocoordinates
            self.room_corners_relative = []
            self.room_corners_geo = []
            corner_order = [0, 1, 2, 3]
            bl_geo = self.origin_geo
            self.room_corners_geo.append(None)  # Top-left
            self.room_corners_geo.append(bl_geo)  # Bottom-left
            bl = self.corners[1]
            # Bottom-right
            br_x = (self.corners[3][0] - bl[0]) * self.meters_per_pixel
            br_y = (self.corners[3][1] - bl[1]) * self.meters_per_pixel
            br_dist = math.sqrt(br_x**2 + br_y**2)
            br_bearing = math.degrees(math.atan2(br_x, br_y)) % 360
            br_geo = geodesic(meters=br_dist).destination(bl_geo, bearing=br_bearing)
            self.room_corners_geo.append(None)  # Top-right
            self.room_corners_geo.append((br_geo.latitude, br_geo.longitude))

            for idx in corner_order:
                px, py = self.corners[idx]
                x = (px - bl[0]) * self.meters_per_pixel
                y = (py - bl[1]) * self.meters_per_pixel
                self.room_corners_relative.append([x, y, 0])
                if idx == 1 or idx == 3:
                    continue
                temp_point = geodesic(meters=y).destination(bl_geo, bearing=0) if y >= 0 else geodesic(meters=-y).destination(bl_geo, bearing=180)
                final_point = geodesic(meters=x).destination(temp_point, bearing=90) if x >= 0 else geodesic(meters=-x).destination(temp_point, bearing=270)
                self.room_corners_geo[idx] = (final_point.latitude, final_point.longitude)

            # Validate geocoordinate distance
            bl_geo = self.room_corners_geo[1]
            br_geo = self.room_corners_geo[3]
            geo_distance = geodesic(bl_geo, br_geo).meters
            if abs(geo_distance - self.calculate_side_length(1, 3)) > 0.1:
                messagebox.showwarning("Warning", f"Geocoordinate distance ({geo_distance:.2f}m) differs from calculated length ({self.calculate_side_length(1, 3):.2f}m)")

            # Calculate side lengths
            self.side_lengths = {
                "top-left_to_bottom-left": self.calculate_side_length(0, 1),
                "bottom-left_to_top-right": self.calculate_side_length(1, 2),
                "top-right_to_bottom-right": self.calculate_side_length(2, 3),
                "bottom-right_to_top-left": self.calculate_side_length(3, 0)
            }

            # Update canvas with transparent room outline
            adjusted_corners = [(x + self.image_offset[0], y + self.image_offset[1]) for x, y in [self.corners[i] for i in corner_order]]
            self.canvas.create_polygon(
                [c for corner in adjusted_corners for c in corner],
                outline="red",
                dash=(10, 10),
                fill="",
                width=2,
                tags="room_outline"
            )

            # Update side lengths with meter values
            for label_id in self.side_label_ids:
                self.canvas.delete(label_id)
            self.side_label_ids = []
            self.side_label_map = {}
            self.display_side_lengths(use_pixels=False)

            self.instruction_var.set("Enter camera ID, height, and heading, then click to place")
            self.mode = "camera"
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def calculate_side_length(self, idx1, idx2):
        p1, p2 = self.corners[idx1], self.corners[idx2]
        pixel_dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        if self.meters_per_pixel is None:
            return pixel_dist
        return round(pixel_dist * self.meters_per_pixel, 3)

    def display_side_lengths(self, use_pixels=False):
        for label_id in self.side_label_ids:
            self.canvas.delete(label_id)
        self.side_label_ids = []
        self.side_label_map = {}

        sides = [
            (0, 1, "top-left_to_bottom-left"),
            (1, 2, "bottom-left_to_top-right"),
            (2, 3, "top-right_to_bottom-right"),
            (3, 0, "bottom-right_to_top-left")
        ]

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

            offset_x, offset_y = 0, 0
            if side_name == "top-left_to_bottom-left":
                offset_x = 25
            elif side_name == "top-right_to_bottom-right":
                offset_x = -25
            elif side_name == "bottom-left_to_top-right":
                offset_y = -10
            elif side_name == "bottom-right_to_top-left":
                offset_y = 10

            label_id = self.canvas.create_text(
                mid_x + offset_x,
                mid_y + offset_y,
                text=text,
                fill="red",
                font=("Arial", 12, "bold")
            )
            self.side_label_ids.append(label_id)
            self.side_label_map[label_id] = side_name

    def start_camera_placement(self):
        if not self.room_length or len(self.corners) != 4:
            messagebox.showerror("Error", "Please define room first")
            return
        if not self.camera_id.get():
            messagebox.showerror("Error", "Please enter a camera ID")
            return
        try:
            camera_id = int(self.camera_id.get())
            if camera_id < 1:
                raise ValueError("Camera ID must be a positive integer")
            z = float(self.camera_height.get())
            heading = float(self.camera_heading.get())
            if z < 0:
                raise ValueError("Height must be non-negative")
            if not 0 <= heading <= 360:
                raise ValueError("Heading must be 0-360 degrees")
            self.current_camera = {"id": camera_id, "z": z, "heading": heading}
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def place_camera(self, x, y):
        if not hasattr(self, "current_camera"):
            messagebox.showerror("Error", "Please set camera details first")
            return

        bl = self.corners[1]
        x_rel = (x - bl[0]) * self.meters_per_pixel
        y_rel = (y - bl[1]) * self.meters_per_pixel
        z = self.current_camera["z"]

        bl_geo = self.room_corners_geo[1]
        temp_point = geodesic(meters=y_rel).destination(bl_geo, bearing=0) if y_rel >= 0 else geodesic(meters=-y_rel).destination(bl_geo, bearing=180)
        final_point = geodesic(meters=x_rel).destination(temp_point, bearing=90) if x_rel >= 0 else geodesic(meters=-x_rel).destination(temp_point, bearing=270)
        lat, lon = final_point.latitude, final_point.longitude

        camera_id = str(self.current_camera["id"])
        self.camera_positions[camera_id] = {
            "geocoordinates": [lat, lon],
            "relative_pos": [x_rel, y_rel, z],
            "height": z,
            "heading": self.current_camera["heading"]
        }

        display_x = x + self.image_offset[0]
        display_y = y + self.image_offset[1]
        circle_id = self.canvas.create_oval(display_x-5, display_y-5, display_x+5, display_y+5, fill="green")
        label_id = self.canvas.create_text(display_x, display_y-10, text=f"ID {camera_id}", fill="#DEDEDE")
        self.camera_circles.append(circle_id)
        self.camera_labels.append(label_id)
        messagebox.showinfo("Success", f"Camera ID {camera_id} placed at ({x_rel:.2f}, {y_rel:.2f}, {z})")
        del self.current_camera

    def undo_camera(self):
        if self.camera_positions:
            last_id = max(self.camera_positions.keys(), key=int)
            self.camera_positions.pop(last_id)
            self.canvas.delete(self.camera_circles.pop())
            self.canvas.delete(self.camera_labels.pop())
            self.instruction_var.set("Enter camera ID, height, and heading, then click to place")

    def preview_coordinates(self, event):
        x = event.x - self.image_offset[0]
        y = event.y - self.image_offset[1]

        # Check if cursor is within image bounds
        within_image = 0 <= x <= self.image_size[0] and 0 <= y <= self.image_size[1]

        # Update coordinate preview label
        if self.mode != "camera" or not self.room_length or len(self.corners) != 4:
            self.coord_var.set("Coordinates: N/A")
        else:
            if within_image:
                # Calculate geocoordinates
                bl = self.corners[1]
                x_rel = (x - bl[0]) * self.meters_per_pixel
                y_rel = (y - bl[1]) * self.meters_per_pixel
                bl_geo = self.room_corners_geo[1]
                temp_point = geodesic(meters=y_rel).destination(bl_geo, bearing=0) if y_rel >= 0 else geodesic(meters=-y_rel).destination(bl_geo, bearing=180)
                final_point = geodesic(meters=x_rel).destination(temp_point, bearing=90) if x_rel >= 0 else geodesic(meters=-x_rel).destination(temp_point, bearing=270)
                lat, lon = final_point.latitude, final_point.longitude
                self.coord_var.set(f"Coordinates: ({lat:.6f}, {lon:.6f})")
            else:
                self.coord_var.set("Coordinates: N/A")

        # Update hover text
        if within_image:
            if self.mode == "room" and len(self.corners) < 4:
                # Show corner-specific instructions
                corner_names = ["TL point", "BL point", "BR point", "TR point"]
                hover_text = f"Set {corner_names[len(self.corners)]}"
            elif self.mode != "camera" or not self.room_length or len(self.corners) != 4:
                # Show pixel coordinates
                hover_text = f"Pixel: ({x:.0f}, {y:.0f})"
            else:
                # Show geocoordinates
                bl = self.corners[1]
                x_rel = (x - bl[0]) * self.meters_per_pixel
                y_rel = (y - bl[1]) * self.meters_per_pixel
                bl_geo = self.room_corners_geo[1]
                temp_point = geodesic(meters=y_rel).destination(bl_geo, bearing=0) if y_rel >= 0 else geodesic(meters=-y_rel).destination(bl_geo, bearing=180)
                final_point = geodesic(meters=x_rel).destination(temp_point, bearing=90) if x_rel >= 0 else geodesic(meters=-x_rel).destination(temp_point, bearing=270)
                lat, lon = final_point.latitude, final_point.longitude
                hover_text = f"Geo: ({lat:.6f}, {lon:.6f})"

            if self.hover_text_id is None:
                # Create new hover text
                self.hover_text_id = self.canvas.create_text(
                    event.x + 10,
                    event.y + 10,
                    text=hover_text,
                    fill="#FF0000",
                    font=("Arial", 12),
                    tags="hover_text",
                    anchor="nw"
                )
            else:
                # Update existing hover text
                self.canvas.itemconfig(self.hover_text_id, text=hover_text)
                self.canvas.coords(self.hover_text_id, event.x + 10, event.y + 10)
        else:
            # Remove hover text if outside image
            if self.hover_text_id is not None:
                self.canvas.delete("hover_text")
                self.hover_text_id = None

        # Update crosshair lines
        if within_image:
            if self.crosshair_h_id is None:
                # Create horizontal crosshair
                self.crosshair_h_id = self.canvas.create_line(
                    0, event.y, 800, event.y,
                    fill="#FF0000",
                    dash=(8, 8),
                    tags="crosshair"
                )
            else:
                # Update horizontal crosshair
                self.canvas.coords(self.crosshair_h_id, 0, event.y, 800, event.y)

            if self.crosshair_v_id is None:
                # Create vertical crosshair
                self.crosshair_v_id = self.canvas.create_line(
                    event.x, 0, event.x, 600,
                    fill="#FF0000",
                    dash=(8, 8),
                    tags="crosshair"
                )
            else:
                # Update vertical crosshair
                self.canvas.coords(self.crosshair_v_id, event.x, 0, event.x, 600)
        else:
            # Remove crosshair lines if outside image
            self.canvas.delete("crosshair")
            self.crosshair_h_id = None
            self.crosshair_v_id = None

    def save_configuration(self):
        config = {
            "name": self.map_name.get(),
            "corners": self.room_corners_geo,
            "room": {
                "length": self.room_length,
                "side_lengths": self.side_lengths
            },
            "cameras": {
                k: {
                    "geocoordinates": v["geocoordinates"],
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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

if __name__ == "__main__":
    app = MapConfigGUI()
