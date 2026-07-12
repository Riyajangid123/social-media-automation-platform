from graph.state import GraphState
from database.queries import save_scheduled_post, mark_post_published, mark_post_failed, get_connected_account
from dotenv import load_dotenv
from database.queries import get_connected_account
import requests  
import json
import os

load_dotenv()  


class PublisherAgent:

    def __init__(self):
        pass  

    async def publish(self, state: GraphState):
        user_id  = state.get("user_id")
        approved = state.get("approved_posts", {})
        schedule = state.get("schedule_time")
        post_id  = state.get("last_saved_post_id")

        if not state.get("human_approved"):
            return {"final_output": "Post not approved"}

        results = {}

        if approved.get("twitter"):  
            account = get_connected_account(user_id, "twitter")
            if not account:
                results["twitter"] = "Failed: Twitter not connected"
            else:
                client = self._get_twitter_client(account)
                results["twitter"] = await self._publish_twitter(
                    client, approved["twitter"], schedule, post_id
                )


        if approved.get("linkedin"):  
            account = get_connected_account(user_id, "linkedin")
            if not account:
                results["linkedin"] = "Failed: LinkedIn not connected"
            else:
                results["linkedin"] = await self._publish_linkedin(
                    account["access_token"],
                    approved["linkedin"],
                    schedule,
                    post_id
                )

        return {
            "publish_results": results,
            "final_output":    "Pipeline complete"
        }

    def _get_twitter_client(self, account: dict):
        import tweepy
        return tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=account["access_token"],
            access_token_secret=account["refresh_token"] 
        )

    async def _publish_twitter(self, twitter_client, raw, schedule, post_id=None):
        try:
            tweets = json.loads(raw)
        except:
            tweets = [raw]

        if schedule:
            scheduled_id = save_scheduled_post(
                generated_post_id=post_id,
                scheduled_time=schedule,
                status="pending"
            )
            return f"Scheduled for {schedule}"

        scheduled_id = save_scheduled_post(
            generated_post_id=post_id,
            scheduled_time=None,
            status="pending"
        )

        try:
            posted_ids  = []
            reply_to_id = None

            for i, tweet_text in enumerate(tweets):
                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."

                if reply_to_id is None:
                    response = twitter_client.create_tweet(text=tweet_text)
                else:
                    response = twitter_client.create_tweet(
                        text=tweet_text,
                        in_reply_to_tweet_id=reply_to_id
                    )

                tweet_id    = response.data["id"]
                reply_to_id = tweet_id
                posted_ids.append(tweet_id)

                import time
                if i < len(tweets) - 1:
                    time.sleep(2)

            thread_url = f"https://twitter.com/i/web/status/{posted_ids[0]}"
            mark_post_published(scheduled_id, posted_ids[0])
            return thread_url

        except Exception as e:
            mark_post_failed(scheduled_id)
            return f"Failed: {str(e)}"


    async def _publish_linkedin(self, access_token, raw,
                            schedule, post_id=None):

    
        try:
            if isinstance(raw, str):
                post_data = json.loads(raw)
            else:
                post_data = raw

            caption = post_data.get("caption", "")
            hashtags = post_data.get("hashtags", [])

            if isinstance(hashtags, list):
                text = f"{caption}\n\n{' '.join(hashtags)}".strip()
            else:
                text = caption

        except Exception:
            text = str(raw)

        if schedule:
            save_scheduled_post(
                generated_post_id=post_id,
                scheduled_time=schedule,
                status="pending"
            )
            return f"Scheduled for {schedule}"

        scheduled_id = save_scheduled_post(
            generated_post_id=post_id,
            scheduled_time=None,
            status="pending"
        )

        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            profile = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=headers
            ).json()

            user_id = profile.get("sub")

            if not user_id:
                raise Exception(f"Couldn't fetch LinkedIn user id: {profile}")

            payload = {
                "author": f"urn:li:person:{user_id}",
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
                headers=headers,
                json=payload
            )

            result = response.json()

            if response.status_code >= 400:
                raise Exception(result)

            mark_post_published(scheduled_id, result.get("id", ""))

            return f"https://www.linkedin.com/feed/update/{result.get('id')}"

        except Exception as e:
            mark_post_failed(scheduled_id)
            return f"Failed: {e}"