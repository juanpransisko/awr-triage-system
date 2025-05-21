
# based on the distance from similarity search
THRESHOLDS = {
    "Highest": {"duplicate": 0.10, "review": 0.25},
    "High": {"duplicate": 0.15, "review": 0.30},
    "Medium": {"duplicate": 0.20, "review": 0.35},
    "Low": {"duplicate": 0.25, "review": 0.40}
}

def get_thresholds(priority: str):
    return THRESHOLDS.get(priority, THRESHOLDS["Medium"])
