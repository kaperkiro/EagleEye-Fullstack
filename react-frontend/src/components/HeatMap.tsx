import React, { useEffect, useRef, useState } from "react";
import { useFloorPlan } from "./FloorPlanProvider";
import "../css/HeatMap.css";

interface HeatmapPoint {
  x: number; // percent X (0-100)
  y: number; // percent Y (0-100)
  intensity: number; // value between 0 and 1
}

interface FloorPlanWithHeatmapProps {
  points: HeatmapPoint[];
  radius?: number; // Influence radius for each point (pixels)
  colorStops?: { offset: number; color: string }[]; // Custom color gradient
}

const FloorPlanWithHeatmap: React.FC<FloorPlanWithHeatmapProps> = ({
  points,
  radius = 20,
  colorStops = [
    { offset: 0.0, color: "rgba(0, 0, 255, 0.0)" }, // Transparent blue
    { offset: 0.1, color: "rgba(0, 64, 255, 0.08)" }, // Vivid light blue
    { offset: 0.2, color: "rgba(0, 128, 255, 0.16)" }, // Bright blue
    { offset: 0.3, color: "rgba(0, 192, 255, 0.24)" }, // Strong cyan
    { offset: 0.4, color: "rgba(0, 255, 192, 0.32)" }, // Vibrant cyan-green
    { offset: 0.5, color: "rgba(0, 255, 128, 0.4)" }, // Bold green
    { offset: 0.6, color: "rgba(128, 255, 0, 0.48)" }, // Bright yellow-green
    { offset: 0.7, color: "rgba(255, 255, 0, 0.56)" }, // Intense yellow
    { offset: 0.8, color: "rgba(255, 192, 0, 0.64)" }, // Vivid orange
    { offset: 0.9, color: "rgba(255, 104, 0, 0.72)" }, // Strong orange-red
    { offset: 1.0, color: "rgba(255, 0, 0, 0.8)" }, // Bold red, opacity 0.8
  ],
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageUrl = useFloorPlan();
  const glRef = useRef<WebGLRenderingContext | null>(null);
  const programRef = useRef<WebGLProgram | null>(null);
  const pointsBufferRef = useRef<Float32Array | null>(null);

  // Log points for debugging
  useEffect(() => {
    console.log("Points:", points);
    console.log("Points count:", points.length);
  }, [points]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Initialize WebGL
    const gl = canvas.getContext("webgl");
    if (!gl) {
      console.error("WebGL not supported");
      return;
    }
    glRef.current = gl;

    // Enable blending for transparent colors
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

    // Draw heatmap function
    const drawHeatmap = () => {
      const gl = glRef.current;
      const program = programRef.current;
      if (!gl || !program) {
        console.warn("WebGL or program not initialized");
        return;
      }

      if (!points || points.length === 0) {
        // Clear canvas when no points
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT);
        return;
      }

      // Update points
      const pointData = new Float32Array(points.length * 3);
      points.forEach((pt, i) => {
        pointData[i * 3] = pt.x / 100; // Normalize x to 0-1
        pointData[i * 3 + 1] = 1 - pt.y / 100; // Normalize and flip y to match WebGL
        pointData[i * 3 + 2] = Math.min(Math.max(pt.intensity, 0), 1); // Clamp intensity
      });
      pointsBufferRef.current = pointData;
      console.log("Point data:", Array.from(pointData));

      gl.uniform3fv(gl.getUniformLocation(program, "u_points"), pointData);

      // Clear and draw
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    };

    // Resize canvas to match parent
    const resizeCanvas = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);
        if (programRef.current) {
          gl.uniform2f(
            gl.getUniformLocation(programRef.current, "u_resolution"),
            canvas.width,
            canvas.height
          );
          drawHeatmap();
        }
      }
    };

    // Vertex Shader: Full-screen quad
    const vertexShaderSource = `
      #version 100
      attribute vec2 a_position;
      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `;

    // Fragment Shader: Gaussian-like heatmap with color gradient
    const fragmentShaderSource = `
      #version 100
      precision mediump float;
      uniform vec2 u_resolution;
      uniform float u_radius;
      uniform vec3 u_points[${points.length}];
      uniform vec4 u_colorStops[${colorStops.length}];
      uniform float u_colorOffsets[${colorStops.length}];

      void main() {
        vec2 fragCoord = gl_FragCoord.xy;
        float density = 0.0;

        // Calculate density from all points
        for (int i = 0; i < ${points.length}; i++) {
          vec2 point = u_points[i].xy * u_resolution;
          float intensity = u_points[i].z;
          float dist = length(fragCoord - point);
          float influence = exp(-dist * dist / (2.0 * u_radius * u_radius));
          density += influence * intensity;
        }

        // Normalize density (adjust based on expected max density)
        density = clamp(density * 2.0, 0.0, 1.0); // Scale to enhance visibility

        // Interpolate color based on density
        vec4 color = u_colorStops[0]; // Default to first color (transparent)
        for (int i = 0; i < ${colorStops.length - 1}; i++) {
          if (density >= u_colorOffsets[i] && density <= u_colorOffsets[i + 1]) {
            float t = (density - u_colorOffsets[i]) / (u_colorOffsets[i + 1] - u_colorOffsets[i]);
            color = mix(u_colorStops[i], u_colorStops[i + 1], t);
            break;
          }
        }
        if (density > u_colorOffsets[${colorStops.length - 1}]) {
          color = u_colorStops[${colorStops.length - 1}];
        }

        gl_FragColor = color;
      }
    `;

    // Compile shaders
    const vertexShader = compileShader(
      gl,
      vertexShaderSource,
      gl.VERTEX_SHADER
    );
    const fragmentShader = compileShader(
      gl,
      fragmentShaderSource,
      gl.FRAGMENT_SHADER
    );
    if (!vertexShader || !fragmentShader) {
      console.error("Shader compilation failed");
      return;
    }

    // Create program
    const program = gl.createProgram();
    if (!program) {
      console.error("Failed to create WebGL program");
      return;
    }
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error("Program link error:", gl.getProgramInfoLog(program));
      return;
    }
    gl.useProgram(program);
    programRef.current = program;

    // Setup quad vertices (full-screen)
    const vertices = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
    const vertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    const positionLoc = gl.getAttribLocation(program, "a_position");
    gl.enableVertexAttribArray(positionLoc);
    gl.vertexAttribPointer(positionLoc, 2, gl.FLOAT, false, 0, 0);

    // Setup uniforms
    const resolutionLoc = gl.getUniformLocation(program, "u_resolution");
    const radiusLoc = gl.getUniformLocation(program, "u_radius");
    gl.uniform2f(resolutionLoc, canvas.width, canvas.height);
    gl.uniform1f(radiusLoc, radius);
    console.log(
      "Resolution:",
      [canvas.width, canvas.height],
      "Radius:",
      radius
    );

    // Setup color stops
    const colorStopColors = colorStops
      .map((stop) => {
        const { r, g, b, a } = parseColor(stop.color);
        return [r / 255, g / 255, b / 255, a];
      })
      .flat();
    const colorStopOffsets = colorStops.map((stop) => stop.offset);
    gl.uniform4fv(
      gl.getUniformLocation(program, "u_colorStops"),
      new Float32Array(colorStopColors)
    );
    gl.uniform1fv(
      gl.getUniformLocation(program, "u_colorOffsets"),
      new Float32Array(colorStopOffsets)
    );
    console.log("Color stops:", colorStopColors, "Offsets:", colorStopOffsets);

    // Initial draw
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      if (gl && program) gl.deleteProgram(program);
      if (gl && vertexShader) gl.deleteShader(vertexShader);
      if (gl && fragmentShader) gl.deleteShader(fragmentShader);
      if (gl && vertexBuffer) gl.deleteBuffer(vertexBuffer);
    };
  }, [points, radius, colorStops]);

  // Helper: Compile shader
  const compileShader = (
    gl: WebGLRenderingContext,
    source: string,
    type: number
  ) => {
    const shader = gl.createShader(type);
    if (!shader) return null;
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error("Shader compile error:", gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }
    return shader;
  };

  // Helper: Parse rgba color string
  const parseColor = (color: string) => {
    const match = color.match(
      /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/
    );
    if (!match) {
      console.warn("Invalid color format:", color);
      return { r: 0, g: 0, b: 0, a: 1 };
    }
    return {
      r: parseInt(match[1]),
      g: parseInt(match[2]),
      b: parseInt(match[3]),
      a: match[4] ? parseFloat(match[4]) : 1,
    };
  };

  return (
    <div className="ObjmapDiv">
      {imageUrl ? (
        <img
          src={imageUrl}
          alt="Floor Plan"
          style={{ width: "100%", height: "100%", zIndex: 0 }}
        />
      ) : (
        <div
          style={{
            width: "100%",
            height: "100%",
            background: "#eee",
            zIndex: 0,
          }}
        />
      )}
      {points && points.length > 0 ? (
        <canvas
          ref={canvasRef}
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            pointerEvents: "none",
            zIndex: 1,
          }}
        />
      ) : (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(54, 54, 54, 0.2)",
            zIndex: 1,
          }}
        >
          <h1
            style={{
              color: "black",
              fontSize: "2rem",
              background: "white",
              borderRadius: "10px",
              padding: "10px",
              backgroundColor: "rgba(255, 255, 255, 0.81)",
            }}
          >
            No historical data available
          </h1>
        </div>
      )}
    </div>
  );
};



