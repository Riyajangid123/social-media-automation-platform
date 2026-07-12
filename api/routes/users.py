from fastapi import APIRouter, HTTPException
from api.schemas import UserCreate, UserResponse
from database.queries import get_or_create_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
def create_user(request: UserCreate):
    try:
        user_id = get_or_create_user(request.username, request.email)
        return UserResponse(
            id=user_id,
            username=request.username,
            email=request.email
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))