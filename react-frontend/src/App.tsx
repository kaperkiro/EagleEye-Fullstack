import React, { useState } from "react";
import Logo from "./assets/logo.png";
import LiveViewData from "./components/LiveView";
import HeatMapData from "./components/HeatMap";
import LarmData from "./components/Alarms";
import "./css/App.css";
import { FloorPlanProvider } from "./components/floorPlanProvider.tsx";

function App() {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleButtonClick = (index: number) => {
    console.log("Button clicked!", index);
    setActiveIndex(index);
  };

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
        {/* Main Content */}
        {SiteData}
      </div>
    </FloorPlanProvider>
  );
}
export default App;
