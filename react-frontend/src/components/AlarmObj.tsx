import React, { useState, useEffect } from "react";
import { useFloorPlan } from "./floorPlanProvider.tsx";
import { mock_obj_data } from "./MockData";
import "../css/AlarmObj.css";

/**
 * Displays the static floorplan image with buttons representing objects seen by cameras.
 *Position of objects are depending on the geological positions of the map and objects.
 *
 * @returns
 */

export const FloorPlanStaticObjects: React.FC = () => {
  // State for mock object positions
  const [objects, setObjects] = useState(mock_obj_data.objects);
  // Get the pre-fetched floor plan image URL from context
  const imageUrl = useFloorPlan();

  useEffect(() => {
    /**
     * Simulate polling data by refreshing the mock object list every 500ms.
     * Replace with actual API call when integrating backend.
     */
    const interval = setInterval(() => {
      setObjects(mock_obj_data.objects);
    }, 500);
    // Cleanup interval on component unmount
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
