import React, { useState } from "react";
import VideoWindow from "./VideoWindow";
import "../css/LiveView.css";
import { FloorPlanWithObjects } from "./MapObj";

export const LiveViewData: React.FC = () => {
  // activeStreams maps an object ID to an array of camera stream IDs
  const [activeStreams, setActiveStreams] = useState<Record<number, string[]>>(
    {}
  );
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const handleDotClick = (id: number, cameraIds: string[]) => {
    setSelectedId((prevId) => {
      if (prevId === id) {
        // Deselect: clear all streams
        setActiveStreams({});
        return null;
      }
      // Select new object: show its camera streams
      setActiveStreams({ [id]: cameraIds });
      return id;
    });
  };

  return (
    <div className="liveViewDiv">
      <div className="liveLeftSidebar">
        {selectedId != null &&
          activeStreams[selectedId]?.map((streamId) => (
            <VideoWindow key={streamId} streamId={streamId} />
          ))}
      </div>
      <div className="liveMapDiv">
        <FloorPlanWithObjects
          selectedId={selectedId}
          onDotClick={handleDotClick}
        />
      </div>
    </div>
  );
};

export default LiveViewData;
