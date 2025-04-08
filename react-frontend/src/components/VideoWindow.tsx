import React, { useRef, useEffect, useState } from "react";
import Hls from "hls.js";
import "../css/VideoWindow.css";

interface Props {
  rtspUrl: string;
}

const VideoWindow: React.FC<Props> = ({ rtspUrl }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const hlsUrl =
    "http://playertest.longtailvideo.com/adaptive/wowzaid3/playlist.m3u8";
  const [active, setActive] = useState(false);

  useEffect(() => {
    if (Hls.isSupported() && videoRef.current) {
      const hls = new Hls();
      hls.loadSource(hlsUrl);
      hls.attachMedia(videoRef.current);
      return () => {
        hls.destroy();
      };
    }
  }, [hlsUrl]);

  // Toggle fullscreen and update active state.
  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current
        ?.requestFullscreen()
        .then(() => setActive(true))
        .catch((err) => console.error("Error enabling fullscreen mode:", err));
    } else {
      document
        .exitFullscreen()
        .then(() => setActive(false))
        .catch((err) => console.error("Error exiting fullscreen mode:", err));
    }
  };

  // Listen for fullscreen changes to update the active state.
  useEffect(() => {
    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        setActive(false);
      }
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  return (
    <div
      className={`videoWindow ${active ? "active" : ""}`}
      ref={containerRef}
      onClick={toggleFullScreen}
      style={{ cursor: "pointer" }}
    >
      <video
        className={`videoStream ${active ? "active" : ""}`}
        ref={videoRef}
        autoPlay
        muted
      />
    </div>
  );
};

export default VideoWindow;
