from typing import TypedDict, List, Optional, Dict, Any,Annotated

def merge_dicts(existing: dict, new_updates: dict) -> dict:
    """Merges concurrent dictionary updates instead of overwriting them."""
    current = existing.copy() if existing else {}
    current.update(new_updates)
    return current

class GraphState(TypedDict):

    user_id:              int
    user_query:           str                    # "write a LinkedIn post about AI"
    target_platforms:     List[str]              # ["twitter", "linkedin"]
    campaign_id:          Optional[str]          # "q3-fintech-campaign"
    schedule_time:        Optional[str]          # "2024-01-15T09:00:00" or None

    # --- supervisor ---
    task_list:            List[Dict]             # [{agent, action, platform, priority}]
    current_step:         str                    # "research" | "content" | "publish"
    retry_count:          int                    # 0, 1, 2...
    error_log:            List[str]              # ["content_agent failed: ..."]

    # --- rag + memory ---
    rag_docs:             List[str]              # retrieved brand docs
    memory:               Dict[str, Any]         # last run state, scores, preferences
    brand_voice:          str                    # tone rules extracted from RAG
    past_post_examples:   List[str]              # high-performing post samples
    last_saved_post_id: Optional[int]

    # --- research agent ---
    trending_topics:      List[str]              # ["AI agents", "fintech 2025"]
    hashtags:             List[str]              # ["#AI", "#fintech"]
    competitor_posts:     List[str]              # what rivals posted recently

    # --- content agent ---
    draft_posts:          Annotated[Dict[str, str],merge_dicts]        # {"twitter": "...", "linkedin": "..."}
    post_variants:        Dict[str, List[str]]   # A/B options per platform
    generated_image_url:  Optional[str]          # image URL from DALL-E / Stability
    validation_passed:    bool                   # char limits, tone check passed        
    
    # --- human approval ---
    human_review_needed:  bool                   # True = pause for approval
    human_approved:       Optional[bool]            # True = approved, False = rejected
    regenerate:           Optional[bool]            # True = regenerate the post   
    regenerate_platforms: List[str] 

    # --- scheduler + publish ---
    approved_posts:       Dict[str, str]         # posts cleared to go live
    optimal_post_time:    Dict[str, str]         # {"twitter": "09:00", "linkedin": "11:00"}
    publish_results:      Dict[str, str]         # {"twitter": "post_id_123"}
    
    # --- analytics (feedback loop) ---
    performance_scores:       Dict[str, float]   # {"post_id_123": 0.87}
    best_performing_platform: Optional[str]      # "linkedin"
    analytics_report:         Optional[str]      # summary text shown to user
    final_output:             Optional[str]      # what the whole graph returns