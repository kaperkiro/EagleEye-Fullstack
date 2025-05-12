import React, { useRef, useEffect } from "react";

export const mock_obj_data = {
  objects: [
    { id: 1, x: 20, y: 45, cId: [1] },
    { id: 2, x: 78, y: 30, cId: [1, 1] },
    { id: 3, x: 50, y: 75, cId: [1] },
  ],
};

export interface ObjectHistory {
  id: number;
  history: { x: number; y: number }[];
}

export function objHistoryMock(id: number): ObjectHistory {
  const histories: Record<number, { x: number; y: number }[]> = {
    1: [
      { x: 20, y: 45 },
      { x: 22, y: 47 },
      { x: 25, y: 50 },
      { x: 30, y: 50 },
      { x: 35, y: 50 },
      { x: 40, y: 50 },
      { x: 45, y: 50 },
      { x: 50, y: 50 },
      { x: 55, y: 50 },
      { x: 60, y: 53 },
      { x: 65, y: 60 },
      { x: 65, y: 65 },
      { x: 70, y: 60 },
    ],
    2: [
      { x: 78, y: 30 },
      { x: 70, y: 30 },
      { x: 70, y: 45 },
      { x: 60, y: 45 },
      { x: 50, y: 45 },
      { x: 41, y: 45 },
      { x: 41, y: 35 },
      { x: 40, y: 30 },
      { x: 40, y: 20 },
    ],
    3: [
      { x: 50, y: 75 },
      { x: 53, y: 70 },
      { x: 55, y: 60 },
      { x: 55, y: 50 },
      { x: 50, y: 50 },
      { x: 45, y: 50 },
      { x: 40, y: 50 },
      { x: 35, y: 58 },
      { x: 35, y: 65 },
      { x: 35, y: 70 },
      { x: 35, y: 75 },
      { x: 35, y: 80 },
      { x: 34, y: 85 },
      { x: 34, y: 87.5 },
    ],
  };

  return {
    id,
    history: histories[id] ?? [],
  };
}

// Example heatmap data (e.g., from your backend)
export const heatmapData = {
  heatmap: {
    last_hour: [
      { x: 20, y: 45, intensity: 0.2 },
      { x: 25, y: 40, intensity: 0.6 },
      { x: 15, y: 50, intensity: 0.8 },
      { x: 20, y: 45, intensity: 0.2 },
      { x: 50, y: 30, intensity: 0.5 },
      { x: 70, y: 50, intensity: 0.8 },
      { x: 15, y: 70, intensity: 0.2 },
      { x: 40, y: 40, intensity: 1 },
      { x: 30, y: 60, intensity: 0.4 },
      { x: 32, y: 62, intensity: 0.5 },
      { x: 28, y: 58, intensity: 0.6 },
      { x: 35, y: 55, intensity: 0.7 },
      { x: 45, y: 55, intensity: 0.7 },
      { x: 50, y: 50, intensity: 0.9 },
      { x: 52, y: 48, intensity: 0.8 },
      { x: 55, y: 45, intensity: 0.8 },
      { x: 60, y: 40, intensity: 0.6 },
      { x: 65, y: 35, intensity: 0.5 },
      { x: 68, y: 38, intensity: 0.6 },
      { x: 70, y: 30, intensity: 0.4 },
      { x: 75, y: 50, intensity: 0.7 },
      { x: 80, y: 50, intensity: 0.7 },
      { x: 82, y: 53, intensity: 0.6 },
      { x: 85, y: 55, intensity: 0.6 },
      { x: 88, y: 57, intensity: 0.7 },
      { x: 90, y: 60, intensity: 0.8 },
      { x: 95, y: 65, intensity: 0.9 },
      { x: 40, y: 70, intensity: 0.5 },
      { x: 38, y: 72, intensity: 0.4 },
      { x: 35, y: 75, intensity: 0.4 },
      { x: 32, y: 78, intensity: 0.5 },
      { x: 30, y: 80, intensity: 0.6 },
      { x: 28, y: 82, intensity: 0.7 },
      { x: 25, y: 85, intensity: 0.7 },
      // Cluster in the center (around 40-60, 40-60)
      { x: 42, y: 42, intensity: 0.5 },
      { x: 44, y: 45, intensity: 0.6 },
      { x: 48, y: 47, intensity: 0.8 },
      { x: 50, y: 46, intensity: 0.7 },
      { x: 54, y: 48, intensity: 0.6 },
      { x: 56, y: 50, intensity: 0.4 },
      { x: 58, y: 52, intensity: 0.5 },
      { x: 60, y: 54, intensity: 0.6 },

      // Scattered points across other regions
      { x: 10, y: 10, intensity: 0.3 },
      { x: 12, y: 15, intensity: 0.2 },
      { x: 15, y: 12, intensity: 0.4 },
      { x: 85, y: 20, intensity: 0.7 },
      { x: 87, y: 22, intensity: 0.8 },
      { x: 90, y: 25, intensity: 0.9 },
      { x: 93, y: 27, intensity: 1.0 },
      { x: 5, y: 90, intensity: 0.4 },
      { x: 8, y: 88, intensity: 0.5 },
      { x: 10, y: 85, intensity: 0.6 },

      // Additional clusters and random points
      { x: 55, y: 10, intensity: 0.3 },
      { x: 60, y: 15, intensity: 0.5 },
      { x: 62, y: 18, intensity: 0.6 },
      { x: 80, y: 80, intensity: 0.7 },
      { x: 82, y: 82, intensity: 0.8 },
      { x: 84, y: 84, intensity: 0.9 },
      { x: 86, y: 86, intensity: 0.8 },
      { x: 88, y: 88, intensity: 0.7 },

      // A few more points to simulate extra busy spots
      { x: 20, y: 20, intensity: 0.5 },
      { x: 22, y: 24, intensity: 0.4 },
      { x: 24, y: 22, intensity: 0.6 },
      { x: 78, y: 40, intensity: 0.7 },
      { x: 80, y: 42, intensity: 0.8 },
      { x: 82, y: 44, intensity: 0.9 },
      { x: 85, y: 46, intensity: 0.8 },
    ],
    // You can include more ranges if needed
  },
  metadata: {
    gridDimensions: { minX: 0, maxX: 100, minY: 0, maxY: 100 },
    generatedAt: "2025-03-17T12:00:00Z",
  },
};
