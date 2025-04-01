import { FloorPlanWithObjects } from "./MapObj";
import React, { useState } from "react";
import VideoWindow from "./VideoWindow";

export const LiveViewData = () => {
  const [activeStreams, setActiveStreams] = useState<Record<number, string[]>>(
    {}
  );
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const handleDotClick = (id: number, urls: string[]) => {
    setSelectedId((prevId) => {
      if (prevId === id) {
        // Deselect: clear that key
        setActiveStreams({});
        return null;
      }
      // Switch selection: clear old streams and set new ones
      setActiveStreams({ [id]: urls });
      return id;
    });
  };

  return (
    <div
      style={{
        display: "flex",
        flex: 1,
        flexDirection: "row",
      }}
    >
      <div
        className="leftSidebar"
        style={{
          borderRight: "solid",
          width: "25%",
        }}
      >
        {selectedId != null &&
          activeStreams[selectedId]?.map((url) => (
            <VideoWindow key={url} rtspUrl={url} />
          ))}
      </div>
      <div
        className="mapDiv"
        style={{
          width: "75%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <FloorPlanWithObjects
          selectedId={selectedId}
          onDotClick={handleDotClick}
        />
      </div>
    </div>
  );
};

export default LiveViewData;
