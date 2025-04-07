import subprocess
import os


def start_rtsp_to_webrtc():
    # Define the path to the RTSPtoWebRTC directory relative to this script
    script_dir = os.path.dirname(
        os.path.abspath(__file__)
    )  # Directory of the Python script
    rtsp_dir = os.path.join(
        script_dir, "external", "RTSPtoWebRTC"
    )  # Path to RTSPtoWebRTC

    # Command to run the Go program
    command = ["go", "run", rtsp_dir]

    try:
        # Start the server as a subprocess
        process = subprocess.Popen(
            command,
            cwd=rtsp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print("RTSPtoWebRTC server starting...")

        for line in process.stdout:  # Read output line by line
            print(line.strip())

        # Check for errors
        # process.wait()  # Wait for the process to complete (optional, remove if you want it to run in background)
        if process.returncode != 0:
            error_output = process.stderr.read()
            raise RuntimeError(f"Failed to start RTSPtoWebRTC: {error_output}")

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print(
            "Error: 'go' command not found. Please ensure Go is installed and in your PATH."
        )


if __name__ == "__main__":
    start_rtsp_to_webrtc()
