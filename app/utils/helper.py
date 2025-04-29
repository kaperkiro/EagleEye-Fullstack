def check_if_same_observation(obs1: dict, obs2: dict) -> bool:
    """Checks if the two different observations are the same object.

    Same if geocoords are max 1.5 m apart and clothes
    """
    x = 1.5  # meters
    max_distance = x / 111320

    # Get all data from the observations

    obs1_class = obs1["class"]
    obs2_class = obs2["class"]

    if obs1_class["type"] != obs2_class["type"]:
        return False

    obs1_upper_clothing_colors = obs1_class["upper_clothing_colors"][0]["name"]
    obs2_upper_clothing_colors = obs2_class["upper_clothing_colors"][0]["name"]
    obs1_lower_clothing_colors = obs1_class["lower_clothing_colors"][0]["name"]
    obs2_lower_clothing_colors = obs2_class["lower_clothing_colors"][0]["name"]

    if (
        obs1_upper_clothing_colors != obs2_upper_clothing_colors
        or obs1_lower_clothing_colors != obs2_lower_clothing_colors
    ):
        return False

    obs1_coords = obs1["geoposition"]
    obs2_coords = obs2["geoposition"]

    # Arbiterary distance threshold of 1.5 m
    if (
        abs(obs1_coords["latitude"] - obs2_coords["latitude"]) > max_distance
        and abs(obs1_coords["longitude"] - obs2_coords["longitude"]) > max_distance
    ):

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
