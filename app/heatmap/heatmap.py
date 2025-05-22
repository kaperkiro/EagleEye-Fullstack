import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from app.logger import get_logger

import numpy as np

# Constants
GRID_SIZE = 50
CELL_PCT = 100.0 / GRID_SIZE  # 2.0%


logger = get_logger("MAIN")


def parse_observation_timestamp(timestamp: str) -> datetime:
    """Parse UTC timestamp string to datetime object.
    Args:
        timestamp: ISO 8601 timestamp string (e.g., "2025-05-16T21:34:00Z").
    Returns:
        Datetime object in UTC.
    Raises:
        ValueError: If timestamp format is invalid.
    """
    try:
        return datetime.fromisoformat(timestamp.rstrip("Z")).replace(
            tzinfo=timezone.utc
        )
    except ValueError as e:
        logger.warning(f"Invalid timestamp format: {timestamp}, error: {e}")
        raise


def read_and_filter_observations(filename: str, cutoff: datetime) -> List[Dict]:
    """Read observations from JSON-Lines file, filtering by cutoff time.
    Args:
        filename: Path to JSON-Lines file containing one observation per line.
        cutoff: Datetime threshold (UTC) for filtering observations.
    Returns:
        List of observation dictionaries within the timeframe.
    Raises:
        IOError: If file reading fails.
    """
    observations = []
    dirpath = os.path.dirname(filename)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

    if not os.path.exists(filename):
        open(filename, "w", encoding="utf-8").close()  # Create empty file

    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                try:
                    obs = json.loads(line)
                    if parse_observation_timestamp(obs["timestamp"]) >= cutoff:
                        observations.append(obs)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed JSON line: {line.strip()}")
                except KeyError:
                    logger.warning(
                        f"Skipping observation without timestamp: {line.strip()}"
                    )
    except IOError as e:
        logger.error(f"Error reading file {filename}: {e}")
        raise

    return observations


def bin_observations(
    observations: List[Dict], mapmanager, grid_size: int = GRID_SIZE
) -> np.ndarray:
    """Bin observations into a grid based on relative coordinates.
    Args:
        observations: List of observation dictionaries with geoposition.
        mapmanager: Object with convert_to_relative((lat, lon)) -> (u%, v%) method.
        grid_size: Size of the grid (default: 50).
    Returns:
        2D NumPy array with binned counts.
    """
    counts = np.zeros((grid_size, grid_size), dtype=int)
    coords = []

    for observation in observations:
        geoposition = observation.get("geoposition", {})
        if not (lat := geoposition.get("latitude")) or not (
            lon := geoposition.get("longitude")
        ):
            continue
        try:
            u, v = mapmanager.convert_to_relative((lat, lon))
            coords.append((max(0, min(u, 99.999)), max(0, min(v, 99.999))))
        except Exception as e:
            logger.warning(f"Error converting coordinates ({lat}, {lon}): {e}")

    if coords:
        coords = np.array(coords)
        x_indices = np.floor(coords[:, 0] / CELL_PCT).astype(int)
        y_indices = np.floor(coords[:, 1] / CELL_PCT).astype(int)
        np.add.at(counts, (y_indices, x_indices), 1)
    return counts


def generate_heatmap_data(counts: np.ndarray, grid_size: int = GRID_SIZE) -> List[Dict]:
    """Generate heatmap data from binned counts.
    Args:
        counts: 2D NumPy array with binned observation counts.
        grid_size: Size of the grid (default: 50).
    Returns:
        List of dictionaries with x, y, and normalized intensity.
    """
    max_count = max(counts.max(), 1)
    heatmap_data = []

    for y_idx in range(grid_size):
        for x_idx in range(grid_size):
            if count := counts[y_idx, x_idx]:
                x = x_idx * CELL_PCT + CELL_PCT / 2
                y = y_idx * CELL_PCT + CELL_PCT / 2
                intensity = count / max_count
                heatmap_data.append(
                    {
                        "x": round(x, 2),
                        "y": round(y, 2),
                        "intensity": round(intensity, 3),
                    }
                )

    return heatmap_data


def delete_old_observations(filename: str, minutes: int = 1440) -> None:
    """Prune observations older than specified minutes from JSON-Lines file.
    Args:
        filename: Path to JSON-Lines file containing one observation per line.
        minutes: Age threshold in minutes (default: 1440, i.e., 24 hours).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    kept_observations = []

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                for line in file:
                    if not line.strip():
                        continue
                    try:
                        obs = json.loads(line)
                        if parse_observation_timestamp(obs["timestamp"]) >= cutoff:
                            kept_observations.append(obs)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping malformed JSON line: {line.strip()}")
                    except KeyError:
                        logger.warning(
                            f"Skipping observation without timestamp: {line.strip()}"
                        )

            with open(filename, "w", encoding="utf-8") as file:
                for obs in kept_observations:
                    file.write(json.dumps(obs) + "\n")

            # logger.info(f"Pruned observations older than {minutes} minutes; {len(kept_observations)} observations kept")
        except IOError as e:
            logger.error(f"Error processing file {filename}: {e}")
            raise
    else:
        logger.info(f"File {filename} does not exist; no pruning needed")


def create_heatmap(
    timeframe_min: int, mapmanager, filename: str
) -> Dict[str, List[Dict]]:
    """Generate a heatmap from observations within a timeframe.
    Args:
        timeframe_min: Time window in minutes (e.g., 60 for last hour).
        mapmanager: Object with convert_to_relative((lat, lon)) -> (u%, v%) method.
        filename: Path to JSON-Lines file with observations.
    Returns:
        Dictionary with heatmap data (e.g., {"heatmap": [{"x": 1.0, "y": 1.0, "intensity": 0.5}]}).
    Raises:
        ValueError: If timeframe_min is not positive.
    """
    if timeframe_min <= 0:
        raise ValueError("timeframe_min must be positive")

    delete_old_observations(filename)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeframe_min)
    observations = read_and_filter_observations(filename, cutoff)

    if not observations:
        logger.info("No observations found within timeframe")
        return {"heatmap": []}

    counts = bin_observations(observations, mapmanager)
    heatmap_data = generate_heatmap_data(counts)
    return {"heatmap": heatmap_data}
