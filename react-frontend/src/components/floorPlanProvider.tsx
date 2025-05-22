import React, {
  useState,
  useEffect,
  createContext,
  useContext,
  ReactNode,
} from "react";

const BACKEND_URL = "http://localhost:5001";
const RETRY_INTERVAL_MS = 1000; // 1 second if no map is fetched
const UPDATE_INTERVAL_MS = 30000; // 30 seconds once map is fetched

// Create a context for the floor plan image URL
const FloorPlanContext = createContext<string>("");

interface FloorPlanProviderProps {
  children: ReactNode;
}

/**
 * Provider component that periodically fetches a floor plan image from the backend,
 * creates an object URL for it, and provides that URL via React context.
 * It automatically retries every second until a valid image is fetched,
 * then switches to a 30-second refresh interval. Old object URLs are revoked
 * to prevent memory leaks.
 *
 * @param children - React elements that need access to the floor plan image URL
 */
export const FloorPlanProvider: React.FC<FloorPlanProviderProps> = ({
  children,
}) => {
  const [imageUrl, setImageUrl] = useState("");
  const [hasMap, setHasMap] = useState(false); // Track if map is successfully fetched

  /**
   * Fetches the floor plan image from the backend as a Blob,
   * converts it to an object URL, revokes the previous URL if any,
   * and updates state accordingly.
   */
  const fetchFloorPlan = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/map`, {
        method: "GET",
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error("Failed to fetch floor plan image");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      if (imageUrl) URL.revokeObjectURL(imageUrl); // Revoke old URL to prevent memory leaks
      setImageUrl(url);
      setHasMap(true); // Map fetched successfully
      console.log("Floor plan image fetched successfully:", url);
    } catch (error) {
      console.error("Error fetching floor plan image:", error);
    }
  };

  /**
   * Effect hook to perform the initial fetch and schedule subsequent fetches
   * on a dynamic interval: retry every second until the first fetch succeeds,
   * then switch to a 30-second update interval.
   */
  useEffect(() => {
    // Initial fetch attempt
    fetchFloorPlan();
    // Set up interval with dynamic timing
    const intervalId = setInterval(
      () => {
        console.log(
          `Fetching floor plan image on interval (${
            (hasMap ? UPDATE_INTERVAL_MS : RETRY_INTERVAL_MS) / 1000
          } seconds)...`
        );
        fetchFloorPlan();
      },
      hasMap ? UPDATE_INTERVAL_MS : RETRY_INTERVAL_MS
    );

    // Clean up interval and URL on unmount
    return () => {
      clearInterval(intervalId);
      if (imageUrl) URL.revokeObjectURL(imageUrl); // Free memory
    };
  }, [hasMap]); // Re-run effect when hasMap changes to update interval timing

  return (
    <FloorPlanContext.Provider value={imageUrl}>
      {children}
    </FloorPlanContext.Provider>
  );
};

/**
 * Custom hook to access the current floor plan image URL from context.
 *
 * @returns The object URL string for the latest fetched floor plan image.
 */
export const useFloorPlan = () => useContext(FloorPlanContext);
