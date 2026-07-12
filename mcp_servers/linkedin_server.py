from fastmcp import FastMCP
from dotenv import load_dotenv
import requests
import json
import os
from datetime import datetime

load_dotenv()

mcp = FastMCP("linkedin-server")

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
HEADERS      = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type":  "application/json"
}


def get_linkedin_user_id() -> str:
    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers=HEADERS
    ).json()
    return response.get("sub", "")


@mcp.tool()
def create_linkedin_post(text: str) -> str:
    """Create a text post on LinkedIn"""
    try:
        user_id = get_linkedin_user_id()

        payload = {
            "author":         f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=HEADERS,
            json=payload
        ).json()

        if "id" in response:
            return json.dumps({
                "status":  "posted",
                "post_id": response["id"]
            })
        else:
            return f"Failed: {response}"

    except Exception as e:
        return f"Failed: {str(e)}"


@mcp.tool()
def create_linkedin_image_post(text: str, image_url: str) -> str:
    """Create a LinkedIn post with an image"""
    try:
        user_id = get_linkedin_user_id()

        payload = {
            "author":         f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status":      "READY",
                            "originalUrl": image_url
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=HEADERS,
            json=payload
        ).json()

        if "id" in response:
            return json.dumps({
                "status":  "posted",
                "post_id": response["id"]
            })
        else:
            return f"Failed: {response}"

    except Exception as e:
        return f"Failed: {str(e)}"


@mcp.tool()
def schedule_linkedin_post(text: str, schedule_time: str) -> str:
    """
    Schedule a LinkedIn post for later.
    schedule_time format: 'YYYY-MM-DD HH:MM'
    """
    try:
        datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")

        queue_file = "scheduled_posts.json"

        if os.path.exists(queue_file):
            with open(queue_file, "r") as f:
                queue = json.load(f)
        else:
            queue = []

        queue.append({
            "platform":      "linkedin",
            "type":          "text",
            "text":          text,
            "schedule_time": schedule_time,
            "status":        "pending",
            "created_at":    datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        with open(queue_file, "w") as f:
            json.dump(queue, f, indent=2)

        return f"LinkedIn post scheduled for {schedule_time}"

    except ValueError:
        return "Error: Invalid time format. Use 'YYYY-MM-DD HH:MM'"
    except Exception as e:
        return f"Failed: {str(e)}"


@mcp.tool()
def get_linkedin_analytics(post_id: str) -> str:
    """Get analytics for a LinkedIn post"""
    try:
        response = requests.get(
            f"https://api.linkedin.com/v2/socialActions/{post_id}",
            headers=HEADERS
        ).json()

        return json.dumps({
            "post_id":  post_id,
            "likes":    response.get("likesSummary", {}).get("totalLikes", 0),
            "comments": response.get("commentsSummary", {}).get("totalFirstLevelComments", 0)
        }, indent=2)

    except Exception as e:
        return f"Failed: {str(e)}"


if __name__ == "__main__":
    mcp.run()