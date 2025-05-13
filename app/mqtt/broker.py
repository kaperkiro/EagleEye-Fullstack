import socket
import subprocess


class BrokerManager:
    def __init__(
        self, host="localhost", port=1883, config_file="external/mosquitto.conf"
    ):
        self.host = host
        self.port = port
        self.config_file = config_file
        self.start()

    def is_running(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.connect((self.host, self.port))
                return True
            except (socket.timeout, ConnectionRefusedError):
                return False
            
    def stop(self) -> None:
        if self.is_running():
            print("Stopping Mosquitto broker...")
            subprocess.run(
                "pkill -f mosquitto", shell=True, check=True
            )
        else:
            print("Mosquitto is not running.")

    def start(self) -> None:
        if self.is_running():
            print("Mosquitto is already running.")
        else:
            subprocess.Popen(
                f"mosquitto -c {self.config_file}", shell=True
            )  # add -v flag to enable verbose logging
            # mosquitto -c {self.config.config_file} -v
