import ListGroup from "./components/ListGroup";

function App() {
  let cameras = ["camera1", "camera2", "camera3", "camera4", "camera5"];

  return (
    <div>
      <ListGroup cameras={cameras} heading="Cameras" />
    </div>
  );
}

export default App;
