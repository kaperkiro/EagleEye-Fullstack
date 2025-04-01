import React from "react";
import FloorPlan from "../assets/floor_plan.jpg";
import { mock_obj_data } from "./MockData";
import "../css/Alarms.css";

export const LarmData = () => {
  return (
    <div className="alarmsDiv">
      <div className="leftSidebar"></div>
      <div className="mapDiv">
        <div className="mapDiv2">
          <img className="floorPlanImage" src={FloorPlan} alt="Floor Plan" />
          {mock_obj_data.objects.map((obj) => {
            return (
              <button
                className="mapButton"
                key={obj.id}
                style={{
                  left: `${obj.x}%`,
                  top: `${obj.y}%`,
                }}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default LarmData;
