import json
import os
import subprocess
import requests
from requests.auth import HTTPDigestAuth
from ax_devil_device_api import Client, DeviceConfig

class Camera:
    """Class to represent a camera and its configuration.
    Manual configuration with configure_camera() function for now.

    Example usage: cam1 = Camera(...).configure_camera(...)
    """

    def __init__(
        self,
        id: int = 1,
        geocoords: tuple = (0, 0),
        ip: str = "192.168.0.93",
        username: str = "student",
        password: str = "student_pass",
    ):
        self.id = id
        self.ip = ip
        self.geocoords = geocoords
        self.username = username
        self.password = password
        self.config = (
            DeviceConfig(self.ip, "student", "student_pass", verify_ssl=False)
        )

        self._add_to_config()
        self.configure_mqtt_frame_metadata()

    def configure_camera(
        self,
        lat: float,
        lon: float,
        inst_height: float,
        heading: float,
        tilt: float = 0,
        roll: float = 0,
    ) -> None:
        """Configure the camera settings using curl commands."""
        with Client(self.config) as client:
            client.geocoordinates.set_location(
                lat,
                lon,
            )
            client.geocoordinates.set_orientation(
                {
                    "heading": heading,
                    "tilt": tilt,
                    "roll": roll,
                    "installation_height": inst_height,
                }
            )
            # client.geocoordinates.apply_settings() # Automatically sets roll so dont use!

            self.geocoords = (lat, lon)


    def save_snapshot(self):
        """Save a snapshot from the camera."""
        assets_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(assets_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
        os.chdir(assets_dir)

        try:
            response = requests.get(
                f"http://{self.ip}/axis-cgi/jpg/image.cgi?resolution=1920x1080",
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=10
            )
            response.raise_for_status()
            with open(f"{self.id}_snapshot.jpg", "wb") as f:
                f.write(response.content)
            print(f"Snapshot saved as {self.id}_snapshot.jpg")
        except requests.RequestException as e:
            print(f"Failed to save snapshot for {self.ip}: {str(e)}")

    def _add_to_config(self) -> None:
        """Add the camera dynamically to the config file."""
        config_file = "external/RTSPtoWebRTC/config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)

            streams = config.get("streams", {})
            if self.id not in streams:
                print("Adding camera to config file")
                streams[self.id] = {
                    "on_demand": False,
                    "disable_audio": True,
                    "url": f"rtsp://{self.username}:{self.password}@{self.ip}/axis-media/media.amp",
                }
                config["streams"] = streams
                with open(config_file, "w") as f:
                    json.dump(config, f, indent=4)
        else:
            print("Config file not found")
            return

    @DeprecationWarning
    def _set_cameras_geocoords(self):
        """USE configure_camera() instead. Fetch geocoordinates from the camera using a curl command."""
        result = subprocess.run(
            f"curl --digest -u {self.username}:{self.password} http://{self.ip}/axis-cgi/geolocation/get.cgi",
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("Curl command executed successfully")
        else:
            print("Failed to fetch geocoordinates")
            print("Error:", result.stderr)

        output = result.stdout
        test = output.splitlines()
        for line in test:
            if "Lat" in line:
                lat = line.split(">")[1].split("<")[0]
            if "Lng" in line:
                lng = line.split(">")[1].split("<")[0]
                self.geocoords = (lat, lng)

    def configure_mqtt_frame_metadata(self, mqtt_topic=None):
        """
        Check if an MQTT publisher with ID 'frame_metadata' and data source key
        'com.axis.analytics_scene_description.v0.beta#1' exists. If not, create one.
        """
        base_url = f"http://{self.ip}/config/rest/analytics-mqtt/v1beta"
        headers = {"accept": "application/json"}

        if mqtt_topic is None:
            mqtt_topic = f"{self.id}/frame_metadata"
        
        try:
            # Step 1: Retrieve existing publishers
            response = requests.get(
                f"{base_url}/publishers",
                auth=HTTPDigestAuth(self.username, self.password),
                headers=headers,
                timeout=10
            )

            response.raise_for_status()
            publishers = response.json().get("data", [])
            
            publisher_exists = False
            for publisher in publishers:
                if (publisher.get("mqtt_topic") == mqtt_topic):
                    publisher_exists = True
                    print(f"MQTT publisher 'frame_metadata' already exists on {self.ip}")
                    break
                elif (publisher.get("data_source_key") == "com.axis.analytics_scene_description.v0.beta#1"):
                    # remove the old publisher if it exists
                    print(f"Removing old publisher with data source key on {self.ip}")
                    delete_response = requests.delete(
                        f"{base_url}/publishers/{publisher['id']}",
                        auth=HTTPDigestAuth(self.username, self.password),
                        headers=headers,
                        timeout=10
                    )
                    delete_response.raise_for_status()
                    if delete_response.json().get("status") == "success":
                        print(f"Removed old publisher with data source key on {self.ip}")
                    else:
                        print(f"Failed to remove old publisher on {self.ip}: {delete_response.text}")

            
            # Step 2: Create publisher if it doesn't exist
            if not publisher_exists:
                payload = {
                    "data": {
                        "id": "frame_metadata",
                        "data_source_key": "com.axis.analytics_scene_description.v0.beta#1",
                        "mqtt_topic": mqtt_topic
                    }
                }
                response = requests.post(
                    f"{base_url}/publishers",
                    auth=HTTPDigestAuth(self.username, self.password),
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                if response.json().get("status") == "success":
                    print(f"Created MQTT publisher 'frame_metadata' on {self.ip} with topic {mqtt_topic}")
                else:
                    print(f"Failed to create MQTT publisher on {self.ip}: {response.text}")
        
        except requests.RequestException as e:
            print(f"Error configuring MQTT publisher on {self.ip}: {str(e)}")
            print("Ensure camera firmware >= 12.2, MQTT client is configured, and credentials are correct.")

def clear_streams():
    """Clear all streams in the config file."""
    config_file = "external/RTSPtoWebRTC/config.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)

        streams = config.get("streams", {})
        streams = {}
        config["streams"] = streams
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
    else:
        print("Config file not found")
        return