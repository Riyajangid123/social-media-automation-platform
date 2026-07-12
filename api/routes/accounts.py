from fastapi import APIRouter, HTTPException
from api.schemas import ConnectAccountRequest
from database.queries import save_connected_account, get_connected_account

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("/connect")
def connect_account(request: ConnectAccountRequest):
    try:
        save_connected_account(
            user_id=request.user_id,
            platform=request.platform,
            access_token=request.access_token,
            refresh_token=request.refresh_token,
            expires_at=request.expires_at
        )
        return {"status": "connected", "platform": request.platform}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connect/{user_id}/{platform}")
def get_account(user_id: str, platform: str):
    account = get_connected_account(user_id, platform)

    if not account:
        raise HTTPException(status_code=404, detail="Account not connected")

    return account