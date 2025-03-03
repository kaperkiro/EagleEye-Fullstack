// Test component for ListGroup
// This component is not used in the final project
import { useState } from "react";

interface Props {
  cameras: string[];
  heading: string;
}

function ListGroup({ cameras, heading }: Props) {
  // Hook
  let [selectedIndex, setSelectedIndex] = useState(-1);

  return (
    <>
      <h1>{heading}</h1>
      {cameras.length === 0 && <p>There are no cameras!</p>}
      <ul className="list-group">
        {cameras.map((camera, index) => (
          <li
            className={
              selectedIndex === index
                ? "list-group-item active"
                : "list-group-item"
            }
            key={camera}
            onClick={() => setSelectedIndex(index)}
          >
            {camera}
          </li>
        ))}
      </ul>
    </>
  );
}

export default ListGroup;
