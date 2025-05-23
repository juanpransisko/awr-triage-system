from enum import Enum
from awr.models import Priority


class Thresholds:
    # text-embedding-3-large will return the normalized embeddings
    # after similarity search (cosine similarity)
    _VALUES = {
        Priority.SHOW_STOPPER: {"duplicate": 0.96, "review": 0.85},
        Priority.URGENT: {"duplicate": 0.93, "review": 0.82},
        Priority.HIGH: {"duplicate": 0.90, "review": 0.78},
        Priority.MEDIUM: {"duplicate": 0.85, "review": 0.75},
        Priority.LOW: {"duplicate": 0.80, "review": 0.70}
    }

    @classmethod
    def get(cls, priority: Priority) -> dict:
        return cls._VALUES.get(priority, cls._VALUES[Priority.MEDIUM])


# based on the distance from similarity search
# THRESHOLDS = {
#     "Highest": {"duplicate": 0.10, "review": 0.25},
#     "High": {"duplicate": 0.15, "review": 0.30},
#     "Medium": {"duplicate": 0.20, "review": 0.35},
#     "Low": {"duplicate": 0.25, "review": 0.40}
# }

# def get_thresholds(priority: str):
#     return THRESHOLDS.get(priority, THRESHOLDS["Medium"])
