import React, { useEffect, useRef, useState } from "react";

import { useFloorPlan } from "./floorPlanProvider";
import "../css/HeatMap.css";

// Define the shape of a single heatmap point
interface HeatmapPoint {
  x: number; // percent X (0-100)
  y: number; // percent Y (0-100)
  intensity: number; // value between 0 and 1
}

// Props for the canvas component
interface FloorPlanWithHeatmapProps {
  points: HeatmapPoint[];
}

// Canvas component that draws an overlay heatmap
const FloorPlanWithHeatmap: React.FC<FloorPlanWithHeatmapProps> = ({
  points,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageUrl = useFloorPlan();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Use RAF for smoother redraw if needed
    const draw = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);

      points.forEach((pt) => {
        const x = (pt.x / 100) * width;
        const y = (pt.y / 100) * height;
        const radius = 7 * 3;

        // Color interpolation from green → yellow → red
        let red: number;
        let green: number;
        const blue = 0;
        if (pt.intensity <= 0.5) {
          red = Math.round((pt.intensity / 0.5) * 255);
          green = 255;
        } else {
          red = 255;
          green = Math.round((1 - (pt.intensity - 0.5) / 0.5) * 255);
        }

        const centerColor = `rgba(${red}, ${green}, ${blue}, 0.7)`;
        const edgeColor = `rgba(${red}, ${green}, ${blue}, 0.4)`;

        const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
        gradient.addColorStop(0, centerColor);
        gradient.addColorStop(1, edgeColor);

        ctx.beginPath();
        ctx.fillStyle = gradient;
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      });
    };

    const frame = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(frame);
  }, [points]);

  return (
    <div className="floorpPlanDiv">
      <img src={imageUrl} alt="Floor Plan" className="floorPlanImage" />
      <canvas
        ref={canvasRef}
        width={800}
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

// Parent component that handles fetching & state
export const HeatMapData: React.FC = () => {
  const [activeIndexHM, setActiveIndex] = useState<number>(0);
  const [points, setPoints] = useState<HeatmapPoint[]>([]);

  useEffect(() => {
    handleButtonClick(0);
  }, []);

  const handleButtonClick = (index: number) => {
    setActiveIndex(index);
    //[60, 360, 720, 1080, 1440];
    const timeframeMap = [1, 3, 5, 10, 1440];
    const minutes = timeframeMap[index];

    fetch(`http://localhost:5001/api/heatmap/${minutes}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`Server responded ${res.status}`);
        return res.json();
      })
      .then((data: { heatmap: Record<string, HeatmapPoint[]> }) => {
        const map = data.heatmap;
        // grab the first-value in that object:
        const firstKey = Object.keys(map)[0];
        const newPoints = map[firstKey];
        setPoints(newPoints);
      })
      .catch((err) => {
        console.error("Heatmap fetch error:", err);
      });
  };

  return (
    <div className="heatDiv">
      <div className="heatLeftSidebar">
        <h1 className="heatMapTitle">Select Timeframe</h1>
        {["Last Hour", "6 Hours", "12 Hours", "18 Hours", "24 Hours"].map(
          (label, i) => (
            <button
              key={i}
              className={`heatMapButton ${activeIndexHM === i ? "active" : ""}`}
              onClick={() => handleButtonClick(i)}
            >
              {label}
            </button>
          )
        )}
      </div>
      <div className="heatMapDiv">
        <FloorPlanWithHeatmap points={points} />
      </div>
    </div>
  );
};

export default HeatMapData;
