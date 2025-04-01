import React from "react";
import FloorPlan from "../assets/floor_plan.jpg";
import { mock_obj_data } from "./MockData";

export const LarmData = () => {
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
      ></div>
      <div
        className="mapDiv"
        style={{
          width: "75%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div style={{ position: "relative", width: "100%", height: "100%" }}>
          <img
            src={FloorPlan}
            alt="Floor Plan"
            style={{ width: "100%", height: "100%" }}
          />
          {mock_obj_data.objects.map((obj) => {
            return (
              <button
                key={obj.id}
                style={{
                  position: "absolute",
                  left: `${obj.x}%`,
                  top: `${obj.y}%`,
                  zIndex: 1,
                  transform: "translate(-50%, -50%)",
                  width: "20px",
                  height: "20px",
                  backgroundColor: "#3B82F6",
                  borderRadius: "50%",
                  border: "2px solid",
                  cursor: "pointer",
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
