import { useEffect, useRef, useState } from "react";
import "../css/VideoWindow.css";

interface WebRTCStreamProps {
  streamId: string;
}

/**
 * Component that connects to a WebRTC-enabled RTSP stream via a signaling server,
 * renders the incoming video tracks in a <video> element, and allows fullscreen toggling.
 *
 * Workflow:
 * 1. Create RTCPeerConnection with a STUN server.
 * 2. Fetch codec information and add appropriate transceivers.
 * 3. Create and send an SDP offer, then set the remote SDP answer.
 * 4. Handle incoming tracks and ICE connection state changes.
 *
 * Clicking the video container toggles fullscreen mode.
 *
 * @param streamId - Identifier of the desired stream to connect to.
 */
const WebRTCStream: React.FC<WebRTCStreamProps> = ({ streamId }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const [status, setStatus] = useState<string>("Connecting...");
  const [active, setActive] = useState(false);

  /**
   * Effect to set up the WebRTC connection on mount and clean up on unmount.
   */
  useEffect(() => {
    const baseUrl = "http://localhost:8083/stream";

    const pc = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });
    pcRef.current = pc;

    const stream = new MediaStream();
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
    }

    /**
     * Handler for when a new media track arrives.
     * Adds the track to the MediaStream and updates status.
     */
    pc.ontrack = (event) => {
      console.log("Video track received");
      stream.addTrack(event.track);
      setStatus("Streaming");
    };

    /**
     * Handler for ICE connection state changes.
     * Clears status on connected, otherwise displays the ICE state.
     */
    pc.oniceconnectionstatechange = () => {
      console.log("ICE state:", pc.iceConnectionState);
      if (pc.iceConnectionState === "connected") {
        setStatus("");
      } else {
        setStatus(pc.iceConnectionState);
      }
    };

    /**
     * Fetch supported codecs from the server and add recvonly transceivers.
     */
    const getCodecInfo = async () => {
      try {
        const response = await fetch(`${baseUrl}/codec/${streamId}`);
        if (!response.ok)
          throw new Error(`Codec fetch failed: ${response.status}`);
        const data: { Type: string }[] = await response.json();
        if (pcRef.current?.signalingState !== "closed") {
          data.forEach((codec) => {
            pc.addTransceiver(codec.Type, { direction: "recvonly" });
          });
          console.log("Codec info loaded:", data);
        }
      } catch (e) {
        console.error("Error fetching codec info:", e);
        setStatus("Failed to load codec info");
      }
    };

    /**
     * Create and send an SDP offer, then set the remote SDP answer
     * to finalize the WebRTC connection.
     */
    const negotiate = async () => {
      try {
        if (pcRef.current?.signalingState === "closed") {
          throw new Error("RTCPeerConnection is closed");
        }
        console.log("Starting negotiation");
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        console.log("Sending SDP offer:", offer.sdp);

        const response = await fetch(`${baseUrl}/receiver/${streamId}`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({
            suuid: streamId,
            data: btoa(offer.sdp || ""),
          }).toString(),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `Server responded with ${response.status}: ${errorText}`
          );
        }

        const answerSdp = await response.text();
        console.log("Raw server response:", answerSdp);
        if (!answerSdp) throw new Error("Empty SDP answer received");

        const answer: RTCSessionDescriptionInit = {
          type: "answer",
          sdp: atob(answerSdp),
        };
        console.log("Decoded SDP answer:", answer.sdp);
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
      } catch (e) {
        console.error("Negotiation failed:", e);
        setStatus(`Negotiation failed: ${e}`);
      }
    };

    /**
     * Orchestrates fetching codec info and negotiating the connection.
     */
    const start = async () => {
      await getCodecInfo();
      await negotiate();
    };

    start();
    // Cleanup on unmount: close the connection if still open
    return () => {
      if (pcRef.current && pcRef.current.signalingState !== "closed") {
        pcRef.current.close();
      }
    };
  }, [streamId]);

  /**
   * Toggle fullscreen mode for the video container and update state.
   */
  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current
        ?.requestFullscreen()
        .then(() => setActive(true))
        .catch((err) => console.error("Error enabling fullscreen:", err));
    } else {
      document
        .exitFullscreen()
        .then(() => setActive(false))
        .catch((err) => console.error("Error exiting fullscreen:", err));
    }
  };

  /**
   * Keeps `active` state in sync when exiting fullscreen via ESC or other means.
   */
  useEffect(() => {
    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        setActive(false);
      }
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () =>
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  return (
    <div
      ref={containerRef}
      onClick={toggleFullScreen}
      className={`videoContainer ${active ? "active" : ""}`}
      style={{ textAlign: "center", padding: "5px", cursor: "pointer" }}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`videoStream ${active ? "active" : ""}`}
        style={{ maxWidth: "100%", maxHeight: "100%" }}
      />
      <div>{status}</div>
    </div>
  );
};

export default WebRTCStream;
