from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from graph.state import GraphState
import os 
import json
from dotenv import load_dotenv

class LinkedInAgent:
    def __init__(self):
        self.model = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
                You are an expert LinkedIn content strategist and copywriter
                specializing in professional, high-engagement LinkedIn posts.

                STRICT RULES:
                - Write ONE LinkedIn post only.
                - Maximum 2500 characters.
                - Tone: professional, authentic, and conversational.
                - Write like an experienced industry expert.
                - Never sound like AI.
                - Never mention competitors.
                - Never use clickbait.
                - Never use excessive emojis (maximum 3).
                - Use short paragraphs for readability.
                - Include a strong hook in the first sentence.
                - Deliver practical value.
                - End with a question or call-to-action.
                - Use storytelling whenever appropriate.
                - Reference trending topics naturally.
                - Follow the provided brand voice exactly.
                - Every regeneration must be completely different:
                    • Different hook
                    • Different structure
                    • Different examples
                    • Different storytelling style
                    • Different CTA

                DO NOT USE GENERIC AI PHRASES LIKE:
                - Revolutionizing
                - Game-changing
                - Unlock the power
                - In today's fast-paced world
                - Dive into
                - Leverage AI
                - Cutting-edge
                - Next-generation

                OUTPUT FORMAT:
                Return ONLY valid JSON.
                No markdown.
                No explanation.

                OUTPUT FORMAT:

                {{
                    "type":"linkedin_post",
                    "caption":"Complete LinkedIn post...",
                    "hashtags":[
                        "#AI",
                        "#MachineLearning",
                        "#Automation"
                    ]
                }}
            """),

            ("human", """
                Create a LinkedIn post about:

                {user_query}

                Brand voice (follow exactly):

                {rag_docs}

                Trending topics:

                {trending_topics}

                Recommended hashtags:

                {hashtags}

                Attempt number:

                {retry_count}

                {regenerate_instruction}

                Target audience:
                Professionals, founders, executives, AI engineers, business leaders,
                startup owners, recruiters, and decision-makers.

                Objectives:
                - Educate the audience.
                - Build authority.
                - Encourage engagement.
                - Generate meaningful discussion.
                - Increase shares and comments.
                - Sound like a real human expert.

                Structure:
                1. Attention-grabbing opening.
                2. Explain the problem.
                3. Share insights or experience.
                4. Give practical takeaways.
                5. End with a thoughtful CTA or question.
                6. Add 3–5 relevant hashtags.

                Remember:
                - Do not sound robotic.
                - Do not repeat previous generations.
                - Write naturally.
                - Optimize for LinkedIn engagement.
            """)
            ])
        
        self.chain=self.prompt|self.model

    def linkedin_generate(self,state:GraphState):
        retry_count=state.get("retry_count",0)

        if retry_count>0:
            regenerate_instruction = (
                f"""
                This is regeneration attempt #{state.get('retry_count', 1)}.

                The previous version was rejected.

                Create a completely different LinkedIn post.

                Requirements:
                - Use a new opening hook.
                - Take a different perspective or angle.
                - Use different examples or storytelling.
                - Change the paragraph structure.
                - Use a different CTA.
                - Use different relevant hashtags.
                - Do NOT reuse sentences or phrases from previous attempts.
                - Keep the same topic and brand voice.
                """
            )

        else:
            regenerate_instruction=""

        response = self.chain.invoke({
            "user_query":             state["user_query"],
            "rag_docs":               "\n".join([str(d) for d in state.get("rag_docs", [])]),
            "hashtags":               " ".join([str(h) for h in state.get("hashtags", [])]),
            "trending_topics":        "\n".join([str(t) for t in state.get("trending_topics", [])]),
            "retry_count":            retry_count,
            "regenerate_instruction": regenerate_instruction
        })
        
        raw=response.content.strip()

        caption = ""
        hashtags = []

        try:
            parsed = json.loads(raw)

            caption = parsed.get("caption", "")
            hashtags = parsed.get("hashtags", [])

            final_post = caption

            if hashtags:
                final_post += "\n\n" + " ".join(hashtags)

            print(f"Generated LinkedIn post ({len(final_post)} characters)")
            print(final_post[:100] + "...")

        except json.JSONDecodeError:
            print("JSON parse failed — using raw output")
            caption = raw
            hashtags = []
            final_post = raw
            
        return {
            "draft_posts": {
                "linkedin": json.dumps({
                    "caption": caption,
                    "hashtags": hashtags
                })
            }
        }