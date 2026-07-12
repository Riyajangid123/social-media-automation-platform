from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import GraphState
from agents.rag_agent import RagAgent
from agents.superviser_agent import SupervisorAgent
from agents.research_agent import ResearchAgent
from agents.twitter_agent import TwitterAgent
from agents.reviewer_agent import ReviewerAgent
from agents.human_approval_agent import HumanApprovalAgent
from agents.publisher_agent import PublisherAgent
from agents.instagram_agent import InstagramAgent
from agents.linkedin_agent import LinkedInAgent
import json

rag_agent            = RagAgent()
supervisor_agent     = SupervisorAgent()
research_agent       = ResearchAgent()
twitter_agent        = TwitterAgent()
instagram_agent      = InstagramAgent()
linkedin_agent       = LinkedInAgent()
reviewer_agent       = ReviewerAgent()
human_approval_agent = HumanApprovalAgent()
publisher_agent      = PublisherAgent()

def extract_clean_content(raw_data) -> tuple[str, list]:
    """Helper to safely extract captions and hashtags from dirty/nested JSON strings."""
    caption = ""
    hashtags = []
    if isinstance(raw_data, str):
        cleaned = raw_data.strip()
        if cleaned.startswith("{") or cleaned.startswith("["):
            try:
                raw_data = json.loads(cleaned)
            except json.JSONDecodeError:
                return cleaned, []
        else:
            return cleaned, []

    if isinstance(raw_data, dict):
        for key in ["caption", "text", "content", "tweets"]:
            if key in raw_data:
                inner_val = raw_data[key]
                if isinstance(inner_val, str) and inner_val.strip().startswith("{"):
                    inner_caption, inner_tags = extract_clean_content(inner_val)
                    if inner_caption: caption = inner_caption
                    if inner_tags: hashtags = inner_tags
                else:
                    caption = str(inner_val)
                break
        if "hashtags" in raw_data and isinstance(raw_data["hashtags"], list):
            hashtags = raw_data["hashtags"]
        if not caption and not hashtags:
            caption = str(raw_data)
    return caption, hashtags

def finalize_posts_node(state: GraphState):
    draft_posts = state.get("draft_posts", {})
    sanitized_approved = {}

    for platform, content in draft_posts.items():
        caption, hashtags = extract_clean_content(content)
        
        if not caption:
            caption = str(content)
            
        tag_string = " ".join(hashtags) if isinstance(hashtags, list) else str(hashtags)
        
        if tag_string:
            sanitized_approved[platform] = f"{caption}\n\n{tag_string}".strip()
        else:
            sanitized_approved[platform] = caption.strip()

    return {"approved_posts": sanitized_approved, "draft_posts": draft_posts}

def after_reviewer(state: GraphState):
    print(f"DEBUG after_reviewer — human_review_needed: {state.get('human_review_needed')}")
    if state.get("human_review_needed"):
        return state.get("regenerate_platform") or "twitter"
    return "human_approval"
 
def after_human(state: GraphState) -> str:
    draft_posts = state.get("draft_posts", {})
    for platform, content in list(draft_posts.items()):
        if isinstance(content, str) and content.strip().startswith("{"):
            try:
                parsed = json.loads(content)
                if "caption" in parsed and isinstance(parsed["caption"], str) and parsed["caption"].strip().startswith("{"):
                    inner_parsed = json.loads(parsed["caption"])
                    draft_posts[platform] = inner_parsed.get("caption", content)
                elif "caption" in parsed:
                    draft_posts[platform] = parsed["caption"]
            except Exception:
                pass

    print(
        f"DEBUG after_human — "
        f"human_approved: {state.get('human_approved')}, "
        f"regenerate: {state.get('regenerate')}, "
        f"platform: {state.get('regenerate_platform')}"
    )

    if state.get("human_approved"):
        return "finalize"

    if state.get("regenerate"):
        if state.get("retry_count", 0) >= 3:
            return "end"
        return state.get("regenerate_platform") or "twitter"

    return "end"

def build_graph():
    graph = StateGraph(GraphState)

    # Base Nodes
    graph.add_node("rag_node",            rag_agent.retrieve)
    graph.add_node("supervisor_node",     supervisor_agent.supervisor)
    graph.add_node("research_node",       research_agent.research)
    graph.add_node("twitter_node",        twitter_agent.generate)
    graph.add_node("instagram_node",      instagram_agent.generate)
    graph.add_node("linkedin_node",       linkedin_agent.linkedin_generate)
    graph.add_node("reviewer_node",       reviewer_agent.review)
    graph.add_node("human_approval_node", human_approval_agent.approve)
    graph.add_node("finalize_node",       finalize_posts_node) 
    graph.add_node("publisher_node",      publisher_agent.publish)


    graph.set_entry_point("rag_node")
    graph.add_edge("rag_node",        "supervisor_node")
    graph.add_edge("supervisor_node", "research_node")
    
    graph.add_edge("research_node",  "twitter_node")
    graph.add_edge("research_node",  "instagram_node")
    graph.add_edge("research_node",  "linkedin_node")
    
    graph.add_edge("twitter_node",   "reviewer_node")
    graph.add_edge("instagram_node", "reviewer_node")
    graph.add_edge("linkedin_node",  "reviewer_node")

    graph.add_conditional_edges(
        "reviewer_node",
        after_reviewer,
        {
            "human_approval": "human_approval_node",
            "twitter": "twitter_node",
            "instagram": "instagram_node",
            "linkedin": "linkedin_node",
        }
    )

    graph.add_conditional_edges(
        "human_approval_node",
        after_human,
        {
            "finalize": "finalize_node",
            "twitter": "twitter_node",
            "instagram": "instagram_node",
            "linkedin": "linkedin_node",
            "end": END
        }
    )

    graph.add_edge("finalize_node", "publisher_node")
    graph.add_edge("publisher_node", END)

    checkpointer = MemorySaver()

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_approval_node"]
    )

app = build_graph()