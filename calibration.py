import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
import cv2
from broker_manager import BrokerManager
from mqtt_client import MqttClient


# Updated FloorplanGUI class to integrate MQTT
class Calibration:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.root = tk.Tk()
        self.root.title("EagleEye Calibration Tool - ({})".format(self.camera_id))
        
        try:
            # Load the icon image (use a .png or .gif file)
            icon_image = tk.PhotoImage(file="logo_no_text.png")  # Replace with your icon file path
            self.root.iconphoto(True, icon_image)
        except tk.TclError as e:
            print(f"Failed to set window icon: {e}")

        # Paths to images (to be loaded)
        self.camera_image_path = None
        self.floorplan_image_path = None
        self.camera_image = None
        self.floorplan_image = None
        self.camera_photo = None  # For Tkinter canvas
        self.floorplan_photo = None  # For Tkinter canvas

        # Image dimensions (to be set after loading)
        self.camera_orig_width = None
        self.camera_orig_height = None
        self.floorplan_orig_width = None
        self.floorplan_orig_height = None
        self.camera_display_width = None
        self.camera_display_height = None
        self.floorplan_display_width = None
        self.floorplan_display_height = None
        self.camera_offset_x = 0  # Offset for centering
        self.camera_offset_y = 0
        self.floorplan_offset_x = 0
        self.floorplan_offset_y = 0

        # Homography matrix (to be computed)
        self.homography = None

        # Lists to store calibration points
        self.camera_points = []
        self.floorplan_points = []

        # State for calibration and tracking
        self.is_calibrating = False
        self.is_tracking = False
        self.current_point_index = 0  # For calibration
        self.dots = []  # For the red dots on the floor plan (support multiple objects)

        # GUI elements, dark mode just nu
        self.configure_gui_elements()

        # Ensure MQTT client is stopped when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start the main loop
        self.root.mainloop()

    def CenterWindowToDisplay(self, width: int, height: int):
        """Centers the window to the main display/monitor"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width/2) - (width/2))
        y = int((screen_height/2) - (height/1.5))
        return f"{width}x{height}+{x}+{y}"

    def configure_gui_elements(self):
        self.root.configure(bg="#333333") # top level container
        self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_pathname(self.root.winfo_id()))
        self.root.geometry(self.CenterWindowToDisplay(1330, 640)) # set window size and position

        # Frame for canvases
        self.canvas_frame = tk.Frame(self.root, bg="#333333", bd=2, relief=tk.FLAT, highlightthickness=0)
        self.canvas_frame.pack(pady=10)

        # Frame for camera canvas and its label
        self.camera_frame = tk.Frame(self.canvas_frame, bg="#333333")
        self.camera_frame.pack(side=tk.LEFT, padx=10)

        # Label for camera canvas
        self.camera_label = tk.Label(self.camera_frame, text="Camera View", bg="#333333", fg="white", font=("Arial", 12))
        self.camera_label.pack()

        # Canvas for camera image (left)
        self.canvas_width = 640
        self.canvas_height = 480
        self.camera_canvas = tk.Canvas(self.camera_frame, width=self.canvas_width, height=self.canvas_height, bg="#444444", highlightthickness=2, highlightbackground="#666666")
        self.camera_canvas.pack()

        # Frame for floorplan canvas and its label
        self.floorplan_frame = tk.Frame(self.canvas_frame, bg="#333333")
        self.floorplan_frame.pack(side=tk.LEFT, padx=10)

        # Label for floorplan canvas
        self.floorplan_label = tk.Label(self.floorplan_frame, text="Floor Plan", bg="#333333", fg="white", font=("Arial", 12))
        self.floorplan_label.pack()

        # Canvas for floor plan (right)
        self.floorplan_canvas = tk.Canvas(self.floorplan_frame, width=self.canvas_width, height=self.canvas_height, bg="#444444", highlightthickness=2, highlightbackground="#666666")
        self.floorplan_canvas.pack()

        # Frame for buttons
        self.button_frame = tk.Frame(self.root, bg="#333333")
        self.button_frame.pack(pady=10)

        self.load_button = tk.Button(self.button_frame, text="Load Images", command=self.load_images, bg="#333333", fg="#DEDEDE", width=20, height=2, activebackground="#666666", font=("Arial", 12), relief=tk.RIDGE, borderwidth=3)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.calibrate_button = tk.Button(self.button_frame, text="Calibrate (Mark Points)", command=self.start_calibration, state=tk.DISABLED, bg="#333333", fg="#DEDEDE", width=20, height=2, activebackground="#666666", font=("Arial", 12), relief=tk.RIDGE, borderwidth=3)
        self.calibrate_button.pack(side=tk.LEFT, padx=5)

        self.track_button = tk.Button(self.button_frame, text="Start Tracking", command=self.start_tracking, state=tk.DISABLED, bg="#333333", fg="#DEDEDE", width=20, height=2, activebackground="#666666", font=("Arial", 12), relief=tk.RIDGE, borderwidth=3)
        self.track_button.pack(side=tk.LEFT, padx=5)

        # Label for instructions
        self.instruction_label = tk.Label(self.root, text="Load images to start", bg="#333333", fg="#DEDEDE", font=("Arial", 15))
        self.instruction_label.pack(pady=3)

    def on_closing(self):
        """Handle window closing by stopping the MQTT client."""
        self.mqtt_client.stop()
        self.root.destroy()

    def resize_with_aspect_ratio(self, image, max_width, max_height):
        """Resize the image while preserving its aspect ratio."""
        orig_width, orig_height = image.size
        aspect_ratio = orig_width / orig_height

        # Calculate new dimensions
        if aspect_ratio > 1:  # Wider than tall
            new_width = min(max_width, orig_width)
            new_height = int(new_width / aspect_ratio)
            if new_height > max_height:
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
        else:  # Taller than wide
            new_height = min(max_height, orig_height)
            new_width = int(new_height * aspect_ratio)
            if new_width > max_width:
                new_width = max_width
                new_height = int(new_width / aspect_ratio)

        # Resize the image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Calculate offsets to center the image
        offset_x = (max_width - new_width) // 2
        offset_y = (max_height - new_height) // 2

        return resized_image, offset_x, offset_y, new_width, new_height

    def load_images(self):
        """Load the camera screenshot and floor plan image from the root folder."""
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.calibrate_button.config(text="Calibrate (Mark Points)")
        self.track_button.config(state=tk.DISABLED)
        # set to assets folder
        root_dir = os.path.join(root_dir, "assets")

        # Look for camera screenshot and floor plan in the root folder
        camera_files = [f for f in os.listdir(root_dir) if self.camera_id in f.lower() and f.endswith((".png", ".jpg", ".jpeg"))]
        floorplan_files = [f for f in os.listdir(root_dir) if "floor" in f.lower() and f.endswith((".png", ".jpg", ".jpeg"))]

        if not camera_files or not floorplan_files:
            self.load_button.config(text="Load Images", state=tk.NORMAL)
            messagebox.showerror("Error", "Could not find camera screenshot or floor plan image in root folder.")
            return

        # Use the first matching files
        self.camera_image_path = os.path.join(root_dir, camera_files[0])
        self.floorplan_image_path = os.path.join(root_dir, floorplan_files[0])

        try:
            # Load the images with PIL
            camera_img = Image.open(self.camera_image_path)
            floorplan_img = Image.open(self.floorplan_image_path)

            # Store original dimensions
            self.camera_orig_width, self.camera_orig_height = camera_img.size
            self.floorplan_orig_width, self.floorplan_orig_height = floorplan_img.size

            # Resize images while preserving aspect ratio
            camera_img, self.camera_offset_x, self.camera_offset_y, self.camera_display_width, self.camera_display_height = \
                self.resize_with_aspect_ratio(camera_img, self.canvas_width, self.canvas_height)
            floorplan_img, self.floorplan_offset_x, self.floorplan_offset_y, self.floorplan_display_width, self.floorplan_display_height = \
                self.resize_with_aspect_ratio(floorplan_img, self.canvas_width, self.canvas_height)

            # Convert to PhotoImage for Tkinter
            self.camera_photo = ImageTk.PhotoImage(camera_img)
            self.floorplan_photo = ImageTk.PhotoImage(floorplan_img)

            # Display the images on the canvases, centered
            self.camera_canvas.create_image(self.camera_offset_x, self.camera_offset_y, anchor=tk.NW, image=self.camera_photo)
            self.floorplan_canvas.create_image(self.floorplan_offset_x, self.floorplan_offset_y, anchor=tk.NW, image=self.floorplan_photo)

            # Update GUI
            self.instruction_label.config(text="Images loaded successfully")
            self.load_button.config(text="Reload Images")
            self.calibrate_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load images: {str(e)}")

    def start_calibration(self):
        """Start the calibration process by enabling clicking on the canvases."""
        if self.camera_photo is None or self.floorplan_photo is None:
            messagebox.showerror("Error", "Images not loaded.")
            return

        self.is_calibrating = True
        self.is_tracking = False
        self.current_point_index = 0
        self.camera_points = []
        self.floorplan_points = []
        self.calibrate_button.config(text="Clear Points")
        self.track_button.config(state=tk.DISABLED)

        # Clear any existing dots on the canvases
        self.camera_canvas.delete("dot")
        self.floorplan_canvas.delete("dot")
        for dot_id in self.dots:
            self.floorplan_canvas.delete(dot_id)
        self.dots = []

        # Update instructions
        self.instruction_label.config(text=f"Click point {self.current_point_index + 1} on the camera image")

        # Bind click events to the canvases
        self.camera_canvas.bind("<Button-1>", self.on_camera_click)
        self.floorplan_canvas.bind("<Button-1>", self.on_floorplan_click)

    def on_camera_click(self, event):
        """Handle clicks on the camera canvas during calibration."""
        if not self.is_calibrating:
            return

        # Adjust click coordinates for the centered image
        x = event.x - self.camera_offset_x
        y = event.y - self.camera_offset_y

        # Ensure the click is within the image bounds
        if 0 <= x < self.camera_display_width and 0 <= y < self.camera_display_height:
            # Scale the coordinates back to the original image size
            x_orig = x * (self.camera_orig_width / self.camera_display_width)
            y_orig = y * (self.camera_orig_height / self.camera_display_height)

            self.camera_points.append((x_orig, y_orig))
            # Draw a small blue dot to mark the point (at the display coordinates)
            self.camera_canvas.create_oval(
                event.x-3, event.y-3, event.x+3, event.y+3, fill="blue", tags="dot"
            )
            self.current_point_index += 1

            if self.current_point_index < 4:
                self.instruction_label.config(text=f"Click point {self.current_point_index + 1} on the camera image")
            else:
                self.instruction_label.config(text="Click the corresponding points on the floor plan")
                self.current_point_index = 0  # Reset for floor plan points

    def on_floorplan_click(self, event):
        """Handle clicks on the floor plan canvas during calibration."""
        if not self.is_calibrating or len(self.camera_points) < 4:
            return

        # Adjust click coordinates for the centered image
        x = event.x - self.floorplan_offset_x
        y = event.y - self.floorplan_offset_y

        # Ensure the click is within the image bounds
        if 0 <= x < self.floorplan_display_width and 0 <= y < self.floorplan_display_height:
            # Scale the coordinates back to the original image size
            x_orig = x * (self.floorplan_orig_width / self.floorplan_display_width)
            y_orig = y * (self.floorplan_orig_height / self.floorplan_display_height)

            self.floorplan_points.append((x_orig, y_orig))
            # Draw a small blue dot to mark the point (at the display coordinates)
            self.floorplan_canvas.create_oval(
                event.x-3, event.y-3, event.x+3, event.y+3, fill="blue", tags="dot"
            )
            self.current_point_index += 1

            if self.current_point_index < 4:
                self.instruction_label.config(text=f"Click point {self.current_point_index + 1} on the floor plan")
            else:
                # Calibration complete
                self.is_calibrating = False
                self.compute_homography()
                self.instruction_label.config(text="Calibration complete. Click 'Start Tracking' to begin.")
                self.track_button.config(state=tk.NORMAL)
                # Unbind the floor plan click event until tracking starts
                self.floorplan_canvas.unbind("<Button-1>")

    def compute_homography(self):
        """Compute the homography matrix from camera points to floor plan points."""
        # Convert points to numpy arrays
        src_points = np.array(self.camera_points, dtype=np.float32)
        dst_points = np.array(self.floorplan_points, dtype=np.float32)

        # Compute the homography matrix
        self.homography, _ = cv2.findHomography(src_points, dst_points)

        if self.homography is None:
            messagebox.showerror("Error", "Homography computation failed.")
            self.homography = None
            self.track_button.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("Success", "Calibration completed successfully!")

    def camera_to_floorplan(self, x_cam: float, y_cam: float) -> tuple:
        """Map a point from the camera image to the floor plan (in pixels)."""
        if self.homography is None:
            raise ValueError("Homography not computed. Complete calibration first.")

        # Convert the point to homogeneous coordinates
        point = np.array([[x_cam, y_cam, 1]], dtype=np.float32).T

        # Apply the homography
        transformed_point = self.homography @ point
        transformed_point /= transformed_point[2]  # Normalize by the homogeneous coordinate

        x_floor = transformed_point[0, 0]
        y_floor = transformed_point[1, 0]

        return x_floor, y_floor

    def process_camera_data(self, camera_data):
        """Process camera data and map detected objects to the floor plan."""
        if self.homography is None:
            return  # Silently return if homography isn't computed

        # Clear previous dots on the floor plan
        for dot_id in self.dots:
            self.floorplan_canvas.delete(dot_id)
        self.dots = []

        # Process each detection in the camera data
        for detection in camera_data:
            
            # Check the type of the detection
            detection_class = detection.get('class', {})
            detection_type = detection_class.get('type', '')

            # Only process detections where type is "Human"
            if detection_type != "Human":
                continue

            # Extract bounding box coordinates (normalized)
            bbox = detection.get('bounding_box', {})
            left = bbox.get('left')
            right = bbox.get('right')
            top = bbox.get('top')
            bottom = bbox.get('bottom')

            if not all([left, right, top, bottom]):  # Skip if bounding box is incomplete
                continue

            # Convert normalized coordinates to pixel coordinates in the original image
            x_left = left * self.camera_orig_width
            x_right = right * self.camera_orig_width
            y_bottom = bottom * self.camera_orig_height

            # Calculate the center of the bounding box
            x_center = (x_left + x_right) / 2

            # Map the center point to the floor plan (in original floor plan coordinates)
            try:
                x_floor, y_floor = self.camera_to_floorplan(x_center, y_bottom)

                # Scale the floor plan coordinates to the display size
                x_display = x_floor * (self.floorplan_display_width / self.floorplan_orig_width)
                y_display = y_floor * (self.floorplan_display_height / self.floorplan_orig_height)

                # Adjust for the centered position on the canvas
                x_display += self.floorplan_offset_x
                y_display += self.floorplan_offset_y

                # Draw a red dot on the floor plan
                dot_id = self.floorplan_canvas.create_oval(
                    x_display-5, y_display-5, x_display+5, y_display+5, fill="red"
                )
                self.dots.append(dot_id)

                # Update the instruction label with the mapped position
                self.instruction_label.config(text=f"Mapped object to floor plan at ({x_display:.1f}, {y_display:.1f})")

            except Exception as e:
                print(f"Failed to map point: {str(e)}")

    def start_tracking(self):
        """Start tracking by continuously processing MQTT data."""
        if self.homography is None:
            messagebox.showerror("Error", "Homography not computed. Complete calibration first.")
            return

        self.is_tracking = True
        self.is_calibrating = False

        def update():
            if not self.is_tracking:
                return
            # Fetch the latest detections from the MQTT client
            # camera_id = 1  # TODO: FIX HARD CODED CAMERA ID
            camera_data = self.mqtt_client.get_detections(self.camera_id)
            if camera_data:
                self.process_camera_data(camera_data)
            self.root.after(100, update)  # Update every 100ms

        # Start the update loop
        update()

        # Update instructions
        self.instruction_label.config(text="Tracking started. Receiving MQTT data...")


if __name__ == "__main__":
#     # Create the GUI
    # root = tk.Tk()
    # app = Calibration(root)
    # root.mainloop()
    app = Calibration()