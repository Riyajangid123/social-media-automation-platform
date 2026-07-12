from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from graph.state import GraphState
import os

load_dotenv()

class SupervisorAgent:

    def __init__(self):
        self.model = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
                You are a social media automation supervisor.

                Your job:
                1. Read the user goal and context provided
                2. Break it into a JSON task list
                3. Assign each task to the correct agent:
                   research_agent, reviewer_agent,publisher_agent
                4. Each task must include: agent, action, platform,
                   priority, depends_on

                Brand rules:
                - Tone: professional but approachable
                - Never post about competitors
                - Max hashtags: 5 per post

                Respond ONLY with valid JSON. No explanation.
            """),
            ("human", """
                User goal: {user_query}

                Relevant brand context:
                {rag_docs}

                Now produce the JSON task list.
            """)
        ])

        self.chain = self.prompt | self.model

    def supervisor(self, state: GraphState):

        rag_docs = state.get("rag_docs", [])

        response = self.chain.invoke({
            "user_query": state["user_query"],
            "rag_docs":   "\n".join(rag_docs)
        })

        return {
            "task_list": response.content
        }