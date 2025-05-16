import json
import logging
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
import os

# Constants
GRID_SIZE = 50
CELL_PCT = 100.0 / GRID_SIZE  # 5.0%

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_observation_timestamp(timestamp: str) -> datetime:
    """Parse UTC timestamp string to datetime object."""
    try:
        return datetime.fromisoformat(timestamp.rstrip("Z")).replace(
            tzinfo=timezone.utc
        )
    except ValueError as e:
        logger.warning(f"Invalid timestamp format: {timestamp}, error: {e}")
        raise


def read_and_filter_observations(filename: str, cutoff: datetime) -> List[Dict]:
    """Read and filter observations from JSON-Lines file within timeframe."""
    observations = []
    if not os.path.exists(filename):
        # create empty file if it doesn't exist
        with open(filename, "w", encoding="utf-8") as f:
            pass
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    batch = json.loads(line)
                    for obs in batch:
                        ts = parse_observation_timestamp(obs["timestamp"])
                        if ts >= cutoff:
                            observations.append(obs)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed JSON line: {line}")
                    continue
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        raise
    except IOError as e:
        logger.error(f"Error reading file {filename}: {e}")
        raise
    return observations


def bin_observations(
    observations: List[Dict], mapmanager, grid_size: int = GRID_SIZE
) -> np.ndarray:
    """Bin observations into a grid using NumPy."""
    counts = np.zeros((grid_size, grid_size), dtype=int)
    coords = []
    for obs in observations:
        try:
            lat = obs["geoposition"]["latitude"]
            lon = obs["geoposition"]["longitude"]
        except KeyError:
            # logger.warning(f"Missing lat/lon in observation: {obs}")
            continue
        try:
            u, v = mapmanager.convert_to_relative((lat, lon))
            u = max(0, min(u, 99.999))
            v = max(0, min(v, 99.999))
            coords.append((u, v))
        except Exception as e:
            logger.warning(f"Error converting coordinates ({lat}, {lon}): {e}")
            continue

    if coords:
        # Convert coordinates to grid indices
        coords = np.array(coords)
        x_indices = np.floor(coords[:, 0] / CELL_PCT).astype(int)
        y_indices = np.floor(coords[:, 1] / CELL_PCT).astype(int)
        # Increment counts using NumPy's advanced indexing
        np.add.at(counts, (y_indices, x_indices), 1)

    return counts


def generate_heatmap_data(counts: np.ndarray, grid_size: int = GRID_SIZE) -> List[Dict]:
    """Generate heatmap data from binned counts."""
    max_count = counts.max() or 1
    heat = []
    for y_idx in range(grid_size):
        for x_idx in range(grid_size):
            count = counts[y_idx, x_idx]
            if count > 0:
                x = x_idx * CELL_PCT + CELL_PCT / 2
                y = y_idx * CELL_PCT + CELL_PCT / 2
                intensity = count / max_count
                heat.append(
                    {
                        "x": round(x, 2),
                        "y": round(y, 2),
                        "intensity": round(intensity, 3),
                    }
                )
    return heat


def create_heatmap(
    timeframe_min: int,
    mapmanager,
    # filename: str = os.path.join("app", "heatmap", "heatmap_data.jl"),
    filename="/Users/kacperorzel/projects/skola/axis/Backend-Code/app/objects/heatmap_data.jl",
) -> Dict[str, List[Dict]]:
    """
    Generate a heatmap from observations within a given timeframe.

    Args:
        timeframe_min: Time window in minutes (e.g., 60 for the last hour).
        mapmanager: Object with convert_to_relative((lat, lon)) -> (u%, v%) method.
        filename: Path to JSON-Lines (.jl) file with observation arrays.

    Returns:
        Dictionary with heatmap data for the specified timeframe.
    """
    if int(timeframe_min) <= 0:
        raise ValueError("timeframe_min must be positive")

    # Compute cutoff in UTC
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=int(timeframe_min))

    # Read and filter observations
    observations = read_and_filter_observations(filename, cutoff)
    if not observations:
        logger.info("No observations found within timeframe")
        return {"heatmap": []}

    # Bin observations into grid using NumPy
    counts = bin_observations(observations, mapmanager)

    # Generate heatmap data
    heat = generate_heatmap_data(counts)

    return {"heatmap": heat}
