// src/map_obj.tsx
import React, { useState, useEffect } from "react";
import { useFloorPlan } from "./floorPlanProvider";
import { objHistoryMock } from "./MockData";
import "../css/MapObj.css";

interface FloorPlanWithObjectsProps {
  selectedId: number | null;
  onDotClick: (id: number, rtspUrls: string[]) => void;
}

interface MapObject {
  id: number; // Numeric track ID
  x: number; // Position in percent (0-100)
  y: number; // Position in percent (0-100)
  cId: number[]; // List of camera IDs seeing this object
}

// Fetch camera positions (static icons)
async function getCameras() {
  const response = await fetch(`http://localhost:5001/api/camera_positions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch camera positions: ${response.status}`);
  }
  return response.json();
}

export const FloorPlanWithObjects: React.FC<FloorPlanWithObjectsProps> = ({
  selectedId,
  onDotClick,
}) => {
  const [cameras, setCameras] = useState<
    Record<string, { x: number; y: number }>
  >({});
  const [objects, setObjects] = useState<MapObject[]>([]);
  const imageUrl = useFloorPlan();
  const cameraIcon = "src/assets/camera.png";

  interface ApiResponse {
    objects: Array<{ cid: number; x: number; y: number; id: number }>;
  }

  const fetchPositionData = async () => {
    try {
      const res = await fetch(`http://localhost:5001/api/objects`);
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(
          `Failed to fetch objects (${res.status}): ${
            errBody.message || res.statusText
          }`
        );
      }
      const { objects: obs }: ApiResponse = await res.json();

      const mapped: MapObject[] = obs.map((o) => ({
        id: o.id,
        x: o.x,
        y: o.y,
        cId: [o.cid],
      }));

      setObjects(mapped);
    } catch (err) {
      console.error("fetchPositionData error:", err);
    }
  };

  const pollCameras = async () => {
    try {
      const data = await getCameras();
      setCameras(data);
    } catch (err) {
      console.error("Failed to poll cameras:", err);
    }
  };

  useEffect(() => {
    pollCameras();
    fetchPositionData();
    const interval = setInterval(fetchPositionData, 100);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="ObjmapDiv">
      <img
        src={imageUrl}
        alt="Floor Plan"
        style={{ width: "100%", height: "100%", zIndex: 0 }}
      />

      {/* Camera icons */}
      {Object.entries(cameras).map(([id, coords]) => (
        <img
          key={id}
          src={cameraIcon}
          alt={`camera ${id}`}
          style={{
            position: "absolute",
            top: `${coords.y}%`,
            left: `${coords.x}%`,
            width: "4%",
            height: "6%",
            zIndex: 1,
            borderRadius: "35px",
            border: "solid 2px black",
          }}
        />
      ))}

      {/* Moving objects */}
      {objects.map((obj) => {
        const isSelected = obj.id === selectedId;
        return (
          <button
            className="mapButton"
            key={obj.id}
            onClick={() => {
              const urls = obj.cId.map((id) => id.toString());
              onDotClick(obj.id, urls);
            }}
            style={{
              left: `${obj.x}%`,
              top: `${obj.y}%`,
              backgroundColor: isSelected ? "yellow" : "#3B82F6",
              zIndex: 2,
            }}
          />
        );
      })}

      {/* History line for selected object */}
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
