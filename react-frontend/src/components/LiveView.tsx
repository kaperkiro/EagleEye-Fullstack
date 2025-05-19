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
        <h1 className="liveLeftSidebarTitle">Video streams</h1>
        {selectedId != null &&
          activeStreams[selectedId]?.map((streamId) => (
            <VideoWindow key={streamId} streamId={streamId} />
          ))}
        {Object.keys(activeStreams).length === 0 && 
        (<p className="liveLeftAltText">No streams selected! Please select a camera or observation...</p>)}
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
