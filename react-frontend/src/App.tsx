import React, { useState } from "react";
import Logo from "./assets/logo.png";
import LiveViewData from "./components/LiveView";
import HeatMapData from "./components/HeatMap.tsx";
import LarmData from "./components/Alarms";
import "./css/App.css";
import { FloorPlanProvider } from "./components/FloorPlanProvider.tsx";

/**
 * Main application for the frontend
 * Displays the header with navigation buttons and conditionally
 * renders data inside of the main content.
 * Either liveview, Hisorical heatmap or Alarms data
 */
function App() {
  const [activeIndex, setActiveIndex] = useState(0);

  /**
   * Handles button click in the header and sets acitve index
   * depending on the button index.
   *  @param {number} index - Index of the selected view (0 = LiveView, 1 = HeatMap, 2 = Alarms)
   */
  const handleButtonClick = (index: number) => {
    setActiveIndex(index);
  };

  //Display the main data depending on the active index.
  let SiteData;
  if (activeIndex === 0) {
    SiteData = <LiveViewData />;
  } else if (activeIndex === 1) {
    SiteData = <HeatMapData />;
  } else if (activeIndex === 2) {
    SiteData = <LarmData />;
  }

  return (
    <FloorPlanProvider>
      <div className="app-container">
        {/* Header Section */}
        <header className="app-header">
          <div className="title-container">
            <img src={Logo} alt="logga" className="app-logo" />
            <h1 className="title">EagleEye</h1>
          </div>
          <div className="button-container">
            <button
              className={`toggle-button ${activeIndex === 0 ? "active" : ""}`}
              onClick={() => handleButtonClick(0)}
            >
              <p className="buttonText">Live View</p>
            </button>
            <button
              className={`toggle-button ${activeIndex === 1 ? "active" : ""}`}
              onClick={() => handleButtonClick(1)}
            >
              <p className="buttonText">Historical</p>
            </button>
            <button
              className={`toggle-button ${activeIndex === 2 ? "active" : ""}`}
              onClick={() => handleButtonClick(2)}
            >
              <p className="buttonText">Alarms</p>
            </button>
          </div>
        </header>
        {/* Renders selected data content*/}
        {SiteData}
      </div>
    </FloorPlanProvider>
  );
}
export default App;
