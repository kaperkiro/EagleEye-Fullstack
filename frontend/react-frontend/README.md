# EagleEye Frontend

This is the React + TypeScript frontend for the EagleEye project. It provides a live view of camera streams, historical heatmaps, and alarm zone management, all visualized on a dynamic floor plan.

## Features

- **Live View:** See real-time camera streams and tracked objects on the floor plan.
- **Historical Heatmap:** Visualize historical movement data as a heatmap overlay.
- **Alarms:** Define, activate/deactivate, and remove alarm zones on the floor plan. Get notified with sound when a zone is triggered.

## Project Structure

```
src/
  App.tsx                # Main application entry
  main.tsx               # React root rendering
  components/            # React components (LiveView, HeatMap, Alarms, etc.)
  assets/                # Images and audio assets
  css/                   # CSS files for styling
public/
  vite.svg               # Public assets
```

## Getting Started

### Prerequisites

- Node.js (v18+ recommended)
- npm

### Installation

1. Clone the repository and navigate to the frontend directory:
   ```sh
   cd EagleEye-Fullstack/frontend/react-frontend
   ```
2. Install dependencies:
   ```sh
   npm install
   ```

### Running the Development Server

Start the frontend in development mode with hot reloading:

```sh
npm run dev
```

The app will be available at [http://localhost:5173](http://localhost:5173) by default.

### Building for Production

To build the frontend for production:

```sh
npm run build
```

### Linting

To check code quality with ESLint:

```sh
npm run lint
```

### Preview Production Build

To preview the production build locally:

```sh
npm run preview
```

## Configuration

- The frontend expects the backend API to be running at `http://localhost:5001`.
- WebRTC video streams are expected from `http://localhost:8083/stream`.

## Customization

- Floor plan images and camera icons are in `src/assets/`.
- CSS styles can be modified in `src/css/`.

## License

This project is for educational purposes.

---

_For backend setup and more details, see the main project README._
