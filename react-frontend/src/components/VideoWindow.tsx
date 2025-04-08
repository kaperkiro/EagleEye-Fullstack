// VideoWindow.tsx
import React, { useRef, useEffect } from "react";
import Hls from "hls.js";
import "../css/VideoWindow.css";

interface Props {
  rtspUrl: string;
}

const VideoWindow: React.FC<Props> = ({ rtspUrl }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  //const hlsUrl = rtspUrl.replace("rtsp://", "https://api.example.com/hls/"); med riktiga api requests
  const hlsUrl = "https://ireplay.tv/test/blender.m3u8";

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

  return (
    <div className="videoWindow">
      <video
        className="videoStream"
        ref={videoRef}
        width="100%"
        height="220"
        autoPlay
        muted
      />
    </div>
  );
};

export default VideoWindow;
