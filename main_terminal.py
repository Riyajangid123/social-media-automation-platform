import asyncio
from langgraph.types import Command
from graph.workflow import app
import json

async def handle_approval(config):
    """Shows tweet and gets human input"""
    state  = await app.aget_state(config)
    draft  = state.values.get("draft_posts", {})

    print("\n" + "="*50)
    print("CONTENT FOR YOUR APPROVAL:")
    print("="*50)

    if "twitter" in draft:
        raw    = draft["twitter"]
        try:
            tweets = json.loads(raw)
        except:
            tweets = [raw]
        print("\nTWITTER THREAD:")
        for i, tweet in enumerate(tweets):
            print(f"\nTweet {i+1}/{len(tweets)} ({len(tweet)}/280 chars):")
            print(tweet)
            print("-"*40)

    
    if "instagram" in draft:
        raw = draft["instagram"]
        try:
            ig = json.loads(raw)
            print("\nINSTAGRAM:")
            print(f"Caption: {ig.get('caption', '')[:200]}...")
            print(f"Hashtags: {' '.join(ig.get('hashtags', []))}")
        except:
            print(f"\nINSTAGRAM: {raw[:200]}...")


    if "linkedin" in draft:
        print(f"\nLINKEDIN: {draft['linkedin'][:200]}...")

    print("\n" + "="*50)
    print("Options:")
    print("  1. Approve and publish")
    print("  2. Regenerate")
    print("  3. Reject")

    while True:
        choice = input("\nYour choice (1/2/3): ").strip()
        if choice in ["1", "2", "3"]:
            break
        print("Invalid — enter 1, 2 or 3")

    return {"1": "approve", "2": "regenerate", "3": "reject"}[choice]


async def run_until_done(input_data, config):
    """Runs graph and handles all interrupts"""
    async for chunk in app.astream(input_data, config=config):
        node_name = list(chunk.keys())[0]
        if node_name != "__interrupt__":
            print(f"\nRunning: {node_name}")

        if "__interrupt__" in chunk:
            human_choice = await handle_approval(config)
            print(f"\nYou chose: {human_choice}")
            await run_until_done(Command(resume=human_choice), config)
            return

    print("\nGraph completed!")


async def main():
    print("\n" + "="*50)
    print("VIRELO AI — SOCIAL MEDIA AUTOMATION")
    print("="*50)

    user_query = input("\nWhat do you want to post about?\n→ ").strip()

    print("\nSelect platforms:")
    print("  1. Twitter only")
    print("  2. Twitter + LinkedIn")
    print("  3. Twitter + Instagram")
    print("  4. All platforms")

    platform_choice = input("\nYour choice (1/2/3/4): ").strip()
    platforms = {
        "1": ["twitter"],
        "2": ["twitter", "linkedin"],
        "3": ["twitter", "instagram"],
        "4": ["twitter", "linkedin", "instagram"]
    }.get(platform_choice, ["twitter"])

    schedule = input("\nSchedule time? (leave empty to post now)\nFormat: YYYY-MM-DD HH:MM\n→ ").strip()
    schedule_time = schedule if schedule else None

    print("\n" + "="*50)
    print(f"Query:     {user_query}")
    print(f"Platforms: {platforms}")
    print(f"Schedule:  {schedule_time or 'Post immediately'}")
    print("="*50 + "\n")

    initial_state = {
        "user_id":               1,
        "user_query":            user_query,
        "target_platforms":      platforms,
        "campaign_id":           None,
        "schedule_time":         schedule_time,
        "task_list":             [],
        "current_step":          "",
        "retry_count":           0,
        "error_log":             [],
        "rag_docs":              [],
        "memory":                {},
        "brand_voice":           "",
        "past_post_examples":    [],
        "trending_topics":       [],
        "hashtags":              [],
        "competitor_posts":      [],
        "draft_posts":           {},
        "post_variants":         {},
        "generated_image_url":   None,
        "validation_passed":     False,
        "human_review_needed":   False,
        "human_approved":        None,
        "regenerate":            None,
        "approved_posts":        {},
        "optimal_post_time":     {},
        "publish_results":       {},
        "performance_scores":    {},
        "best_performing_platform": None,
        "analytics_report":      None,
        "final_output":          None,
        "last_saved_post_id":    None
    }

    config = {"configurable": {"thread_id": "thread_1"}}

    await run_until_done(initial_state, config)

    final_state = await app.aget_state(config)
    values      = final_state.values

    print("\n" + "="*50)
    print("FINAL RESULT:")
    print("="*50)
    print(f"Status:          {values.get('final_output')}")
    print(f"Publish results: {values.get('publish_results')}")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())