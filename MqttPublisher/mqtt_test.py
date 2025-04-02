import paho.mqtt.client as mqtt
import json
import time

broker_host = "localhost"
broker_port = 1883
topic = "axis/frame_metadata"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(topic)
def get_coords(decoded_msg):
    try:
        data = json.loads(decoded_msg)
        coords = {
            "latitude": data["observations"][0]["geoposition"]["latitude"],
            "longitude": data["observations"][0]["geoposition"]["longitude"]
        }
        return coords
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error extracting coordinates: {e}")
        return None

def on_message(client, userdata, msg):

    coords = get_coords(msg.payload.decode())
    if coords:
        print(f"Coordinates: {coords}")
    else:
        print("No coordinates found.")


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker_host, broker_port, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()