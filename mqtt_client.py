import paho.mqtt.client as mqtt
import json
from typing import List, Dict, Any


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
        self.detections: Dict[int, List[Dict]] = {}  # Camera ID -> detections
        self._setup_callbacks()

        self.dict_position: Dict[int, List[tuple]] = (
            {}
        )  # Camera ID -> [latitude, longitude]
        self.position = []

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
        self.subscribe("axis/frame_metadata", qos=0)  # TODO: HARDCODED TOPIC

    def _on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        """Dynamic handling of multiple messages
        Stores all detections in a dictionary and only updates its own view of the data
        """
        try:
            camera_id = "camera1"  # TODO: FIX HARD CODED CAMERA ID
            payload = json.loads(msg.payload.decode())
            frame_data = payload.get("frame", {})
            self.detections[camera_id] = frame_data.get("observations", [])

            try:
                data = payload["frame"]["observations"]
                coords = []
                # clear the list of coordinates for the current camera ID
                if camera_id in self.dict_position:
                    self.dict_position[camera_id] = []
                for obs in data:
                    if "geoposition" in obs:
                        # Create key for camera ID if it doesn't exist and update
                        # the coordinates
                        if camera_id not in self.dict_position:
                            self.dict_position[camera_id] = []
                        self.dict_position[camera_id].append(
                            (
                                obs["geoposition"]["latitude"],
                                obs["geoposition"]["longitude"],
                            )
                        )

                        coords.append(
                            (
                                obs["geoposition"]["latitude"],
                                obs["geoposition"]["longitude"],
                            )
                        )

                        print(self.dict_position[camera_id])
            except (KeyError, IndexError) as e:
                print(f"Error extracting coordinates: {e}")
                coords = None
            if coords:
                # Will this ever not happen?
                self.position = coords
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
        return self.detections.get(camera_id, [])
