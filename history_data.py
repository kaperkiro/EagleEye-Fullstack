import json
from datetime import datetime, timedelta, timezone


def load_hist_data(obj_id: str, minutes: int = 5, filename: str = "heatmap_data.jl"):
    """
    Returns a list of {x, y} points for the given track_id,
    including only records from the past `minutes` minutes.
    x is seconds since cutoff; y is latitude.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=minutes)

    points = []
    with open(filename, "r") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            if rec.get("track_id") != obj_id:
                continue

            # parse ISO timestamp
            t = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
            if t < cutoff:
                continue

            elapsed = int((t - cutoff).total_seconds())
            points.append({"x": elapsed, "y": rec["geoposition"]["latitude"]})

    # ensure chronological order
    points.sort(key=lambda p: p["x"])
    return points
