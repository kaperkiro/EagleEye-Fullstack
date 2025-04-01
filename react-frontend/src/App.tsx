import React, { useState } from "react";
import Logo from "./assets/logo.png";
import LiveViewData from "./components/LiveView";
import HeatMapData from "./components/HeatMap";
import LarmData from "./components/Alarms";
import "./css/App.css";

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
    <div className="app-container">
      {/* Header Section */}
      <header className="app-header">
        <img src={Logo} alt="logga" className="app-logo" />
        <h1>EagleEye</h1>
        <div className="button-container">
          <button
            className={`toggle-button ${activeIndex === 0 ? "active" : ""}`}
            onClick={() => handleButtonClick(0)}
          >
            Live View
          </button>
          <button
            className={`toggle-button ${activeIndex === 1 ? "active" : ""}`}
            onClick={() => handleButtonClick(1)}
          >
            Historical
          </button>
          <button
            className={`toggle-button ${activeIndex === 2 ? "active" : ""}`}
            onClick={() => handleButtonClick(2)}
          >
            Larms
          </button>
        </div>
      </header>
      {/* Main Content */}
      {SiteData}
    </div>
  );
}
export default App;
