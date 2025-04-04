import paho.mqtt.client as mqtt
import json
from typing import List, Dict, Any

class MqttClient:
    def __init__(self, broker_host="localhost", broker_port=1883, keepalive=60):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.keepalive = keepalive
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.detections: Dict[int, List[Dict]] = {}  # Camera ID -> detections
        self._setup_callbacks()
        
        self.position = []
        
    def _setup_callbacks(self) -> None:
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
    
    def _on_connect(self, client: mqtt.Client, userdata: Any, 
                   flags: dict, reason_code: int, properties: Any) -> None:
        print(f"Connected with result code {reason_code}")
        self.subscribe("axis/frame_metadata", qos=0)  # TODO: HARDCODED TOPIC 

    def _on_message(self, client: mqtt.Client, userdata: Any,
                   msg: mqtt.MQTTMessage) -> None:
        try:
            camera_id = 1 # TODO: FIX HARD CODED CAMERA ID
            payload = json.loads(msg.payload.decode())
            frame_data = payload.get("frame", {})
            self.detections[camera_id] = frame_data.get("observations", [])
            # print(f"Received message: {payload}")
            # coords = [obs.get("coords") for obs in frame_data.get("observations", []) if "coords" in obs]
            # print(f"Coordinates: {coords}")
            #Received message: {'frame': {'observations': [{'bounding_box': {'bottom': 0.9066, 'left': 0.0765, 'right': 0.4078, 'top': 0.1169}, 'class': {'lower_clothing_colors': [{'name': 'White', 'score': 0.36}], 'score': 0.79, 'type': 'Human', 'upper_clothing_colors': [{'name': 'White', 'score': 0.69}]}, 'timestamp': '2025-04-04T12:33:19.622048Z', 'track_id': '2350'}, {'bounding_box': {'bottom': 0.9984, 'left': 0.4598, 'right': 0.5938, 'top': 0.7766}, 'timestamp': '2025-04-04T12:33:19.622048Z', 'track_id': '2755'}, {'bounding_box': {'bottom': 0.3734, 'left': 0.6062, 'right': 0.6777, 'top': 0.0016}, 'timestamp': '2025-04-04T12:33:19.622048Z', 'track_id': '2774'}, {'bounding_box': {'bottom': 0.8422, 'left': 0.933, 'right': 0.9526, 'top': 0.7922}, 'timestamp': '2025-04-04T12:33:19.622048Z', 'track_id': '2781'}, {'bounding_box': {'bottom': 0.8516, 'left': 0.958, 'right': 0.9847, 'top': 0.7922}, 'timestamp': '2025-04-04T12:33:19.622048Z', 'track_id': '2782'}, {'bounding_box': {'bottom': 0.2454, 'left': 0.8866, 'right': 0.9687, 'top': 0.1985}, 'timestamp': '2025-04-04T12:33:19.622048Z', 'track_id': '2796'}, {'bounding_box': {'bottom': 0.161, 'left': 0.9723, 'right': 0.9803, 'top': 0.1469}, 'timestamp': '2025-04-04T12:33:19.622048Z', 'track_id': '2799'}, {'bounding_box': {'bottom': 0.1672, 'left': 0.9374, 'right': 0.9544, 'top': 0.1547}, 'timestamp': '2025-04-04T12:33:19.622048Z', 'track_id': '2800'}, {'bounding_box': {'bottom': 0.3111, 'left': 0.2199, 'right': 0.3489, 'top': 0.1083}, 'class': {'lower_clothing_colors': [{'name': 'Blue', 'score': 0.12}], 'score': 0.18, 'type': 'Human', 'upper_clothing_colors': [{'name': 'White', 'score': 0.25}]}, 'geoposition': {'latitude': 58.3870632073232, 'longitude': 15.565143099610822}, 'timestamp': '2025-04-04T12:33:19.622048Z', 'track_id': '2801'}], 'operations': [], 'timestamp': '2025-04-04T12:33:19.622048Z'}}
            #print geoposition
            
            # Extract coordinates from the payload
            try:
                # Assuming the payload has a structure similar to the one in the example
                # {'frame': {'observations': [{'geoposition': {'latitude': ..., 'longitude': ...}}]}}
                coords = [1,
                payload["frame"]["observations"][0]["geoposition"]["latitude"],
                payload["frame"]["observations"][0]["geoposition"]["longitude"]
                ]
            except (KeyError, IndexError) as e:
                print(f"Error extracting coordinates: {e}")
                coords = None
            if coords:
                print(f"Coordinates: {coords}")
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