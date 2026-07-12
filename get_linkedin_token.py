import os
import webbrowser
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()

print("RUNNING FILE:", __file__)

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")

REDIRECT_URI = "http://localhost:8000/callback"

# OAuth scopes
SCOPES = [
    "w_member_social"
]

params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": " ".join(SCOPES),
}

auth_url = (
    "https://www.linkedin.com/oauth/v2/authorization?"
    + urllib.parse.urlencode(params)
)

print("=" * 70)
print("Opening LinkedIn Authorization Page...")
print("=" * 70)
print(auth_url)
print("=" * 70)

# Open browser automatically
webbrowser.open(auth_url)

print("\nAfter approving the application, LinkedIn will redirect to:")
print(REDIRECT_URI)
print("\nCopy ONLY the value after 'code=' from the URL.")

code = input("\nPaste authorization code here: ").strip()

print("\nExchanging code for access token...\n")

response = requests.post(
    "https://www.linkedin.com/oauth/v2/accessToken",
    data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
)

if response.status_code != 200:
    print("LinkedIn returned an error:")
    print(response.status_code)
    print(response.text)
    exit()

data = response.json()

print("=" * 70)
print("ACCESS TOKEN")
print("=" * 70)
print(data["access_token"])

print("\nExpires In:", data["expires_in"], "seconds")