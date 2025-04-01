import React, { useState } from "react";
import Logo from "./assets/logo.png";
import LiveViewData from "./components/LiveView";
import HeatMapData from "./components/HeatMap";
import LarmData from "./components/Alarms";

function App() {
  // State to track the active button index
  const [activeIndex, setActiveIndex] = useState(0);

  // Update active index on button click
  const handleButtonClick = (index: React.SetStateAction<number>) => {
    console.log("Button clicked!", index);
    setActiveIndex(index);
  };

  let SiteData;
  if (activeIndex == 0) {
    SiteData = <LiveViewData />;
  } else if (activeIndex == 1) {
    SiteData = <HeatMapData />;
  } else if (activeIndex == 2) {
    SiteData = <LarmData />;
  }

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        display: "flex",
        overflow: "hidden",
        flexDirection: "column",
        margin: 0, // reset default margin if needed
      }}
    >
      {/* Header Section */}
      <header
        style={{
          borderBottom: "solid",
          display: "flex",
          backgroundColor: "#FFFFFF",
          padding: "20px",
          textAlign: "center",
        }}
      >
        <img
          src={Logo}
          alt="logga"
          style={{
            width: "100px",
            height: "100px",
          }}
        />
        <h1 style={{ margin: 20 }}>EagleEye</h1>

        <div
          className="ButtonContainer"
          style={{
            display: "flex",
            backgroundColor: "#ffffff",
            textAlign: "center",
            alignItems: "center",
            flexDirection: "row",
            marginLeft: "120px",
          }}
        >
          <button
            style={{
              border: "solid black",
              marginLeft: 40,
              backgroundColor: activeIndex === 0 ? "#3B82F6" : "white",
              width: "150px",
              height: "50px",
              fontSize: "24px",
              borderRadius: "20px",
              color: activeIndex === 0 ? "white" : "black",
            }}
            onClick={() => handleButtonClick(0)}
          >
            Live View
          </button>
          <button
            style={{
              border: "solid black",
              marginLeft: 50,
              backgroundColor: activeIndex === 1 ? "#3B82F6" : "white",
              width: "150px",
              height: "50px",
              fontSize: "24px",
              borderRadius: "20px",
              color: activeIndex === 1 ? "white" : "black",
            }}
            onClick={() => handleButtonClick(1)}
          >
            Historical
          </button>
          <button
            style={{
              border: "solid black",
              marginLeft: 50,
              backgroundColor: activeIndex === 2 ? "#3B82F6" : "white",
              width: "150px",
              height: "50px",
              fontSize: "24px",
              borderRadius: "20px",
              color: activeIndex === 2 ? "white" : "black",
            }}
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
