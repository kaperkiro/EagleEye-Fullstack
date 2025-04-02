import paho.mqtt.client as mqtt
import json
import time

broker_host = "localhost"
broker_port = 1883
topic = "axis/frame_metadata"

def publish_dummy_data(client):
    dummy_payload = {
       # "frame": {
            "observations": [
                {
                    "bounding_box": {
                        "bottom": 0.6157,
                        "left": 0.4778,
                        "right": 0.5588,
                        "top": 0.3986
                    },
                    "class": {
                        "lower_clothing_colors": [
                            {"name": "Black", "score": 0.6}
                        ],
                        "score": 0.92,
                        "type": "Human",
                        "upper_clothing_colors": [
                            {"name": "Gray", "score": 0.71}
                        ]
                    },
                    "geoposition": {
                        "latitude": 58.387021008804375,
                        "longitude": 15.565212926847485
                    },
                    "timestamp": "2025-04-02T08:18:12.678869Z",
                    "track_id": "29"
                }
            ],
            "operations": [],
            "timestamp": "2025-04-02T08:18:12.678869Z"
        }
  #  }
    client.publish(topic, json.dumps(dummy_payload), qos=0)
    print(f"Published: {json.dumps(dummy_payload)} ")

def main():
    client = mqtt.Client()
    client.connect(broker_host, broker_port, 60)
    client.loop_start()
    try:
        while True:
            publish_dummy_data(client)
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping dummy publisher.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()