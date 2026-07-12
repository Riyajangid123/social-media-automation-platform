from langgraph.types import interrupt
from graph.state import GraphState
import json

class HumanApprovalAgent:

    def approve(self, state: GraphState):
        print("DEBUG — human_approval_node reached!")

        draft = state.get("draft_posts", {})

        preview = {}

        if "twitter" in draft:
            raw = draft["twitter"]
            try:
                tweets = json.loads(raw)
            except:
                tweets = [raw]
            preview["twitter"] = {
                "type":   "thread",
                "tweets": tweets,
                "count":  len(tweets)
            }

        if "linkedin" in draft:
            raw = draft["linkedin"]
            try:
                li = json.loads(raw)
                preview["linkedin"] = {
                    "type":     "post",
                    "caption":  li.get("caption", "")[:200],
                    "hashtags": li.get("hashtags", [])
                }
            except:
                preview["linkedin"] = {"type": "post", "raw": str(raw)[:200]}

        human_choice = interrupt({
            "preview":  preview,
            "message":  "Please review this content",
            "options":  ["approve", "regenerate", "reject"]
        })

        if human_choice == "approve":
            approved = {}
            if "twitter"   in draft: approved["twitter"]   = draft["twitter"]
            if "linkedin"  in draft: approved["linkedin"]   = draft["linkedin"]

            return {
                "human_approved": True,
                "regenerate":     False,
                "approved_posts": approved
            }

        elif human_choice == "regenerate":
            return {
                "human_approved": False,
                "regenerate":     True,
                "draft_posts":    {},
                "retry_count":    state.get("retry_count", 0) + 1
            }

        else:
            return {
                "human_approved": False,
                "regenerate":     False,
                "draft_posts":    {},
                "final_output":   "Content rejected by human"
            }