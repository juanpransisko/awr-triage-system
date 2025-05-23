

from enum import Enum
from pydantic import BaseModel

class Priority(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class JiraTicket(BaseModel):
    id: str
    summary: str
    description: str
    priority: Priority
    labels: list[str] = []


