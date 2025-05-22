import json
import os
from typing import Dict, Tuple

import requests
from requests.auth import HTTPDigestAuth

from app.camera.webrtc import add_camera_to_config
from ax_devil_device_api import Client, DeviceConfig
from app.logger import get_logger

logger = get_logger("CAMERA")
CAM_TILT_OFFSET = 3  # degrees fine-tuning offset for tilt

class Camera:
    """Represents a camera with configuration for geocoordinates and MQTT publishing.

    Example usage:
        camera = Camera(id=1, ip="192.168.0.93")
        camera.configure_camera(lat=59.3245, lon=18.0705, inst_height=2.5, heading=90)
    """

    def __init__(
        self,
        id: int = 1,
        geocoordinates: Tuple[float, float] = (0.0, 0.0),
        ip: str = "192.168.0.93",
        username: str = "student",
        password: str = "student_pass",
    ):
        """Initialize camera with ID, IP, and credentials."""
        self.id = id
        self.ip = ip
        self.geocoordinates = geocoordinates
        self.username = username
        self.password = password
        self.config = DeviceConfig(self.ip, username, password, verify_ssl=False)
        self._last_settings = self.get_last_settings()

        self._configure_mqtt_publisher(
            topic=f"{self.id}/frame_metadata",
            publisher_key="com.axis.analytics_scene_description.v0.beta#1",
        )
        add_camera_to_config(cam_id=self.id, cam_ip=self.ip, cam_username=self.username, cam_password=self.password)

    def configure_camera(
        self,
        lat: float,
        lon: float,
        inst_height: float,
        heading: float,
    ) -> None:
        """Configure camera geocoordinates and orientation, defaulting to last settings.

        Args:
            lat: Latitude (degrees), defaults to last known latitude.
            lon: Longitude (degrees), defaults to last known longitude.
            inst_height: Camera height (meters), defaults to last known height.
            heading: Camera heading (degrees), defaults to last known heading.
            tilt: Camera tilt (degrees), defaults to last known tilt.
            roll: Camera roll (degrees), defaults to last known roll.
        """
        with Client(self.config) as client:

            # Apply settings
            client.geocoordinates.set_location(lat, lon)
            client.geocoordinates.apply_settings() # automatically sets tilt and roll

            # Retrieve last settings
            last_settings = self.get_last_settings() # retrieve automatically set tilt
            adjusted_tilt = last_settings["tilt"] + CAM_TILT_OFFSET
            
            client.geocoordinates.set_orientation({
                "heading": heading,
                "tilt": adjusted_tilt,
                "roll": 0, # roll doesnt work coorectly so we set it to 0
            })
            logger.info(f"Configured camera {self.id} at {self.ip} with settings:\n\t\t\t| lat: {lat}, lng: {lon}, height: {inst_height}, heading: {heading}, tilt: {adjusted_tilt}, roll: {0}")


    def get_last_settings(self) -> Dict[str, float]:
        """Retrieve current camera settings from the device.

        Returns:
            Dictionary with latitude, longitude, inst_height, heading, tilt, and roll.
        """
        try:
            with Client(self.config) as client:
                location = client.geocoordinates.get_location()
                orientation = client.geocoordinates.get_orientation()
                return {
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "installation_height": orientation["installation_height"],
                    "heading": orientation["heading"],
                    "tilt": orientation["tilt"],
                    "roll": orientation["roll"],
                }
        except Exception as e:
            logger.error(f"Failed to retrieve settings for {self.ip}: {e}")
            return {
                "latitude": 0.0,
                "longitude": 0.0,
                "installation_height": 0.0,
                "heading": 0.0,
                "tilt": 0.0,
                "roll": 0.0,
            }

    def save_snapshot(self) -> None:
        """Save a snapshot from the camera to assets directory."""
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        os.makedirs(assets_dir, exist_ok=True)

        try:
            response = requests.get(
                f"http://{self.ip}/axis-cgi/jpg/image.cgi?resolution=1920x1080",
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=10,
            )
            response.raise_for_status()
            snapshot_path = os.path.join(assets_dir, f"{self.id}_snapshot.jpg")
            with open(snapshot_path, "wb") as file:
                file.write(response.content)
            logger.info(f"Snapshot saved as {snapshot_path}")
        except requests.RequestException as e:
            logger.error(f"Failed to save snapshot for {self.ip}: {e}")

    def _configure_mqtt_publisher(self, topic: str, publisher_key: str) -> None:
        """Configure MQTT publisher if it doesn't exist or has a different topic.

        Args:
            topic: MQTT topic (e.g., "1/frame_metadata").
            publisher_key: Data source key (e.g., "com.axis.analytics_scene_description.v0.beta#1").
        """
        base_url = f"http://{self.ip}/config/rest/analytics-mqtt/v1beta/publishers"
        headers = {"accept": "application/json"}
        publisher_id = topic.split("/")[1]

        try:
            # Check existing publishers
            response = requests.get(
                base_url,
                auth=HTTPDigestAuth(self.username, self.password),
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            publishers = response.json().get("data", [])

            for publisher in publishers:
                if publisher.get("mqtt_topic") == topic:
                    logger.info(f"MQTT publisher '{publisher_id}' exists on {self.ip} with topic {topic}")
                    return
                if publisher.get("data_source_key") == publisher_key:
                    # Remove old publisher with same data source key
                    response = requests.delete(
                        f"{base_url}/{publisher['id']}",
                        auth=HTTPDigestAuth(self.username, self.password),
                        headers=headers,
                        timeout=10,
                    )
                    response.raise_for_status()
                    if response.json().get("status") != "success":
                        logger.error(f"Failed to remove old publisher on {self.ip}")
                    else:
                        logger.info(f"Removed old publisher on {self.ip}")

            # Create new publisher
            payload = {
                "data": {
                    "id": publisher_id,
                    "data_source_key": publisher_key,
                    "mqtt_topic": topic,
                }
            }
            response = requests.post(
                base_url,
                auth=HTTPDigestAuth(self.username, self.password),
                json=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            if response.json().get("status") == "success":
                logger.info(f"MQTT publisher '{publisher_id}' created on {self.ip} with topic {topic}")
            else:
                logger.error(f"Failed to create MQTT publisher on {self.ip}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Failed to configure MQTT publisher on {self.ip}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from {self.ip}: {e}")