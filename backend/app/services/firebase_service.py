"""
Firebase service: xác thực ID token và thao tác Firestore.

Hỗ trợ 2 chế độ:
- Production: dùng Firebase Admin SDK thực (cần file serviceAccountKey.json)
- Dev/Demo: nếu không có credentials, fallback sang in-memory store
  (tiện cho việc chấm bài / chạy thử mà không cần config Firebase).
"""
from __future__ import annotations

import os
import time
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Cố gắng import firebase_admin. Nếu không có hoặc không config được
# thì sẽ fallback sang in-memory.
try:
    import firebase_admin
    from firebase_admin import auth as fb_auth
    from firebase_admin import credentials, firestore

    _HAS_FIREBASE_LIB = True
except Exception:  # pragma: no cover
    _HAS_FIREBASE_LIB = False


class FirebaseService:
    def __init__(self) -> None:
        self._mode = "memory"  # "firebase" hoặc "memory"
        self._db = None
        self._memory_tasks: Dict[str, Dict[str, Any]] = {}
        self._memory_users: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        self._try_init_firebase()

    def _try_init_firebase(self) -> None:
        if not _HAS_FIREBASE_LIB:
            print("[FirebaseService] firebase_admin chưa cài, dùng in-memory store.")
            return

        cred_path = os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json")
        if not os.path.exists(cred_path):
            print(
                f"[FirebaseService] Không tìm thấy '{cred_path}', "
                "dùng in-memory store. Để bật Firebase thật, đặt biến môi trường "
                "FIREBASE_CREDENTIALS trỏ đến file service account JSON."
            )
            return

        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            self._db = firestore.client()
            self._mode = "firebase"
            print("[FirebaseService] Đã kết nối Firebase Admin SDK + Firestore.")
        except Exception as exc:
            print(f"[FirebaseService] Khởi tạo Firebase thất bại: {exc}")
            print("[FirebaseService] Dùng in-memory store thay thế.")

    @property
    def mode(self) -> str:
        return self._mode

    # ==================== AUTH ====================
    def verify_token(self, id_token: str) -> Dict[str, Any]:
        """
        Trả về dict chứa thông tin user (uid, email, name, ...).
        Raise ValueError nếu token không hợp lệ.
        """
        if self._mode == "firebase":
            try:
                return self._verify_with_retry(id_token)
            except Exception as exc:
                print("[Auth Error]", exc)  # log để debug production
                raise ValueError(f"Token không hợp lệ: {exc}") from exc

        # In-memory mode: token đơn giản dạng "demo:<uid>:<email>"
        if not id_token or not id_token.startswith("demo:"):
            raise ValueError("Token demo không hợp lệ. Định dạng: demo:<uid>:<email>")
        parts = id_token.split(":", 2)
        if len(parts) < 3:
            raise ValueError("Token demo không hợp lệ.")
        uid, email = parts[1], parts[2]
        with self._lock:
            self._memory_users[uid] = {"uid": uid, "email": email, "name": email}
        return {"uid": uid, "email": email, "name": email}
    
    def _verify_with_retry(self, id_token: str, retries: int = 3):
        for i in range(retries + 1):
            try:
                decoded = fb_auth.verify_id_token(
                    id_token,
                    clock_skew_seconds=60
                )

                return {
                    "uid": decoded.get("uid"),
                    "email": decoded.get("email"),
                    "name": decoded.get("name") or decoded.get("email"),
                }

            except Exception as e:
                msg = str(e)

                if "Token used too early" in msg and i < retries:
                    sleep_time = 2 ** i  # 1s → 2s → 4s
                    print(f"[Retry] Token too early, sleep {sleep_time}s")
                    time.sleep(sleep_time)
                    continue

                raise
    # ==================== TASKS ====================

    def create_task(self, user_id: str, title: str) -> Dict[str, Any]:
        now = datetime.utcnow()
        if self._mode == "firebase":
            doc_ref = self._db.collection("tasks").document()
            data = {
                "title": title,
                "done": False,
                "created_at": now,
                "user_id": user_id,
            }
            doc_ref.set(data)
            return {"id": doc_ref.id, **data}

        with self._lock:
            tid = str(uuid.uuid4())
            data = {
                "id": tid,
                "title": title,
                "done": False,
                "created_at": now,
                "user_id": user_id,
            }
            self._memory_tasks[tid] = data
            return data.copy()

    def list_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        if self._mode == "firebase":
            docs = (
                self._db.collection("tasks")
                .where("user_id", "==", user_id)
                .stream()
            )
            tasks = []
            for d in docs:
                data = d.to_dict()
                data["id"] = d.id
                tasks.append(data)
            tasks.sort(key=lambda x: x.get("created_at"), reverse=True)
            return tasks

        with self._lock:
            tasks = [t.copy() for t in self._memory_tasks.values() if t["user_id"] == user_id]
            tasks.sort(key=lambda x: x["created_at"], reverse=True)
            return tasks

    def update_task(
        self,
        user_id: str,
        task_id: str,
        title: Optional[str] = None,
        done: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        if self._mode == "firebase":
            doc_ref = self._db.collection("tasks").document(task_id)
            snap = doc_ref.get()
            if not snap.exists:
                return None
            data = snap.to_dict()
            if data.get("user_id") != user_id:
                return None
            updates = {}
            if title is not None:
                updates["title"] = title
            if done is not None:
                updates["done"] = done
            if updates:
                doc_ref.update(updates)
            new_snap = doc_ref.get().to_dict()
            new_snap["id"] = task_id
            return new_snap

        with self._lock:
            task = self._memory_tasks.get(task_id)
            if not task or task["user_id"] != user_id:
                return None
            if title is not None:
                task["title"] = title
            if done is not None:
                task["done"] = done
            return task.copy()

    def delete_task(self, user_id: str, task_id: str) -> bool:
        if self._mode == "firebase":
            doc_ref = self._db.collection("tasks").document(task_id)
            snap = doc_ref.get()
            if not snap.exists:
                return False
            if snap.to_dict().get("user_id") != user_id:
                return False
            doc_ref.delete()
            return True

        with self._lock:
            task = self._memory_tasks.get(task_id)
            if not task or task["user_id"] != user_id:
                return False
            del self._memory_tasks[task_id]
            return True


firebase_service = FirebaseService()
