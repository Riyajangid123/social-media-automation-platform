import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from api.main import app

client = TestClient(app)

@pytest.fixture
def mock_graph_and_queries(mocker):
    """Mocks asynchronous LangGraph application methods and database queries."""
    mock_graph = mocker.patch("api.routes.posts.graph_app")
    mock_get_scheduled = mocker.patch("api.routes.posts.get_pending_scheduled_posts")
    return {"graph": mock_graph, "get_scheduled": mock_get_scheduled}

@pytest.mark.asyncio
async def test_generate_post_complete_workflow(mock_graph_and_queries):
    """Tests the /posts/generate flow when the graph runs smoothly to completion."""

    async def mock_astream(*args, **kwargs):
        yield {"some_node": "output_data"}

    mock_graph_and_queries["graph"].astream = mock_astream

    mock_state = MagicMock()
    mock_state.values = {
        "human_review_needed": False,
        "draft_posts": {"twitter": "Hello World!"},
        "publish_results": {"twitter": "success"},
        "final_output": "All posts published successfully."
    }
    mock_state.next = None
    
    mock_graph_and_queries["graph"].aget_state = AsyncMock(return_value=mock_state)

    payload = {
        "user_id": 1,
        "user_query": "Write a tweet about tech trends",
        "target_platforms": ["twitter"],
        "campaign_id": None,
        "schedule_time": None
    }
    
    response = client.post("/posts/generate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "complete"
    assert data["draft_posts"] == {"twitter": "Hello World!"}
    assert data["publish_results"] == {"twitter": "success"}

@pytest.mark.asyncio
async def test_generate_post_interrupt_awaits_approval(mock_graph_and_queries):
    """Verifies that an internal workflow interruption yields a pending status."""
    async def mock_astream_interrupt(*args, **kwargs):
        yield {"__interrupt__": "human_checkpoint"}

    mock_graph_and_queries["graph"].astream = mock_astream_interrupt

    mock_state = MagicMock()
    mock_state.values = {"draft_posts": {"twitter": "Draft requiring review"}}
    mock_graph_and_queries["graph"].aget_state = AsyncMock(return_value=mock_state)

    payload = {
        "user_id": 1,
        "user_query": "Write a high-risk prompt",
        "target_platforms": ["twitter"],
        "campaign_id": None,
        "schedule_time": None
    }

    response = client.post("/posts/generate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "pending_approval"
    assert "Waiting for human approval" in data["final_output"]

@pytest.mark.asyncio
async def test_approve_post_action(mock_graph_and_queries):
    """Tests resuming a human-in-the-loop agentic workflow via the approval gate."""
    async def mock_astream_resume(*args, **kwargs):
        yield {"supervisor": "resumed_work"}

    mock_graph_and_queries["graph"].astream = mock_astream_resume

    mock_state = MagicMock()
    mock_state.values = {
        "publish_results": {"twitter": "scheduled_id_999"},
        "final_output": "Post approved and moved to queue."
    }
    mock_graph_and_queries["graph"].aget_state = AsyncMock(return_value=mock_state)

    response = client.post("/posts/approve?user_id=1&choice=approve")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "complete"
    assert data["publish_results"] == {"twitter": "scheduled_id_999"}

def test_approve_post_invalid_choice_throws_error():
    """Ensures the server rejects invalid review choices immediately before executing graphs."""
    response = client.post("/posts/approve?user_id=1&choice=invalid_action_type")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid choice"

def test_get_scheduled_endpoint(mock_graph_and_queries):
    """Verifies retrieval of currently scheduled database content logs."""
    mock_graph_and_queries["get_scheduled"].return_value = [{"id": 1, "text": "Scheduled item"}]

    response = client.get("/posts/scheduled")
    assert response.status_code == 200
    assert "scheduled_posts" in response.json()
    assert len(response.json()["scheduled_posts"]) == 1