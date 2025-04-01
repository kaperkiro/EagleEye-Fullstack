import React, { useEffect, useRef, useState } from "react";
import FloorPlan from "../assets/floor_plan.jpg";
import { heatmapData } from "./MockData";

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
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <h1
          style={{
            marginBottom: 40,
            marginTop: -40,
            color: "#1A202C",
            opacity: "75%",
            fontSize: "40px",
          }}
        >
          Select Timeframe
        </h1>
        <button
          style={{
            border: "solid black",
            backgroundColor: activeIndexHM === 0 ? "#3B82F6" : "white",
            width: "150px",
            height: "50px",
            marginBottom: "20px",
            fontSize: "24px",
            borderRadius: "20px",
            color: activeIndexHM === 0 ? "white" : "black",
          }}
          onClick={() => handleButtonClick(0)}
        >
          Last Hour
        </button>

        <button
          style={{
            border: "solid black",
            backgroundColor: activeIndexHM === 1 ? "#3B82F6" : "white",
            width: "150px",
            height: "50px",
            marginBottom: "20px",
            fontSize: "24px",
            borderRadius: "20px",
            color: activeIndexHM === 1 ? "white" : "black",
          }}
          onClick={() => handleButtonClick(1)}
        >
          6 Hours
        </button>
        <button
          style={{
            border: "solid black",
            backgroundColor: activeIndexHM === 2 ? "#3B82F6" : "white",
            width: "150px",
            height: "50px",
            marginBottom: "20px",
            fontSize: "24px",
            borderRadius: "20px",
            color: activeIndexHM === 2 ? "white" : "black",
          }}
          onClick={() => handleButtonClick(2)}
        >
          12 Hours
        </button>
        <button
          style={{
            border: "solid black",
            backgroundColor: activeIndexHM === 3 ? "#3B82F6" : "white",
            width: "150px",
            height: "50px",
            marginBottom: "20px",
            fontSize: "24px",
            borderRadius: "20px",
            color: activeIndexHM === 3 ? "white" : "black",
          }}
          onClick={() => handleButtonClick(3)}
        >
          18 Hours
        </button>
        <button
          style={{
            border: "solid black",
            backgroundColor: activeIndexHM === 4 ? "#3B82F6" : "white",
            width: "150px",
            height: "50px",
            marginBottom: "20px",
            fontSize: "24px",
            borderRadius: "20px",
            color: activeIndexHM === 4 ? "white" : "black",
          }}
          onClick={() => handleButtonClick(4)}
        >
          24 Hours
        </button>
      </div>
      <div
        className="mapDiv"
        style={{
          width: "75%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <FloorPlanWithHeatmap />
      </div>
    </div>
  );
};

export default HeatMapData;
