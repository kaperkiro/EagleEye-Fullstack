import React, { useState } from "react";
import VideoWindow from "./VideoWindow";
import "../css/LiveView.css";
import { FloorPlanWithObjects } from "./MapObj";

/**
 * Component managing live video streams overlayed on a floor plan with selectable objects.
 * Maintains selected object state and displays associated camera streams in VideoWindow components.
 */
export const LiveViewData: React.FC = () => {
  /**
   * Maps an object ID to its active camera stream IDs.
   * @example { 1: ["camA", "camB"] }
   */
  const [activeStreams, setActiveStreams] = useState<Record<number, string[]>>(
    {}
  );
  /**
   * Currently selected object ID, or null if none.
   */
  const [selectedId, setSelectedId] = useState<number | null>(null);

  /**
   * Handles clicking on a map object dot. Toggles selection and updates active streams.
   * @param id - ID of the clicked object
   * @param cameraIds - List of camera stream IDs associated with the object
   */
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
        {Object.keys(activeStreams).length === 0 && (
          <p className="liveLeftAltText">
            No streams selected! Please select a camera or observation...
          </p>
        )}
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
