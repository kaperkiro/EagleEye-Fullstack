import paho.mqtt.client as mqtt
import json
import time
import math
import sys  # Import sys to access command line arguments


class MqttPublisher:
    # Define paths for different camera IDs (using string keys for flexibility)
    PATHS = {
        "1": [  # Entrance -> Kitchen -> Around (for Camera 1)
            [59.32415, 18.07040],  # 0: Start near entrance door
            [59.32450, 18.07040],  # 1: Move further up hallway (straight)
            [59.32450, 18.07065],  # 2: Turn right towards Kitchen/Living
            [59.32480, 18.07080],  # 3: Middle of Kitchen Area
            [59.32450, 18.07090],  # 4: Near Dining Table
            [59.32430, 18.07070],  # 5: Living Room Sofa Area
            [59.32460, 18.07060],  # 6: Moving back towards kitchen start
        ],
        "2": [  # Walk around large bedroom (top-left) (for Camera 2)
            [59.32465, 18.07025],  # 0: Enter near door
            [59.32490, 18.07025],  # 1: Walk towards window
            [59.32490, 18.07005],  # 2: Walk along window wall (left)
            [59.32475, 18.07005],  # 3: Turn back (down)
            [59.32475, 18.07015],  # 4: Stop mid-room
            [59.32465, 18.07015],  # 5: Move towards door again
        ],
        "3": [  # Stay in bathroom (top-middle) (for Camera 3)
            [59.32465, 18.07035],  # 0: Enter near door
            [59.32485, 18.07035],  # 1: Walk to sink area
            [59.32485, 18.07045],  # 2: Walk towards shower area
            [59.32475, 18.07045],  # 3: Move slightly back
            [59.32475, 18.07035],  # 4: Back towards sink area
        ],
    }

    def __init__(
        self,
        broker_host="localhost",
        broker_port=1883,
        topic="axis/frame_metadata",  # Base topic, camera_id added below
        publish_interval=0.5,
        camera_id=1,  # Default camera_id
        speed=0.00005,
        # track_id is now derived from camera_id
    ):
        self.camera_id = camera_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        # Set topic based on camera_id
        self.topic = f"axis/{self.camera_id}/frame_metadata"
        self.publish_interval = publish_interval
        self.speed = speed
        # Derive track_id from camera_id
        self.track_id = f"person{self.camera_id}"
        self.client = mqtt.Client()

        # Select path based on camera_id (convert to string for dict lookup)
        camera_id_str = str(self.camera_id)
        self.path = self.PATHS.get(
            camera_id_str, self.PATHS["1"]
        )  # Default to path "1"
        if not self.path:  # Should not happen with the default, but good practice
            raise ValueError(f"No path defined for camera_id: {self.camera_id}")

        self.current_waypoint_index = 0
        self.current_pos = list(
            self.path[0]
        )  # Start at the first waypoint of the selected path

    def connect(self):
        # ...existing code...
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()

    def disconnect(self):
        # ...existing code...
        self.client.loop_stop()
        self.client.disconnect()

    def _move_towards_waypoint(self):
        # ... (rest of the method remains the same) ...
        target_waypoint = self.path[self.current_waypoint_index]
        lat_diff = target_waypoint[0] - self.current_pos[0]
        lon_diff = target_waypoint[1] - self.current_pos[1]

        # Use a small tolerance to handle floating point comparisons
        tolerance = self.speed / 2  # Or a small fixed value like 1e-7

        moved = False
        # Prioritize moving vertically (latitude) first
        if abs(lat_diff) > tolerance:
            move_lat = math.copysign(self.speed, lat_diff)
            # Prevent overshooting the target latitude
            if abs(move_lat) > abs(lat_diff):
                move_lat = lat_diff
            self.current_pos[0] += move_lat
            moved = True

        # If latitude is aligned (or was just moved), move horizontally (longitude)
        elif abs(lon_diff) > tolerance:
            move_lon = math.copysign(self.speed, lon_diff)
            # Prevent overshooting the target longitude
            if abs(move_lon) > abs(lon_diff):
                move_lon = lon_diff
            self.current_pos[1] += move_lon
            moved = True

        # If no movement occurred, we are at the waypoint
        if not moved:
            self.current_pos = list(target_waypoint)  # Snap to waypoint
            self.current_waypoint_index = (self.current_waypoint_index + 1) % len(
                self.path
            )

    def publish_dummy_data(self):
        self._move_towards_waypoint()

        dummy_payload = {
            "frame": {
                "observations": [
                    {
                        "bounding_box": {  # Static bounding box for simplicity
                            "bottom": 0.6,
                            "left": 0.45,
                            "right": 0.55,
                            "top": 0.4,
                        },
                        "class": {
                            "lower_clothing_colors": [{"name": "Blue", "score": 0.8}],
                            "score": 0.95,
                            "type": "Human",
                            "upper_clothing_colors": [{"name": "White", "score": 0.75}],
                        },
                        "geoposition": {
                            "latitude": self.current_pos[0],
                            "longitude": self.current_pos[1],
                        },
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "track_id": self.track_id,  # Uses the derived track_id
                    }
                ],
                "operations": [],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        }
        payload_str = json.dumps(dummy_payload)
        self.client.publish(self.topic, payload_str, qos=0)

    def run(self):
        self.connect()
        print(
            f"Starting dummy publisher for Camera ID {self.camera_id} (Track '{self.track_id}') on topic '{self.topic}'..."
        )
        path_desc = "Custom Path"
        camera_id_str = str(self.camera_id)
        if camera_id_str == "1":
            path_desc = "Entrance -> Kitchen -> Around"
        elif camera_id_str == "2":
            path_desc = "Large Bedroom"
        elif camera_id_str == "3":
            path_desc = "Bathroom"
        print(
            f"Simulating path: {path_desc}. Speed: {self.speed} deg/interval. Interval: {self.publish_interval}s"
        )
        try:
            while True:
                self.publish_dummy_data()
                time.sleep(self.publish_interval)
        except KeyboardInterrupt:
            print(
                f"Stopping dummy publisher for Camera ID {self.camera_id} (Track '{self.track_id}')."
            )
        finally:
            self.disconnect()


if __name__ == "__main__":
    # Default values
    camera_id = 1
    interval = 0.2
    speed = 0.00001

    if len(sys.argv) > 1:
        try:
            requested_id = int(sys.argv[1])
            if str(requested_id) in MqttPublisher.PATHS:
                camera_id = requested_id
            else:
                print(
                    f"Warning: Camera ID '{requested_id}' not found in defined paths. Using default ID 1."
                )
                print(f"Available IDs: {list(MqttPublisher.PATHS.keys())}")
                camera_id = 1  # Keep default
        except ValueError:
            print(
                f"Warning: Invalid Camera ID '{sys.argv[1]}'. Must be an integer. Using default ID 1."
            )
            camera_id = 1  # Keep default

    publisher = MqttPublisher(
        camera_id=camera_id, publish_interval=interval, speed=speed
    )
    publisher.run()
