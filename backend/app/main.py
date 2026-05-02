from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth as auth_router
from app.routers import tasks as tasks_router
from app.services.firebase_service import firebase_service

app = FastAPI(
    title="Todo App API",
    version="1.0.0",
    description="Backend cho Todo App - LAB 2 (Firebase Auth + Firestore).",
)

# CORS: cho phép frontend (chạy ở port khác hoặc mở trực tiếp file html) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "Todo App API",
        "message": "API đang hoạt động.",
        "storage_mode": firebase_service.mode,
        "endpoints": [
            "GET /",
            "GET /health",
            "GET /auth/me",
            "GET /tasks",
            "POST /tasks",
            "PATCH /tasks/{task_id}",
            "DELETE /tasks/{task_id}",
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "storage_mode": firebase_service.mode,
    }


app.include_router(auth_router.router)
app.include_router(tasks_router.router)
