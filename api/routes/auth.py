from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.queries import get_user_by_email, create_user
from api.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    username: str
    email:    str
    password: str

class LoginRequest(BaseModel):
    email:    str
    password: str

@router.post("/register")
def register(request: RegisterRequest):
    existing = get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed  = hash_password(request.password)
    user_id = create_user(request.username, request.email, hashed)
    token   = create_access_token(user_id)

    return {
        "user_id":      user_id,
        "access_token": token,
        "token_type":   "bearer"
    }

@router.post("/login")
def login(request: LoginRequest):
    user = get_user_by_email(request.email)
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["id"])
    return {
        "user_id":      user["id"],
        "access_token": token,
        "token_type":   "bearer"
    }