import paho.mqtt.client as mqtt
import json
import time


class MqttPublisher:
    def __init__(
        self,
        broker_host="localhost",
        broker_port=1883,
        topic="axis/frame_metadata",
        publish_interval=0.5,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.publish_interval = publish_interval
        self.client = mqtt.Client()
        self.current_coords = [59.3245, 18.0705]

    def connect(self):
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish_dummy_data(self):
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
                            "latitude": self.current_coords[0],
                            "longitude": self.current_coords[1],
                        },
                        "timestamp": "2025-04-02T08:18:12.678869Z",
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
                            "latitude": self.current_coords[0] + 0.001,
                            "longitude": self.current_coords[1] - 0.001,
                        },
                        "timestamp": "2025-04-02T08:18:12.678869Z",
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
                            "latitude": self.current_coords[0] - 0.001,
                            "longitude": self.current_coords[1] + 0.001,
                        },
                        "timestamp": "2025-04-02T08:18:12.678869Z",
                        "track_id": "31",
                    },
                ],
                "operations": [],
                "timestamp": "2025-04-02T08:18:12.678869Z",
            }
        }
        payload_str = json.dumps(dummy_payload)
        self.client.publish(self.topic, payload_str, qos=0)
        print(f"Published: {payload_str}")

    def run(self):
        self.connect()
        dividor = 0
        count = 0
        try:
            while True:
                self.publish_dummy_data()
                dividor += 1
                if dividor % 10 == 0:
                    count += 1
                    dividor = 0
                    if count == 4:
                        count = 0

                self.cycle_coords(count)

                time.sleep(self.publish_interval)
        except KeyboardInterrupt:
            print("Stopping dummy publisher.")
        finally:
            self.disconnect()

    def cycle_coords(self, count):
        coords = [
            (59.3250, 18.0700),
            (59.3240, 18.0700),
            (59.3250, 18.0710),
            (59.3240, 18.0710),
        ]
        print("count", count)
        # Take incremental steps towards the next coordinate

        if count < len(coords):
            self.current_coords[0] += (coords[count][0] - self.current_coords[0]) / 10
            self.current_coords[1] += (coords[count][1] - self.current_coords[1]) / 10


if __name__ == "__main__":
    publisher = MqttPublisher()
    publisher.run()
