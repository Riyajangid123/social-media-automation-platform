from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from graph.state import GraphState
from dotenv import load_dotenv
import json
import os

load_dotenv()

class ResearchAgent:
    def __init__(self):
        self.model = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )

    async def research(self, state: GraphState):

        client = MultiServerMCPClient({
            "research": {
                "command":   "python",
                "args":      ["mcp_servers/search_server.py"],
                "env":       {"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")},
                "transport": "stdio"
            }
        })

        tools = await client.get_tools()
        agent = create_react_agent(self.model, tools)

        result = await agent.ainvoke({
                "messages": [(
                    "human",
                    f"""
            Research for social media content.

            Topic: {state["user_query"]}
            Platforms: {state["target_platforms"]}

            Use the full_research tool.

            Return ONLY valid JSON.

            Example:

            {{
                "trending_topics": [
                    "...",
                    "..."
                ],
                "hashtags": [
                    "#AI",
                    "#MachineLearning"
                ]
            }}

            Do not include markdown.
            Do not include explanations.
            Do not include ```json.
            Only return the JSON object.
            """
                )]
            })

    

        output = result["messages"][-1].content
        print(result["messages"][-1].content)

        if isinstance(output, list):
            text = ""
            for item in output:
                if isinstance(item, dict):
                    text += item.get("text", "")
                elif isinstance(item, str):
                    text += item
            output = text


        data = json.loads(output)

        return {
            "trending_topics": data.get("trending_topics", []),
            "hashtags": data.get("hashtags", [])
        }