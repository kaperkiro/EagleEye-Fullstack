import json
from datetime import datetime, timedelta, timezone


def create_heatmap(timeframe_min, mapmanager, filename="heatmap_data.jl"):
    """
    timeframe_min: int, window in minutes (e.g. 60 for the last hour)
    mapmanager:  has convert_to_relative((lat,lon)) -> (u%, v%)
    filename:    path to JSON-Lines (.jl) file where each line is a JSON array of observations
    """
    # 1. compute cutoff
    now = datetime.now().astimezone()

    cutoff = now - timedelta(minutes=int(timeframe_min))

    # 2. load & flatten all observations from the .jl file
    observations = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                batch = json.loads(line)
                observations.extend(batch)
            except json.JSONDecodeError:
                # skip malformed lines
                continue

    # 3. filter to only those in the timeframe
    recent = []
    for obs in observations:
        # obs['timestamp'] is like "2025-04-25T09:06:26Z"
        ts = obs["timestamp"].replace("Z", "+00:00")
        t = datetime.fromisoformat(ts)
        if t >= cutoff:
            recent.append(obs)

    # 4. bin into a 20×20 grid
    grid_size = 20
    cell_pct = 100.0 / grid_size  # = 5.0 %
    counts = [[0] * grid_size for _ in range(grid_size)]

    for obs in recent:
        try:
            lat = obs["geoposition"]["latitude"]
            lon = obs["geoposition"]["longitude"]
        except KeyError:
            print("Missing lat/lon in observation:", obs)
            continue
        u, v = mapmanager.convert_to_relative((lat, lon))
        # clamp and integer‐bin
        u = max(0, min(u, 99.999))
        v = max(0, min(v, 99.999))
        ix = int(u // cell_pct)
        iy = int(v // cell_pct)
        counts[iy][ix] += 1

    # 5. normalize by the busiest cell
    max_count = max(max(row) for row in counts) or 1

    # 6. build the output list of non‐empty cells
    heat = []
    for iy in range(grid_size):
        for ix in range(grid_size):
            c = counts[iy][ix]
            if c > 0:
                # center of cell in percent coords
                x = ix * cell_pct + cell_pct / 2
                y = iy * cell_pct + cell_pct / 2
                intensity = round(c / max_count, 3)
                heat.append(
                    {"x": round(x, 2), "y": round(y, 2), "intensity": intensity}
                )

    return {f"last_{timeframe_min}_min": heat}
