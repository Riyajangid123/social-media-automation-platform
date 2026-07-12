from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from graph.state import GraphState
from database.queries import save_generated_post
from dotenv import load_dotenv
import json
import os

load_dotenv()

class TwitterAgent:
    def __init__(self):
        self.model = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
                You are an expert Twitter/X content writer for a professional brand.

                STRICT RULES:
                - Each tweet max 280 characters
                - Max 5 hashtags total across entire thread
                - Tone: professional but approachable
                - Never mention competitors
                - Make it engaging and shareable
                - Use trending topics naturally
                - Write in first person brand voice
                - No generic AI phrases like
                  "groundbreaking" or "revolutionizing"
                - EVERY regeneration must be completely different
                  from previous attempts — different angle,
                  different hook, different structure

                THREAD RULES:
                - First tweet must hook the reader and end with 
                - Number tweets from 1/ onwards after first tweet
                - Last tweet must have call to action + hashtags
                - Each tweet must flow naturally to the next
                - Middle tweets must each have ONE clear point

                OUTPUT FORMAT:
                Return ONLY valid JSON. No explanation. No markdown.
                {{
                    "type": "thread",
                    "tweets": [
                        "Hook tweet here ",
                        "1/ First point here...",
                        "2/ Second point here...",
                        "Final tweet with CTA and hashtags #tag1 #tag2"
                    ]
                }}
            """),
            ("human", """
                Write a Twitter thread about: {user_query}

                Brand voice — write exactly like these past posts:
                {rag_docs}

                Trending topics to reference naturally:
                {trending_topics}

                Hashtags to use (max 5 total):
                {hashtags}

                This is attempt number: {retry_count}
                {regenerate_instruction}

                Target audience: professionals and business owners

                Remember:
                - Sound like the brand not like an AI
                - Each tweet must standalone but connect to next
                - Hook must make people want to read the whole thread
                - MUST be completely different from any previous version
            """)
        ])

        self.chain = self.prompt | self.model

    def _extract_text_safely(self, item) -> str:
        """Extracts plain text from strings, lists, dicts, or LangChain Document objects."""
        if item is None:
            return ""
        
        if hasattr(item, "page_content"):
            return str(item.page_content)
        
        if isinstance(item, dict):
            if "page_content" in item:
                return str(item["page_content"])
            if "text" in item:
                return str(item["text"])
            return json.dumps(item)
            
        if isinstance(item, list):
            return " ".join([self._extract_text_safely(sub_item) for sub_item in item])
            
        return str(item)

    def _prepare_list_for_join(self, state_value) -> list:
        """Converts any mixture of inputs into a reliable list of clean strings."""
        if not state_value:
            return []
        if not isinstance(state_value, list):
            state_value = [state_value]
            
        return [self._extract_text_safely(element) for element in state_value if element]

    def generate(self, state: GraphState):
        retry_count = state.get("retry_count", 0)
        
        if retry_count > 0:
            regenerate_instruction = f"""
                IMPORTANT: This is regeneration attempt {retry_count}.
                Write a COMPLETELY DIFFERENT thread:
                - Use a different hook angle
                - Use a different structure
                - Cover different aspects of the topic
                - Do NOT repeat previous content
            """
        else:
            regenerate_instruction = ""

        safe_rag_docs = "\n".join(self._prepare_list_for_join(state.get("rag_docs", [])))
        safe_trending_topics = "\n".join(self._prepare_list_for_join(state.get("trending_topics", [])))
        safe_hashtags = " ".join(self._prepare_list_for_join(state.get("hashtags", [])))

        response = self.chain.invoke({
            "user_query":             state["user_query"],
            "rag_docs":               safe_rag_docs,
            "trending_topics":        safe_trending_topics,
            "hashtags":               safe_hashtags,
            "retry_count":            retry_count,
            "regenerate_instruction": regenerate_instruction
        })

        raw = response.content.strip()

        try:
            parsed = json.loads(raw)
            tweets = parsed.get("tweets", [])
            print(f"Generated thread with {len(tweets)} tweets")
            for i, t in enumerate(tweets):
                print(f"  Tweet {i+1} ({len(t)} chars): {t[:60]}...")
        except json.JSONDecodeError:
            print("JSON parse failed — using as single tweet")
            tweets = [raw[:280]]

        post_id = save_generated_post(
            user_id=state["user_id"],
            platform="twitter",
            topic=state["user_query"],
            caption=json.dumps(tweets),
            hashtags=[],
            retry_count=retry_count
        )
        print(f"Saved post to DB with id: {post_id}")

        return {
            "draft_posts": {"twitter": json.dumps(tweets)},
            "last_saved_post_id": post_id 
        }