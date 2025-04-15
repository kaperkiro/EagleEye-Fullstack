import React, { useEffect, useRef, useState } from "react";
import { heatmapData } from "./MockData";
import { useFloorPlan } from "./floorPlanProvider";
import "../css/HeatMap.css";

const FloorPlanWithHeatmap = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const imageUrl = useFloorPlan();

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
      // Convert the x and y percentages into pixel values.
      const x = (point.x / 100) * canvasWidth;
      const y = (point.y / 100) * canvasHeight;

      // Define the radius as needed.
      const radius = 5 * 3;

      // Determine the color based on intensity (which is now a value between 0 and 1).
      let red, green;
      const blue = 0; // Always 0.

      if (point.intensity <= 0.5) {
        // For intensities between 0 and 0.5, interpolate from green (0,255,0) to yellow (255,255,0).
        red = Math.round((point.intensity / 0.5) * 255);
        green = 255;
      } else {
        // For intensities above 0.5, interpolate from yellow (255,255,0) to red (255,0,0).
        red = 255;
        green = Math.round((1 - (point.intensity - 0.5) / 0.5) * 255);
      }

      // Create the center and edge colors with alpha values for opacity.
      const centerColor = `rgba(${red}, ${green}, ${blue}, 0.7)`; // Opaque center.
      const edgeColor = `rgba(${red}, ${green}, ${blue}, 0.4)`; // Fully transparent edge.

      // Create a radial gradient from center (opaque) to edge (transparent).
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      gradient.addColorStop(0, centerColor);
      gradient.addColorStop(1, edgeColor);

      // Draw the dot using the gradient.
      ctx.beginPath();
      ctx.fillStyle = gradient;
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fill();
    });
  }, []);

  return (
    <div className="floorpPlanDiv">
      <img src={imageUrl} alt="Floor Plan" />
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
