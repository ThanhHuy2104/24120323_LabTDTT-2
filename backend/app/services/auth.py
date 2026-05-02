from fastapi import Depends, Header, HTTPException, status

from app.services.firebase_service import firebase_service


def get_current_user(authorization: str = Header(default="")) -> dict:
    """
    Đọc header `Authorization: Bearer <token>` và trả về thông tin user.
    Raise 401 nếu không hợp lệ.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu Authorization header dạng 'Bearer <token>'.",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        return firebase_service.verify_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
