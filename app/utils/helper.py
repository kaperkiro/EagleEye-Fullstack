def check_if_same_observation(obs1: dict, obs2: dict) -> bool:
    """Checks if two different observations are of the same object.
    Same if geocoords are max 1.5 m apart and clothing colors match.
    """
    x = 1.5  # meters
    max_distance = x / 111320  # Convert meters to degrees

    # Get data from observations
    obs1_class = obs1.get("class", {})
    obs2_class = obs2.get("class", {})

    if obs1_class.get("type") != obs2_class.get("type"):
        return False

    # Safely access clothing colors
    obs1_upper = obs1_class.get("upper_clothing_colors", [{}])[0].get("name", "")
    obs2_upper = obs2_class.get("upper_clothing_colors", [{}])[0].get("name", "")
    obs1_lower = obs1_class.get("lower_clothing_colors", [{}])[0].get("name", "")
    obs2_lower = obs2_class.get("lower_clothing_colors", [{}])[0].get("name", "")

    if obs1_upper != obs2_upper or obs1_lower != obs2_lower:
        return False

    obs1_coords = obs1.get("geoposition", {})
    obs2_coords = obs2.get("geoposition", {})

    # Check if coordinates are within 1.5 meters
    lat_diff = abs(obs1_coords.get("latitude", 0) - obs2_coords.get("latitude", 0))
    lon_diff = abs(obs1_coords.get("longitude", 0) - obs2_coords.get("longitude", 0))
    if lat_diff > max_distance or lon_diff > max_distance:
        return False

    return True


def obs_test():
    # Example usage
    obs1 = {
        "geoposition": {"latitude": 59.3250, "longitude": 18.0700},
        "class": {
            "type": "Human",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Blue", "score": 0.7}],
        },
    }

    obs2 = {
        "geoposition": {"latitude": 59.32501, "longitude": 18.07001},
        "class": {
            "type": "Human",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Blue", "score": 0.7}],
        },
    }

    obs3 = {
        "geoposition": {"latitude": 59.4250, "longitude": 18.0700},
        "class": {
            "type": "Vehicle",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Blue", "score": 0.7}],
        },
    }

    obs4 = {
        "geoposition": {"latitude": 59.3250, "longitude": 18.0700},
        "class": {
            "type": "Human",
            "upper_clothing_colors": [{"name": "Red", "score": 0.8}],
            "lower_clothing_colors": [{"name": "Green", "score": 0.7}],
        },
    }
    assert check_if_same_observation(obs1, obs2) == True
    assert check_if_same_observation(obs1, obs3) == False
    assert check_if_same_observation(obs1, obs4) == False
    print("Observation tests passed!")


if __name__ == "__main__":
    obs_test()
