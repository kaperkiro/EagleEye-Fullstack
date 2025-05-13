import subprocess
import os
import logging

logger = logging.getLogger(__name__)

def start_rtsp_to_webrtc():
    # Locate the project root directory (three levels up) and external folder
    root_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    rtsp_dir = os.path.join(
        root_dir, "external", "RTSPtoWebRTC"
    )  # Path to RTSPtoWebRTC

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
        logger.info("RTSPtoWebRTC server started successfully. Preview URL: http://localhost:8083")

        for line in process.stdout:  # Read output line by line
            print(line.strip())

        # Check for errors
        process.wait()  # Wait for the process to complete (optional, remove if you want it to run in background)
        if process.returncode not in (0, 1):
            error_output = process.stderr.read()
            logger.error(f"RTSPtoWebRTC server exited with error: {error_output.strip()}") 

    except subprocess.CalledProcessError as e:
        logger.error(f"Error starting RTSPtoWebRTC: {e}")
    except FileNotFoundError:
        logger.error("RTSPtoWebRTC executable not found. Ensure Go is installed and the path is correct.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping RTSPtoWebRTC server.")
    finally:
        if process:
            process.terminate()


if __name__ == "__main__":
    start_rtsp_to_webrtc()
