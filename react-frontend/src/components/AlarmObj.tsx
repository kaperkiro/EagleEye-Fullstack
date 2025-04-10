// src/StaticMapObj.tsx
import React, { useState, useEffect } from "react";
import FloorPlan from "../assets/floor_plan.jpg";
import { mock_obj_data } from "./MockData";
import "../css/AlarmObj.css";

// This component simply renders the objects on the floor plan without click behavior or history lines.
export const FloorPlanStaticObjects: React.FC = () => {
  // Store and update the objects periodically
  const [objects, setObjects] = useState(mock_obj_data.objects);

  useEffect(() => {
    const interval = setInterval(() => {
      // Update with the same mock data – replace with API call if needed
      setObjects(mock_obj_data.objects);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="ObjmapDiv">
      <img
        src={FloorPlan}
        alt="Floor Plan"
        style={{ width: "100%", height: "100%" }}
      />
      {objects.map((obj) => (
        // Render each object as a non-clickable dot
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
