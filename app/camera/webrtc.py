import subprocess
import os
import logging
import json

logger = logging.getLogger(__name__)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_FILE = os.path.join(ROOT_DIR, "external", "RTSPtoWebRTC", "config.json")


def start_rtsp_to_webrtc():
    root_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    rtsp_dir = os.path.join(root_dir, "external", "RTSPtoWebRTC")

    # Command to run the Go program
    command = ["go", "run", rtsp_dir]

    try:
        # Start the server as a subprocess
        logger.info("Starting RTSPtoWebRTC server...")
        process = subprocess.Popen(
            command,
            cwd=rtsp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.info(
            "RTSPtoWebRTC server started successfully. Preview URL: http://localhost:8083"
        )

        for line in process.stdout:  # Read output line by line
            logger.info(line.strip())

        # Check for errors
        process.wait()  # Wait for the process to complete (optional, remove if you want it to run in background)
        if process.returncode not in (0, 1):
            error_output = process.stderr.read()
            logger.error(
                f"RTSPtoWebRTC server exited with error: {error_output.strip()}"
            )

    except subprocess.CalledProcessError as e:
        logger.error(f"Error starting RTSPtoWebRTC: {e}")
    except FileNotFoundError:
        logger.error(
            "RTSPtoWebRTC executable not found. Ensure Go is installed and the path is correct."
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping RTSPtoWebRTC server.")
    finally:
        if process:
            process.terminate()


def add_camera_to_config(
    cam_id, cam_ip, cam_username="student", cam_password="student_pass"
) -> None:
    """Add the camera dynamically to the config file."""

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        streams = config.get("streams", {})
        if cam_id not in streams:
            logger.info(f"Adding camera {cam_id} to config file")
            streams[cam_id] = {
                "on_demand": False,
                "disable_audio": True,
                "url": f"rtsp://{cam_username}:{cam_password}@{cam_ip}/axis-media/media.amp",
            }
            config["streams"] = streams
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
    else:
        logger.error("Config file not found")
        return


def clear_streams():
    """Clear all streams in the config file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        streams = config.get("streams", {})
        streams = {}
        config["streams"] = streams
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    else:
        logger.error("Config file not found")
        return


if __name__ == "__main__":
    start_rtsp_to_webrtc()
