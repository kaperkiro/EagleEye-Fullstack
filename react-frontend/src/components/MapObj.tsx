// src/map_obj.tsx
import React, { useState, useEffect } from "react";
import FloorPlan from "../assets/floor_plan.jpg";
import { mock_obj_data } from "./MockData";
import { objHistoryMock } from "./MockData";
import "../css/MapObj.css";

interface FloorPlanWithObjectsProps {
  selectedId: number | null;
  onDotClick: (id: number, rtspUrls: string[]) => void;
}

export async function getStreamUrls(id: number): Promise<string[]> {
  let urls: string[] = [];
  // Later, replace this with an API call to retrieve URLs for the given button.
  if (id === 1) {
    urls = [`rtsp://camera/${id}/1`];
  }
  if (id === 2) {
    urls = [`rtsp://camera/${id}/1`, `rtsp://camera/${id}/2`];
  }
  if (id === 3) {
    urls = [
      `rtsp://camera/${id}/1`,
      `rtsp://camera/${id}/2`,
      `rtsp://camera/${id}/3`,
    ];
  }
  return urls;
}

export const FloorPlanWithObjects: React.FC<FloorPlanWithObjectsProps> = ({
  selectedId,
  onDotClick,
}) => {
  // Use state to store the object data
  const [objects, setObjects] = useState(mock_obj_data.objects);

  useEffect(() => {
    // Poll for new object data every 500ms.
    const interval = setInterval(() => {
      // Replace this line with your API call when ready.
      setObjects(mock_obj_data.objects);
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mapDiv">
      <img
        src={FloorPlan}
        alt="Floor Plan"
        style={{ width: "100%", height: "100%" }}
      />
      {objects.map((obj) => {
        const isSelected = obj.id === selectedId;
        return (
          <button
            className="mapButton"
            key={obj.id}
            onClick={() =>
              getStreamUrls(obj.id).then((urls) => onDotClick(obj.id, urls))
            }
            style={{
              // leave variable styling in component for now
              left: `${obj.x}%`,
              top: `${obj.y}%`,
              backgroundColor: isSelected ? "yellow" : "#3B82F6",
            }}
          />
        );
      })}
      {/* Draw blue, dotted, smoothed history line when selected */}
      {selectedId !== null && objHistoryMock(selectedId).history.length > 0 && (
        <svg
          className="blueDots"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          <path
            d={objHistoryMock(selectedId)
              .history.map((p, i) =>
                i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`
              )
              .join(" ")}
            fill="none"
            stroke="#3B82F6"
            strokeWidth={1}
            strokeDasharray="1 1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </div>
  );
};
