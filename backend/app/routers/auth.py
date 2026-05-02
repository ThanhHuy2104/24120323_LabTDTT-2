from fastapi import APIRouter, Depends

from app.schemas.task import UserOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)) -> UserOut:
    """
    Trả về thông tin user hiện tại dựa trên Firebase ID token.
    Frontend dùng endpoint này để xác nhận đăng nhập thành công.
    """
    return UserOut(uid=user["uid"], email=user.get("email"), name=user.get("name"))
