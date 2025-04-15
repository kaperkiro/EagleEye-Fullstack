// src/FloorPlanProvider.tsx
import React, {
  useState,
  useEffect,
  createContext,
  useContext,
  ReactNode,
} from "react";

const BACKEND_URL = "http://localhost:5001";

// Create a context for the floor plan image URL
const FloorPlanContext = createContext<string>("");

interface FloorPlanProviderProps {
  children: ReactNode;
}

export const FloorPlanProvider: React.FC<FloorPlanProviderProps> = ({
  children,
}) => {
  const [imageUrl, setImageUrl] = useState("");

  useEffect(() => {
    // Fetch the image as a blob from the backend
    fetch(`${BACKEND_URL}/map`, { method: "GET", cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch floor plan image");
        }
        return response.blob();
      })
      .then((blob) => {
        // Convert the blob into an object URL usable in an <img> tag
        const url = URL.createObjectURL(blob);
        setImageUrl(url);
      })
      .catch((error) => {
        console.error("Error fetching floor plan image:", error);
      });
  }, []);

  return (
    <FloorPlanContext.Provider value={imageUrl}>
      {children}
    </FloorPlanContext.Provider>
  );
};

// Custom hook to use the floor plan image URL
export const useFloorPlan = () => useContext(FloorPlanContext);
