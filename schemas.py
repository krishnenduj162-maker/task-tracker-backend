from datetime import date
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    status: str
    priority: str
    description: str
    due_date: date | None = None


class PriorityRequest(BaseModel):
    task: str