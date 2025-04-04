import { useEffect, useRef, useState } from "react";

const WebRTCStream: React.FC = () => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const pcRef = useRef<RTCPeerConnection | null>(null);
    const [status, setStatus] = useState<string>("Connecting...");

    useEffect(() => {
        const streamId = "camera1";
        const baseUrl = "http://localhost:8083/stream";

        const pc = new RTCPeerConnection({
            iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
        });
        pcRef.current = pc;

        const stream = new MediaStream();
        if (videoRef.current) {
            videoRef.current.srcObject = stream;
        }

        pc.ontrack = (event) => {
            console.log("Video track received");
            stream.addTrack(event.track);
            setStatus("Streaming");
        };

        pc.oniceconnectionstatechange = () => {
            console.log("ICE state:", pc.iceConnectionState);
            setStatus(pc.iceConnectionState);
        };

        const getCodecInfo = async () => {
            try {
                const response = await fetch(`${baseUrl}/codec/${streamId}`);
                if (!response.ok) throw new Error(`Codec fetch failed: ${response.status}`);
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
                    throw new Error(`Server responded with ${response.status}: ${errorText}`);
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

        const start = async () => {
            await getCodecInfo();
            await negotiate();
        };

        start();

        return () => {
            if (pcRef.current && pcRef.current.signalingState !== "closed") {
                pcRef.current.close();
            }
        };
    }, []);

    return (
        <div style={{ textAlign: "center", padding: "5px" }}>
            <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ maxWidth: "100%", maxHeight: "100%" }}
            />
        </div>
    );
};

export default WebRTCStream;