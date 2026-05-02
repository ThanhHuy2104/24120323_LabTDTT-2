from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Nội dung công việc")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    done: Optional[bool] = None


class TaskOut(BaseModel):
    id: str
    title: str
    done: bool
    created_at: datetime
    user_id: str


class UserOut(BaseModel):
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
