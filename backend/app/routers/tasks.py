from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services.auth import get_current_user
from app.services.firebase_service import firebase_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, user: dict = Depends(get_current_user)) -> TaskOut:
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Tiêu đề không được để trống.")
    data = firebase_service.create_task(user_id=user["uid"], title=title)
    return TaskOut(**data)


@router.get("", response_model=list[TaskOut])
def list_tasks(user: dict = Depends(get_current_user)) -> list[TaskOut]:
    items = firebase_service.list_tasks(user_id=user["uid"])
    return [TaskOut(**i) for i in items]


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    user: dict = Depends(get_current_user),
) -> TaskOut:
    title = payload.title.strip() if payload.title is not None else None
    updated = firebase_service.update_task(
        user_id=user["uid"],
        task_id=task_id,
        title=title,
        done=payload.done,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy task hoặc không có quyền.")
    return TaskOut(**updated)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, user: dict = Depends(get_current_user)) -> None:
    ok = firebase_service.delete_task(user_id=user["uid"], task_id=task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy task hoặc không có quyền.")
    return None
