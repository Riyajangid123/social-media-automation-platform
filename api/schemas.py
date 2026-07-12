from pydantic import BaseModel
from typing import Optional, List

class GeneratePostRequest(BaseModel):
    user_id:          int
    user_query:       str
    target_platforms: List[str]
    schedule_time:    Optional[str] = None
    campaign_id:      Optional[str] = None

class GeneratePostResponse(BaseModel):
    status:          str
    draft_posts:     dict
    publish_results: dict
    final_output:    Optional[str]

class UserCreate(BaseModel):
    username: str
    email:    str

class UserResponse(BaseModel):
    id:       int
    username: str
    email:    str

class ConnectAccountRequest(BaseModel):
    user_id:       int
    platform:      str
    access_token:  str
    refresh_token: Optional[str] = None
    expires_at:    Optional[str] = None