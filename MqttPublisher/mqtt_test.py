import paho.mqtt.client as mqtt

broker_host = "localhost"
broker_port = 1883
topic = "axis/frame_metadata"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(topic)

def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker_host, broker_port, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()