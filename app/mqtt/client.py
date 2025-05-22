import paho.mqtt.client as mqtt
import json
from typing import List, Dict, Any
from app.logger import get_logger
import logging
import time
import socket


logger = get_logger("MQTT CLIENT")


class MqttClient:
    """MQTT client for receiving and processing messages from a broker.
    This class handles the connection to the MQTT broker, subscribes to topics,
    Hardcoded currently to "axis/frame_metadata" and processes incoming messages.
    """

    def __init__(
        self, object_manager, broker_host="localhost", broker_port=1883, keepalive=60
    ):
        """Initialize client, set callbacks, and connect to the broker."""
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.keepalive = keepalive
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.object_manager = object_manager
        self.first_message_received = False
        self._setup_callbacks()
        self.start()

    def _setup_callbacks(self) -> None:
        """Assign internal connect and message handlers to the MQTT client."""
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
        """Handle successful connection by subscribing to frame metadata topics."""
        logger.info(
            f"Connected to MQTT broker at {self.broker_host}:{self.broker_port} with result code: %s",
            reason_code,
        )
        self.subscribe("+/frame_metadata")
        # self.subscribe("+/consolidated_metadata")

    def _on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        """Dynamic handling of multiple messages
        Stores all detections in a dictionary and only updates its own view of the data
        """
        try:
            payload = json.loads(msg.payload.decode())
            observations = payload.get("frame", {}).get("observations", [])
            camera_id = msg.topic.split("/")[
                0
            ]  # Extract camera ID from topic ("cam_id"/frame_metadata)

            if not self.first_message_received:
                logging.getLogger("MAIN").info("\x1b[32;20m" + "SYSTEM READY!")
                self.first_message_received = True

            # Update global object tracking
            self.object_manager.add_observations(camera_id, observations)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error decoding JSON message: {e}")

    def connect(self) -> None:
        """Establish connection to the MQTT broker."""
        self.client.connect(self.broker_host, self.broker_port, self.keepalive)

    def subscribe(self, topic: str, qos: int = 0) -> None:
        """Subscribe to a MQTT topic with given QoS."""
        self.client.subscribe(topic, qos=qos)

    def start_background_loop(self) -> None:
        """Start the network loop in a background thread."""
        self.client.loop_start()

    def start(self) -> None:
        """Keep trying to connect until successful, then spin up the network loop."""
        while True:
            try:
                self.client.connect(self.broker_host, self.broker_port, self.keepalive)
            except (ConnectionRefusedError, socket.error) as e:
                logger.warning(f"MQTT connect failed ({e}), retrying in 3s…")
                time.sleep(3)
            else:
                logger.info(
                    f"Successfully connected to {self.broker_host}:{self.broker_port}"
                )
                break

        # once connected, start the background network loop
        self.client.loop_start()

    def stop(self) -> None:
        """Stop the network loop and disconnect from the broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def get_detections(self, camera_id: int) -> List[Dict]:
        """Retrieve latest detections for a given camera from object manager."""
        return self.object_manager.get_objects_by_camera(camera_id)
