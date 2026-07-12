from fastmcp import FastMCP
from dotenv import load_dotenv
import tweepy
import json
import time
import os

load_dotenv()

mcp=FastMCP("twitter-server")

client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
)

@mcp.tool
def create_thread(tweets:list[str])-> str:
    """create and post a twitter thread from list of tweets"""
    print(f"DEBUG twitter_server — create_thread called with {len(tweets)} tweets")
    try:
        if not tweets:
            return "Error: No tweets provided"
        
        if len(tweets) > 25:
            return "Error: Max 25 tweets per thread"
        
        posted_ids  = []
        reply_to_id = None

        for i, tweet_text in enumerate(tweets):

            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."

            if reply_to_id is None:
                response = client.create_tweet(text=tweet_text)
            else:
                response = client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=reply_to_id
                )

            tweet_id    = response.data["id"]
            reply_to_id = tweet_id
            posted_ids.append(tweet_id)

            print(f"Posted tweet {i+1}/{len(tweets)}")

            if i < len(tweets) - 1:
                time.sleep(1)

        thread_url = f"https://twitter.com/i/web/status/{posted_ids[0]}"

        return f"Thread posted! Tweets: {len(posted_ids)} URL: {thread_url}"

    except Exception as e:
        return f"Failed: {str(e)}"
    

@mcp.tool()
def schedule_thread(tweets: list[str], schedule_time: str) -> str:
    """
    Schedule a Twitter thread for later.
    schedule_time format: 'YYYY-MM-DD HH:MM'
    """
    try:
        if not tweets:
            return "Error: No tweets provided"

        if len(tweets) > 25:
            return "Error: Max 25 tweets per thread"

        from datetime import datetime
        datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")

        queue_file = "scheduled_tweets.json"

        if os.path.exists(queue_file):
            with open(queue_file, "r") as f:
                queue = json.load(f)
        else:
            queue = []

        queue.append({
            "type":          "thread",
            "tweets":        tweets,
            "schedule_time": schedule_time,
            "status":        "pending",
            "created_at":    datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        with open(queue_file, "w") as f:
            json.dump(queue, f, indent=2)

        return f"Thread of {len(tweets)} tweets scheduled for {schedule_time}"

    except ValueError:
        return "Error: Invalid time format. Use: 'YYYY-MM-DD HH:MM'"
    except Exception as e:
        return f"Failed: {str(e)}"
    
@mcp.tool()
def get_account_analytics(username: str) -> str:
    """Get overall account analytics and performance summary"""
    try:
        user = client.get_user(
            username=username,
            user_fields=["public_metrics", "created_at", "description"]
        )

        metrics = user.data.public_metrics

        result = {
            "username":         username,
            "followers":        metrics["followers_count"],
            "following":        metrics["following_count"],
            "tweet_count":      metrics["tweet_count"],
            "listed_count":     metrics["listed_count"],
            "follower_ratio":   round(
                metrics["followers_count"] /
                max(metrics["following_count"], 1), 2
            )
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Failed to get account analytics: {str(e)}"


if __name__ == "__main__":
    mcp.run()


