import paho.mqtt.client as mqtt
import json
from typing import List, Dict, Any
from app.objects.manager import ObjectManager


class MqttClient:
    """MQTT client for receiving and processing messages from a broker.
    This class handles the connection to the MQTT broker, subscribes to topics,
    Hardcoded currently to "axis/frame_metadata" and processes incoming messages.
    """

    def __init__(self, broker_host="localhost", broker_port=1883, keepalive=60):

        self.broker_host = broker_host
        self.broker_port = broker_port
        self.keepalive = keepalive
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.object_manager = ObjectManager()
        self._setup_callbacks()

        self.dict_position: Dict[int, List[tuple]] = (
            {}
        )  # Camera ID -> [latitude, longitude]

    def _setup_callbacks(self) -> None:
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict,
        reason_code: int,
        properties: Any,
    ) -> None:
        print(f"Connected with result code {reason_code}")
        self.subscribe("+/frame_metadata", qos=0)

    def _on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        """Dynamic handling of multiple messages
        Stores all detections in a dictionary and only updates its own view of the data
        """
        try:

            payload = json.loads(msg.payload.decode())

            observations = payload.get("frame", {}).get("observations", [])
            camera_id = msg.topic.split("/")[0] # Extract camera ID from topic ("cam_id"/frame_metadata)
            print(f"Received observations on cam {camera_id}: {observations}\n")

            # Update global object tracking
            self.object_manager.add_observations(camera_id, observations)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse MQTT message: {e}")

    def connect(self) -> None:
        self.client.connect(self.broker_host, self.broker_port, self.keepalive)

    def subscribe(self, topic: str, qos: int = 0) -> None:
        self.client.subscribe(topic, qos=qos)

    def start_background_loop(self) -> None:
        self.client.loop_start()

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

    def get_detections(self, camera_id: int) -> List[Dict]:
        # Return globally tracked objects for the camera
        return self.object_manager.get_objects_by_camera(camera_id)
