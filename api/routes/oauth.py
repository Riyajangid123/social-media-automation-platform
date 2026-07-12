from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from database.queries import save_connected_account
from jose import jwt
from dotenv import load_dotenv
import os
import tweepy
import requests
import json

load_dotenv()

router = APIRouter(prefix="/oauth", tags=["oauth"])

@router.get("/twitter/connect")
def twitter_connect(token: str = Query(...)):
    """Redirect user to Twitter OAuth — token passed as query param"""
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY")),
            algorithms=["HS256"]
        )
        user_id = str(payload.get("sub"))
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    oauth1 = tweepy.OAuth1UserHandler(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        callback="https://sandworm-dorsal-scarce.ngrok-free.dev/oauth/twitter/callback"
    )

    try:
        auth_url = oauth1.get_authorization_url()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twitter OAuth error: {e}")

    tokens = {}
    if os.path.exists("temp_tokens.json"):
        try:
            with open("temp_tokens.json") as f:
                tokens = json.load(f)
        except Exception:
            tokens = {}

    request_token = oauth1.request_token["oauth_token"]
    tokens[request_token] = {
        "user_id": user_id,
        "request_token_secret": oauth1.request_token["oauth_token_secret"]
    }

    with open("temp_tokens.json", "w") as f:
        json.dump(tokens, f)

    return RedirectResponse(auth_url)


@router.get("/twitter/callback")
def twitter_callback(oauth_token: str, oauth_verifier: str):
    """Twitter redirects here after user authorizes"""
    try:
        with open("temp_tokens.json") as f:
            tokens = json.load(f)
    except Exception:
        raise HTTPException(status_code=400, detail="No temp tokens storage found")

    user_tokens = tokens.get(oauth_token)
    if not user_tokens:
        raise HTTPException(status_code=400, detail="OAuth token session expired or invalid")

    user_id = user_tokens["user_id"]

    oauth1 = tweepy.OAuth1UserHandler(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET")
    )
    oauth1.request_token = {
        "oauth_token": oauth_token,
        "oauth_token_secret": user_tokens["request_token_secret"]
    }

    try:
        access_token, access_token_secret = oauth1.get_access_token(oauth_verifier)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get access token: {e}")

    tokens.pop(oauth_token, None)
    with open("temp_tokens.json", "w") as f:
        json.dump(tokens, f)

    save_connected_account(
        user_id=user_id,
        platform="twitter",
        access_token=access_token,
        refresh_token=access_token_secret
    )

    print(f"Twitter connected for user {user_id}")

    return HTMLResponse("""
        <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h2>Twitter Connected Successfully!</h2>
            <p>You can close this tab and return to Virelo AI.</p>
            <script>
                setTimeout(() => { window.close(); }, 2000);
            </script>
        </body>
        </html>
    """)


@router.get("/linkedin/connect")
def linkedin_connect(token: str = Query(...)):
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"]
        )
        user_id = str(payload["sub"])
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    redirect_uri = "https://sandworm-dorsal-scarce.ngrok-free.dev/oauth/linkedin/callback"

    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=openid profile w_member_social"
        f"&state={user_id}"
    )

    return RedirectResponse(auth_url)

@router.get("/linkedin/callback")
def linkedin_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
):
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"{error}: {error_description}"
        )

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Authorization code not received."
        )

    user_id = int(state)

    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    redirect_uri = "https://sandworm-dorsal-scarce.ngrok-free.dev/oauth/linkedin/callback"

    token_response = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=token_response.json()
        )

    token_data = token_response.json()

    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in")

    save_connected_account(
        user_id=user_id,
        platform="linkedin",
        access_token=access_token,
        refresh_token="",
        expires_at=expires_in,
    )

    print(f"LinkedIn connected successfully for user {user_id}")

    return HTMLResponse("""
    <html>
        <body style="font-family:Arial;text-align:center;margin-top:60px;">
            <h2>LinkedIn Connected Successfully!</h2>
            <p>You can now close this tab and return to Virelo.</p>
            <script>
                setTimeout(() => window.close(), 3000);
            </script>
        </body>
    </html>
    """)
