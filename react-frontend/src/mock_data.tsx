import React, { useRef, useEffect } from "react";

export const mock_obj_data = {
  objects: [
    { id: 1, x: 20, y: 45 },
    { id: 2, x: 78, y: 30 },
    { id: 3, x: 50, y: 75 },
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
      { x: 20, y: 45, intensity: 30 },
      { x: 50, y: 30, intensity: 5 },
    ],
    // You can include more ranges if needed
  },
  metadata: {
    gridDimensions: { minX: 0, maxX: 100, minY: 0, maxY: 100 },
    generatedAt: "2025-03-17T12:00:00Z",
  },
};

export const larmZones = {
  larmZones: [
    {
      id: 1,
      name: "Zone A",
      corners: {
        topLeft: { x: 10, y: 10 },
        topRight: { x: 30, y: 10 },
        bottomRight: { x: 30, y: 30 },
        bottomLeft: { x: 10, y: 30 },
      },
    },
    {
      id: 2,
      name: "Zone B",
      corners: {
        topLeft: { x: 40, y: 15 },
        topRight: { x: 60, y: 15 },
        bottomRight: { x: 60, y: 35 },
        bottomLeft: { x: 40, y: 35 },
      },
    },
    {
      id: 3,
      name: "Zone C",
      corners: {
        topLeft: { x: 20, y: 40 },
        topRight: { x: 50, y: 40 },
        bottomRight: { x: 50, y: 60 },
        bottomLeft: { x: 20, y: 60 },
      },
    },
  ],
};
