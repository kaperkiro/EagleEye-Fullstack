import subprocess
import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# Configuration
RTSP_URL = "rtsp://student:student_pass@192.168.0.93/axis-media/media.amp"
HLS_OUTPUT_DIR = os.path.abspath("hls")  # Absolute path to avoid relative path issues
HLS_OUTPUT_PATH = os.path.join(HLS_OUTPUT_DIR, "stream.m3u8")
PORT = 8000

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow all origins
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        super().end_headers()

# Ensure the HLS output directory exists
if not os.path.exists(HLS_OUTPUT_DIR):
    os.makedirs(HLS_OUTPUT_DIR)

def start_ffmpeg():
    print("Starting FFmpeg...")
    ffmpeg_cmd = [
    "ffmpeg",
    "-rtsp_transport", "tcp",
    "-i", RTSP_URL,
    "-f", "hls",
    "-hls_time", "2",           # Target segment duration
    "-hls_segment_type", "mpegts",  # Force MPEG-TS segments
    "-hls_list_size", "4",
    "-hls_flags", "delete_segments",
    "-c:v", "copy",
    "-c:a", "aac",
    "-hls_playlist_type", "event",  # Optional: for live streaming
    HLS_OUTPUT_PATH
    ]
    try:
        process = subprocess.Popen(ffmpeg_cmd, stderr=subprocess.PIPE, text=True)
        for line in iter(process.stderr.readline, ''):
            print(f"FFmpeg: {line.strip()}")
        process.wait()
        if process.returncode != 0:
            print(f"FFmpeg exited with code {process.returncode}")
    except Exception as e:
        print(f"FFmpeg failed to start: {e}")

def start_server():
    print("Starting HTTP server with CORS support...")
    os.chdir(HLS_OUTPUT_DIR)
    with TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"Serving HLS at http://localhost:{PORT}/stream.m3u8")
        httpd.serve_forever()

if __name__ == "__main__":
    # Start FFmpeg in a separate thread
    ffmpeg_thread = threading.Thread(target=start_ffmpeg)
    ffmpeg_thread.start()

    # Start the HTTP server in the main thread
    start_server()