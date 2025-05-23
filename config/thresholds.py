from types import MappingProxyType
from typing import Dict
from awr.models import Priority


class Thresholds:
    # text-embedding-3-large will return the normalized embeddings
    # after similarity search (cosine similarity)

    _VALUES: Dict[Priority, Dict[str, float]] = MappingProxyType(
        {
            Priority.SHOW_STOPPER: {"duplicate": 0.96, "review": 0.85},
            Priority.URGENT: {"duplicate": 0.93, "review": 0.82},
            Priority.HIGH: {"duplicate": 0.90, "review": 0.78},
            Priority.MEDIUM: {"duplicate": 0.85, "review": 0.75},
            Priority.LOW: {"duplicate": 0.80, "review": 0.70},
        }
    )

    @classmethod
    def get(cls, priority: Priority) -> Dict[str, float]:
        """Get similarity thresholds for the given ticket priority.
        default is MEDIUM if priority is not recognized."""
        return cls._VALUES.get(priority, cls._VALUES[Priority.MEDIUM])
