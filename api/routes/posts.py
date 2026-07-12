from fastapi import APIRouter, HTTPException
from api.schemas import GeneratePostRequest, GeneratePostResponse
from graph.workflow import app as graph_app
from langgraph.types import Command
from database.queries import get_pending_scheduled_posts
import json

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/generate", response_model=GeneratePostResponse)
async def generate_post(request: GeneratePostRequest):
    try:
        initial_state = {
            "user_id":                   request.user_id,
            "user_query":                request.user_query,
            "target_platforms":          request.target_platforms,
            "campaign_id":               request.campaign_id,
            "schedule_time":             request.schedule_time,
            "task_list":                 [],
            "current_step":              "",
            "retry_count":               0,
            "error_log":                 [],
            "rag_docs":                  [],
            "memory":                    {},
            "brand_voice":               "",
            "past_post_examples":        [],
            "trending_topics":           [],
            "hashtags":                  [],
            "competitor_posts":          [],
            "draft_posts":               {},
            "post_variants":             {},
            "generated_image_url":       None,
            "validation_passed":         False,
            "human_review_needed":       False,
            "human_approved":            None,
            "regenerate":                None,
            "approved_posts":            {},
            "optimal_post_time":         {},
            "publish_results":           {},
            "performance_scores":        {},
            "best_performing_platform": None,
            "analytics_report":          None,
            "final_output":              None,
            "last_saved_post_id":        None
        }

        config = {"configurable": {"thread_id": f"user_{request.user_id}"}}

        chunks = []
        async for chunk in graph_app.astream(initial_state, config=config):
            chunks.append(chunk)
            if "__interrupt__" in chunk:
                state = await graph_app.aget_state(config)
                draft = state.values.get("draft_posts", {})
                return GeneratePostResponse(
                    status="pending_approval",
                    draft_posts=draft,
                    publish_results={},
                    final_output="Waiting for human approval"
                )

        final_state = await graph_app.aget_state(config)
        values      = final_state.values

        if values.get("human_review_needed") is True or final_state.next:
            return GeneratePostResponse(
                status="pending_approval",
                draft_posts=values.get("draft_posts", {}),
                publish_results={},
                final_output="Waiting for human approval due to validation constraints."
            )

        return GeneratePostResponse(
            status="complete",
            draft_posts=values.get("draft_posts", {}),
            publish_results=values.get("publish_results", {}),
            final_output=values.get("final_output") or "Generation complete."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_post(user_id: int, choice: str):
    if choice not in ["approve", "regenerate", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid choice")

    try:
        config = {"configurable": {"thread_id": f"user_{user_id}"}}

        state_updates = {
            "human_approved": True if choice == "approve" else False,
            "regenerate": True if choice == "regenerate" else False,
        }

        final_state = None
        async for chunk in graph_app.astream(
            Command(
                resume={
                    "action": choice,
                    "platform": None
                },
                update=state_updates
            ),
            config=config
        ):
            if "__interrupt__" in chunk:
                state = await graph_app.aget_state(config)
                draft = state.values.get("draft_posts", {})
                return {
                    "status":      "pending_approval",
                    "draft_posts": draft,
                    "message":     "New content generated, awaiting approval"
                }

        final_state = await graph_app.aget_state(config)
        values      = final_state.values

        return {
            "status":          "complete",
            "publish_results": values.get("publish_results", {}),
            "final_output":    values.get("final_output")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduled")
def get_scheduled():
    try:
        posts = get_pending_scheduled_posts()
        return {"scheduled_posts": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))