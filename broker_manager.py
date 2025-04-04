import socket
import subprocess

class BrokerConfig:
    def __init__(self, host="localhost", port=1883, config_file="external/mosquitto.conf"):
        self.host = host
        self.port = port
        self.config_file = config_file

class BrokerManager:
    def __init__(self, config: BrokerConfig):
        self.config = config
    
    def is_running(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.connect((self.config.host, self.config.port))
                return True
            except (socket.timeout, ConnectionRefusedError):
                return False
    
    def start(self) -> None:
        if self.is_running():
            print("Mosquitto is already running.")
        else:
            print("Starting Mosquitto broker...")
            subprocess.Popen(f"mosquitto -c {self.config.config_file}", shell=True)  # add -v flag to enable verbose logging 
                                                                                        # mosquitto -c {self.config.config_file} -v