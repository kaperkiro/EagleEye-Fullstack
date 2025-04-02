import React, { useEffect, useRef, useState } from "react";
import FloorPlan from "../assets/floor_plan.jpg";
import { heatmapData } from "./MockData";
import "../css/HeatMap.css";

const FloorPlanWithHeatmap = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    // Set canvas drawing context
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Ensure canvas is cleared
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Use the "last_hour" data for this example.
    const points = heatmapData.heatmap.last_hour;

    // Canvas dimensions (we assume the canvas fills the container)
    const canvasWidth = canvas.width;
    const canvasHeight = canvas.height;

    // Draw each heatmap point as a radial gradient circle
    points.forEach((point) => {
      // The x and y values are percentages (0-100). Convert them to pixels.
      const x = (point.x / 100) * canvasWidth;
      const y = (point.y / 100) * canvasHeight;

      // Map intensity to a radius (adjust scaling as needed)
      const radius = point.intensity * 3;

      // Create a radial gradient: center is red and opaque, edges are transparent
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      gradient.addColorStop(0, "rgba(255, 0, 0, 0.8)");
      gradient.addColorStop(1, "rgba(255, 0, 0, 0)");

      ctx.beginPath();
      ctx.fillStyle = gradient;
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fill();
    });
  }, []);

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
      }}
    >
      <img
        src={FloorPlan}
        alt="Floor Plan"
        style={{
          width: "100%",
          height: "100%",
          display: "block",
        }}
      />
      {/* Canvas overlay: pointerEvents: "none" so it doesn't block clicks */}
      <canvas
        ref={canvasRef}
        width={800} // Set these to match your floor plan image's native resolution or container size
        height={600}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      />
    </div>
  );
};

export const HeatMapData = () => {
  const [activeIndexHM, setActiveIndex] = useState(0);

  // Update active index on button click
  const handleButtonClick = (index: React.SetStateAction<number>) => {
    setActiveIndex(index);
  };

  return (
    <div className="heatMapDiv">
      <div className="heatLeftSidebar">
        <h1 className="heatMapTitle">Select Timeframe</h1>
        <button
          //We can create css for both states and use inline JS to go between both states...
          className={`heatMapButton ${activeIndexHM === 0 ? "active" : ""}`}
          onClick={() => handleButtonClick(0)}
        >
          Last Hour
        </button>

        <button
          className={`heatMapButton ${activeIndexHM === 1 ? "active" : ""}`}
          onClick={() => handleButtonClick(1)}
        >
          6 Hours
        </button>
        <button
          className={`heatMapButton ${activeIndexHM === 2 ? "active" : ""}`}
          onClick={() => handleButtonClick(2)}
        >
          12 Hours
        </button>
        <button
          className={`heatMapButton ${activeIndexHM === 3 ? "active" : ""}`}
          onClick={() => handleButtonClick(3)}
        >
          18 Hours
        </button>
        <button
          className={`heatMapButton ${activeIndexHM === 4 ? "active" : ""}`}
          onClick={() => handleButtonClick(4)}
        >
          24 Hours
        </button>
      </div>
      <div className="mapDiv">
        <FloorPlanWithHeatmap />
      </div>
    </div>
  );
};

export default HeatMapData;
