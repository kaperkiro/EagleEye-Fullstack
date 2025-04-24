import paho.mqtt.client as mqtt
import json
import time
import random


class MqttPublisher:
    def __init__(
        self,
        broker_host="localhost",
        broker_port=1883,
        topic="axis/frame_metadata",
        publish_interval=0.5,
        camera_id=1,
    ):
        self.camera_id = camera_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = f"axis/{camera_id}/frame_metadata"
        self.publish_interval = publish_interval
        self.client = mqtt.Client()
        # maintain independent geopositions per track
        self.coords = {
            "29": [59.3245, 18.0705],
            "30": [59.3245 - 0.00001, 18.0705 + 0.00001],
            "31": [59.3245 + 0.00001, 18.0705 - 0.00001],
        }

    def connect(self):
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish_dummy_data(self):
        # update each track's position independently
        for tid, pos in self.coords.items():
            pos[0] += random.uniform(-0.0001, 0.0001)
            pos[1] += random.uniform(-0.0001, 0.0001)

        dummy_payload = {
            "frame": {
                "observations": [
                    {
                        "bounding_box": {
                            "bottom": 0.6157,
                            "left": 0.4778,
                            "right": 0.5588,
                            "top": 0.3986,
                        },
                        "class": {
                            "lower_clothing_colors": [{"name": "Black", "score": 0.6}],
                            "score": 0.92,
                            "type": "Human",
                            "upper_clothing_colors": [{"name": "Gray", "score": 0.71}],
                        },
                        "geoposition": {
                            "latitude": self.coords["29"][0],
                            "longitude": self.coords["29"][1],
                        },
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "track_id": "29",
                    },
                    {
                        "bounding_box": {
                            "bottom": 0.7257,
                            "left": 0.3778,
                            "right": 0.4588,
                            "top": 0.2986,
                        },
                        "class": {
                            "lower_clothing_colors": [{"name": "Blue", "score": 0.8}],
                            "score": 0.88,
                            "type": "Vehicle",
                            "upper_clothing_colors": [{"name": "White", "score": 0.75}],
                        },
                        "geoposition": {
                            "latitude": self.coords["30"][0],
                            "longitude": self.coords["30"][1],
                        },
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "track_id": "30",
                    },
                    {
                        "bounding_box": {
                            "bottom": 0.5157,
                            "left": 0.5778,
                            "right": 0.6388,
                            "top": 0.4986,
                        },
                        "class": {
                            "lower_clothing_colors": [{"name": "Red", "score": 0.7}],
                            "score": 0.95,
                            "type": "Animal",
                            "upper_clothing_colors": [{"name": "Brown", "score": 0.65}],
                        },
                        "geoposition": {
                            "latitude": self.coords["31"][0],
                            "longitude": self.coords["31"][1],
                        },
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "track_id": "31",
                    },
                ],
                "operations": [],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        }
        payload_str = json.dumps(dummy_payload)
        self.client.publish(self.topic, payload_str, qos=0)

    def run(self):
        self.connect()
        try:
            while True:
                self.publish_dummy_data()
                time.sleep(self.publish_interval)
        except KeyboardInterrupt:
            print("Stopping dummy publisher.")
        finally:
            self.disconnect()


if __name__ == "__main__":
    publisher = MqttPublisher()
    publisher.run()
