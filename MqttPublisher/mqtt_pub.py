import paho.mqtt.client as mqtt
import json
import time

broker_host = "localhost"
broker_port = 1883
topic = "axis/frame_metadata"

def publish_dummy_data(client):
    dummy_payload = {
        "frame": {
            "observations": [
                {
                    "bounding_box": {"left": 0.1, "top": 0.1, "right": 0.3, "bottom": 0.3},
                    "class": {"type": "Human", "score": 0.95}
                },
                {
                    "bounding_box": {"left": 0.5, "top": 0.5, "right": 0.7, "bottom": 0.7},
                    "class": {"type": "Car", "score": 0.88}
                }
            ]
        }
    }
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