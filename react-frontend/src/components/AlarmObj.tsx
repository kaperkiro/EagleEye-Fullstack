// src/StaticMapObj.tsx
import React, { useState, useEffect } from "react";
import { useFloorPlan } from "./floorPlanProvider.tsx"; // adjust the path as necessary
import { mock_obj_data } from "./MockData";
import "../css/AlarmObj.css";

export const FloorPlanStaticObjects: React.FC = () => {
  const [objects, setObjects] = useState(mock_obj_data.objects);
  const imageUrl = useFloorPlan(); // Get the pre-fetched image URL

  useEffect(() => {
    const interval = setInterval(() => {
      // Update with the same mock data – replace with API call if needed
      setObjects(mock_obj_data.objects);
    }, 500);
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
