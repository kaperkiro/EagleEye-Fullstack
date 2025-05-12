// src/map_obj.tsx
import React, { useState, useEffect } from "react";
//import FloorPlan from "../assets/floor_plan.jpg";
import { useFloorPlan } from "./floorPlanProvider";
import { mock_obj_data } from "./MockData";
import { objHistoryMock } from "./MockData";
import "../css/MapObj.css";

interface FloorPlanWithObjectsProps {
  selectedId: number | null;
  onDotClick: (id: number, rtspUrls: string[]) => void;
}

interface ApiResponse {
  camera_id: number;
  detections: BackendDetection[];
  position: number[];
}

interface BackendDetection {
  bounding_box: {
    /* ... */
  }; // Behåll om relevant
  class: {
    /* ... */
  }; // Behåll om relevant
  timestamp: string;
  track_id: string; // ID från MQTT
}

// Typ för objekt som komponenten använder internt för rendering
interface MapObject {
  id: number; // Använder numeriskt ID internt, från track_id
  x: number; // Position i procent (0-100)
  y: number; // Position i procent (0-100)
  cId: number[];
  // Lägg till andra fält från BackendDetection om de behövs för rendering
}

export async function getStreamUrls(objectId: number): Promise<string[]> {
  const obj = mock_obj_data.objects.find((o) => o.id === objectId);
  if (!obj) return [];
  // Convert each camera ID to string for the streamId prop
  return obj.cId.map((id) => id.toString());
}

async function getCameras() {
  const response = await fetch(`http://localhost:5001/api/camera_positions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch camera positions: ${response.status}`);
  }
  const data = await response.json();
  return data;
}

export const FloorPlanWithObjects: React.FC<FloorPlanWithObjectsProps> = ({
  selectedId,
  onDotClick,
}) => {
  // Use state to store the object data
  const [cameras, setCameras] = useState<
    Record<string, { x: number; y: number }>
  >({});
  const [objects, setObjects] = useState(mock_obj_data.objects);
  const imageUrl = useFloorPlan(); // Get the pre-fetched image URL

  //camera image jpg:
  const camerIcon = "src/assets/camera.png";

  //Real object
  //const [objects, setObjects] = useState<MapObject[]>([]);

  //kanske borde ändra s.a fetchPositionData in är nästlad
  const fetchPositionData = async (cameraId: number) => {
    try {
      const response = await fetch(
        `http://localhost:5001/api/detections/${cameraId}/all`
      );
      if (!response.ok) {
        let errorMsg = `HTTP error! status: ${response.status} ${response.statusText}`;
        try {
          const errorBody = await response.json();
          errorMsg += `: ${errorBody.message || JSON.stringify(errorBody)}`;
        } catch (e) {
          /* Ignorera om body inte är JSON */
        }
        throw new Error(errorMsg);
      }
      const data: ApiResponse = await response.json();
      console.log(data);

      // Assuming data.position is now an array of position objects:
      // e.g., [{ id: number, x: number, y: number, camera_id: number }, ...]
      const mappedObjects: MapObject[] = Array.isArray(data.position)
        ? data.position.map((pos: any) => ({
            // Use either pos.id or pos.camera_id here according to what the API sends
            id: pos.camera_id,
            x: pos.x,
            y: pos.y,
            cId: [],
          }))
        : [];
      setObjects(mappedObjects);
    } catch (err) {
      console.error("Failed to fetch position data:", err);
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

  //fetch camera pos once before interval
  useEffect(() => {
    // on mount, fetch camera positions a single time
    pollCameras();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      // Replace this line with your API call when ready.
      //API call:
      //fetchPositionData(1);
      // remove this and uncomment fetchPositionData(1) for API call
      setObjects(mock_obj_data.objects);
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="ObjmapDiv">
      <img
        src={imageUrl}
        alt="Floor Plan"
        style={{ width: "100%", height: "100%", zIndex: 0 }}
      />
      {Object.entries(cameras).map(([id, coords]) => (
        <img
          key={id}
          src={camerIcon}
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
              zIndex: 2,
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
