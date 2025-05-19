import React, { useState, useEffect } from "react";
import { useFloorPlan } from "./FloorPlanProvider";
import "../css/MapObj.css";
import cameraIcon from "../assets/camera.png"; // Ensure correct path

interface FloorPlanWithObjectsProps {
  selectedId: number | null;
  onDotClick: (id: number, rtspUrls: string[]) => void;
}

interface MapObject {
  id: number;
  x: number;
  y: number;
  cId: number[];
}

interface Camera {
  x: number;
  y: number;
  heading: number; // Heading in degrees
}

async function getCameras() {
  try {
    const response = await fetch(`http://localhost:5001/api/camera_positions`);
    if (!response.ok) {
      throw new Error(`Failed to fetch camera positions: ${response.status}`);
    }
    const data = await response.json();
    console.log("Camera positions data:", data);
    return data;
  } catch (error) {
    console.error("Error fetching camera positions:", error);
    return {};
  }
}

export const FloorPlanWithObjects: React.FC<FloorPlanWithObjectsProps> = ({
  selectedId,
  onDotClick,
}) => {
  const [cameras, setCameras] = useState<Record<string, Camera>>({});
  const [objects, setObjects] = useState<MapObject[]>([]);
  const imageUrl = useFloorPlan();

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
        x: Math.min(Math.max(o.x, 0), 100),
        y: Math.min(Math.max(o.y, 0), 100),
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
    const interval = setInterval(fetchPositionData, 300);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    console.log("Cameras state:", cameras);
    console.log("Floor plan imageUrl:", imageUrl);
  }, [cameras, imageUrl]);

  // Calculate POV cone points (isosceles triangle)
  const getConePoints = (x: number, y: number, heading: number) => {
    const radius = 20; // Cone length in % (adjust as needed)
    const fov = 90; // Field of view in degrees
    const halfFov = fov / 2;

    // Convert heading to radians, adjust for SVG (0° = right, 90° = up)
    const rad = (heading * Math.PI) / 180;
    const centerX = x;
    const centerY = y;

    // Cone apex (camera position)
    const p1 = { x: centerX, y: centerY };

    // Two points at the cone's base
    const p2 = {
      x: centerX + radius * Math.cos(rad - (halfFov * Math.PI) / 180),
      y: centerY + radius * Math.sin(rad - (halfFov * Math.PI) / 180),
    };
    const p3 = {
      x: centerX + radius * Math.cos(rad + (halfFov * Math.PI) / 180),
      y: centerY + radius * Math.sin(rad + (halfFov * Math.PI) / 180),
    };

    return `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y}`;
  };

  return (
    <div className="ObjmapDiv">
      {imageUrl ? (
        <img
          src={imageUrl}
          alt="Floor Plan"
          style={{ width: "100%", height: "100%", zIndex: 0 }}
        />
      ) : (
        <div
          style={{
            width: "100%",
            height: "100%",
            background: "#eee",
            zIndex: 0,
          }}
        />
      )}
      {/* POV cones and camera icons */}
      <svg
        className="cameraCones"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          zIndex: 1,
        }}
      >
        {Object.entries(cameras).map(([id, coords]) => (
          <polygon
            key={`cone-${id}`}
            points={getConePoints(coords.x, coords.y, coords.heading - 90 || 0)}
            fill="rgba(0, 128, 255, 0.2)"
            stroke="rgba(0, 128, 255, 0.3)"
            strokeWidth={0.15}
          />
        ))}
      </svg>
      {Object.entries(cameras).map(([id, coords]) => (
        <img
          key={id}
          src={cameraIcon}
          alt={`camera ${id}`}
          className="cameraIcon"
          onClick={() => onDotClick(parseInt(id, 10), [id])}
          style={{
            top: `${coords.y}%`,
            left: `${coords.x}%`,
            width: "4%",
            height: "4%",
            marginTop: "-2%",
            marginLeft: "-2.2%",
            cursor: "pointer",
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
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </div>
  );
};
