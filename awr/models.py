from enum import Enum
from pydantic import BaseModel


class Priority(str, Enum):
    SHOW_STOPPER = "Show Stopper"
    URGENT = "Urgent"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class JiraTicket(BaseModel):
    id: str
    summary: str
    description: str
    priority: Priority
    labels: list[str] = []
