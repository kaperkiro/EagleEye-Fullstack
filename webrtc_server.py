import cv2
import base64
import asyncio
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

app = FastAPI()

RTSP_URL = "rtsp://student:student_pass@192.168.0.93/axis-media/media.amp"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("Client attempting to connect...")
    await websocket.accept()
    print("Client connected!")
    
    while True:
        cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            print(f"❌ ERROR: Cannot open RTSP stream at {RTSP_URL}")
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text("Stream unavailable, retrying...")
            await asyncio.sleep(2)
            continue

        try:
            while websocket.client_state == WebSocketState.CONNECTED:
                ret, frame = cap.read()
                if not ret:
                    print("❌ No frame received, reconnecting...")
                    break
                # frame = cv2.resize(frame, (640, 360))
                _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70]) # Adjust quality as needed
                await websocket.send_bytes(buffer.tobytes())
                await asyncio.sleep(0.033)
        except WebSocketDisconnect:
            print("Client disconnected")
            break  # Exit if client disconnects
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        finally:
            cap.release()
            await asyncio.sleep(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)