import json
import os
import subprocess
import requests
from requests.auth import HTTPDigestAuth
from ax_devil_device_api import Client, DeviceConfig
from app.camera.webrtc import add_camera_to_config
import logging

logger = logging.getLogger(__name__)

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

        self._configure_mqtt_publisher(mqtt_topic=f"{self.id}/frame_metadata", publisher_key="com.axis.analytics_scene_description.v0.beta#1")
        # self._configure_mqtt_publisher(mqtt_topic=f"{self.id}/consolidated_metadata", publisher_key="com.axis.consolidated_track.v1.beta#1")

        add_camera_to_config(cam_id=self.id, cam_ip=self.ip, cam_username=self.username, cam_password=self.password)

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
            with open(f"app/assets/{self.id}_snapshot.jpg", "wb") as f:
                f.write(response.content)
            logger.info(f"Snapshot saved as {self.id}_snapshot.jpg")
        except requests.RequestException as e:
            logger.error(f"Failed to save snapshot for {self.ip}: {str(e)}")

    def _configure_mqtt_publisher(self, mqtt_topic=None, publisher_key=None):
        """
        Check if an MQTT publisher with ID 'frame_metadata' and data source key
        'com.axis.analytics_scene_description.v0.beta#1' exists. If not, create one.
        """
        base_url = f"http://{self.ip}/config/rest/analytics-mqtt/v1beta/publishers"
        headers = {"accept": "application/json"}
        publisher_id = mqtt_topic.split("/")[1]
        
        try:
            # Step 1: Retrieve existing publishers
            response = requests.get(
                f"{base_url}",
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
                    logger.info(f"MQTT publisher 'frame_metadata' already exists on {self.ip} with topic {mqtt_topic}")
                    break
                elif (publisher.get("data_source_key") == publisher_key):
                    # remove the old publisher if it exists with another topic
                    logger.info(f"Removing old publisher with data source key on {self.ip}")
                    delete_response = requests.delete(
                        f"{base_url}/{publisher['id']}",
                        auth=HTTPDigestAuth(self.username, self.password),
                        headers=headers,
                        timeout=10
                    )
                    delete_response.raise_for_status()
                    if delete_response.json().get("status") == "success":
                        logger.info(f"Removed old publisher on {self.ip}")
                    else:
                        logger.error(f"Failed to remove old publisher on {self.ip}: {delete_response.text}")
            
            # Step 2: Create publisher if it doesn't exist
            if not publisher_exists:
                payload = {
                    "data": {
                        "id": publisher_id,
                        "data_source_key": publisher_key,
                        "mqtt_topic": mqtt_topic
                    }
                }
                response = requests.post(
                    f"{base_url}",
                    auth=HTTPDigestAuth(self.username, self.password),
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                if response.json().get("status") == "success":
                    logger.info(f"MQTT publisher 'frame_metadata' created successfully on {self.ip} with topic {mqtt_topic}")
                else:
                    logger.error(f"Failed to create MQTT publisher on {self.ip}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Failed to configure MQTT publisher on {self.ip}: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from {self.ip}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        return mqtt_topic
    