import json
import os
import subprocess
from ax_devil_device_api import Client, DeviceConfig
# Sets the cameras geocoords
# curl --digest -u student:student_pass --anyauth -X 'GET' http://192.168.0.93/axis-cgi/geolocation/set.cgi?lat=camera-latitude&lng=camera-longitude

# Sets the cameras installation height and heading
# curl --digest -u student:student_pass --anyauth -X 'GET' http://192.168.0.93/axis-cgi/geoorientation/geoorientation.cgi?action=set&inst_height=installation-height&heading=installation-heading

# Applys the camera settings
# curl --digest -u student:student_pass --anyauth -X 'GET' http://192.168.0.93/axis-cgi/geoorientation/geoorientation.cgi?action=set&auto_update_once=true




#TODO: use decimals instead of floats for better precision 

class Camera:
    """ Class to represent a camera and its configuration.
        Manual configuration with configure_camera() function for now. 
        
        Example usage: cam1 = Camera(...).configure_camera(...)
    """
    def __init__(
        self,
        id: str = "camera1",
        geocoords: tuple = (0, 0),
        ip: str = "192.168.0.93",
        config: DeviceConfig = None,
        ):
        self.id = id 
        self.ip = ip
        self.geocoords = geocoords
        self.config = DeviceConfig(self.ip, "student", "student_pass", verify_ssl=False) if config is None else config
        self._add_to_config() 
        
    #    self._set_cameras_geocoords() 
        
    def configure_camera(self, lat: float , lon :float, inst_height: float, heading: float, tilt: float = 0, roll: float = 0) -> None:
        """Configure the camera settings using curl commands."""
        with Client(self.config) as client:
            client.geocoordinates.set_location(
                lat,
                lon,
            )
            client.geocoordinates.set_orientation(
                {
                "heading" : heading,
                "tilt" : tilt,
                "roll" : roll,
                "installation_height" : inst_height,
                }
                
            )
            client.geocoordinates.apply_settings()

            self.geocoords = (lat, lon)
            print(f"Camera: ${self.id} configured successfully")

    def save_snapshot(self):
        """Save a snapshot from the camera."""
        assets_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(assets_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
        os.chdir(assets_dir)
        
        with Client(self.config) as client:
            snapshot = client.media.get_snapshot("1920x1080", 0, 0)
            if snapshot:
                with open(f"{self.id}_snapshot.jpg", "wb") as f:
                    f.write(snapshot)
                print(f"Snapshot saved as {self.id}_snapshot.jpg")
            else:
                print("Failed to save snapshot")
            
        
        
    def _add_to_config(self) -> None:
        """Add the camera dynamically to the config file."""
        config_file = "external/RTSPtoWebRTC/config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
                
            streams = config.get("streams", {})
            if self.id not in streams:
                print("Adding camera to config file")
                streams[self.id] = {
                    "on_demand": False,
                    "disable_audio": True,
                    "url": f"rtsp://student:student_pass@{self.ip}/axis-media/media.amp"
                }
                config["streams"] = streams
                with open(config_file, "w") as f:
                    json.dump(config, f, indent=4)
        else:
            print("Config file not found")
            return

    def _set_cameras_geocoords(self):
        """USE configure_camera() instead. Fetch geocoordinates from the camera using a curl command. """
        result = subprocess.run(
            f"curl --digest -u student:student_pass http://{self.ip}/axis-cgi/geolocation/get.cgi",
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("Curl command executed successfully")
        else:
            print("Failed to fetch geocoordinates")
            print("Error:", result.stderr)

        output = result.stdout
        test = output.splitlines()
        for line in test:
            if "Lat" in line:
                lat = line.split(">")[1].split("<")[0]
            if "Lng" in line:
                lng = line.split(">")[1].split("<")[0]
                self.geocoords = (lat, lng)

def clear_streams():
    """Clear all streams in the config file."""
    config_file = "external/RTSPtoWebRTC/config.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            
        streams = config.get("streams", {})
        streams = {}
        config["streams"] = streams
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
    else:
        print("Config file not found")
        return
    
    
        