import React, { useState, useEffect } from "react";
import { useFloorPlan } from "./floorPlanProvider.tsx";
import "../css/AlarmObj.css";

/**
 * Displays the static floorplan image with buttons representing objects seen by cameras.
 *Position of objects are depending on the geological positions of the map and objects.
 *
 */

interface MapObject {
  id: number; // Numeric track ID
  x: number; // Position in percent (0-100)
  y: number; // Position in percent (0-100)
  cId: number[]; // List of camera IDs seeing this object
}

export const FloorPlanStaticObjects: React.FC = () => {
  // State for mock object positions
  const [objects, setObjects] = useState<MapObject[]>([]);
  // Get the pre-fetched floor plan image URL from context
  const imageUrl = useFloorPlan();

  interface ApiResponse {
    objects: Array<{ cid: number; x: number; y: number; id: number }>;
  }

  //get objects positions:
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

  useEffect(() => {
    /**
     * Simulate polling data by refreshing the mock object list every 500ms.
     * Replace with actual API call when integrating backend.
     */
    fetchPositionData();
    const interval = setInterval(() => {
      fetchPositionData();
    }, 100);
    // Cleanup interval on component unmount to stop it from iterating.
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="ObjmapDiv">
      {imageUrl ? (
        <img src={imageUrl} alt="Floor Plan" />
      ) : (
        <div>Loading floor plan...</div>
      )}

      {objects.map((obj) => (
        <div
          key={obj.id}
          className="staticMapObj"
          style={{
            left: `${obj.x}%`,
            top: `${obj.y}%`,
          }}
        />
      ))}
    </div>
  );
};