// Parent component that handles fetching & state
export const HeatMapData: React.FC = () => {
  const [activeIndexHM, setActiveIndex] = React.useState<number>(0);
  const [points, setPoints] = React.useState<HeatmapPoint[]>([]);
  // Track saving state for loading message
  const [isLoading, setIsLoading] = useState(false);

  React.useEffect(() => {
    handleButtonClick(0);
  }, []);

  const handleButtonClick = (index: number) => {
    setActiveIndex(index);
    const timeframeMap = [1, 3, 5, 10, 1440];
    const minutes = timeframeMap[index];
    setIsLoading(true); // Set loading state

    fetch(`http://localhost:5001/api/heatmap/${minutes}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`Server responded ${res.status}`);
        setIsLoading(false); // Clear loading state
        return res.json();
      })
      .then((data: { heatmap: Record<string, HeatmapPoint[]> }) => {
        const map = data.heatmap;
        const firstKey = Object.keys(map)[0];
        const newPoints = map[firstKey] || []; // Fallback to empty array if undefined
        setPoints(newPoints);
      })
      .catch((err) => {
        console.error("Heatmap fetch error:", err);
        setPoints([]); // Set empty array on error
      });
  };

  return (
    <div className="liveViewDiv">
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
      <div className="ObjmapDiv">
        <FloorPlanWithHeatmap points={points} />
          {isLoading && (
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                backgroundColor: "rgba(0, 0, 0, 0.7)",
                color: "white",
                padding: "10px 20px",
                borderRadius: "5px",
                zIndex: 10,
              }}
            >
              Loading...
            </div>
        )}
      </div>
    </div>
  );
};

export default HeatMapData;
