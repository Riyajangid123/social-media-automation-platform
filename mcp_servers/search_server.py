from fastmcp import FastMCP
from tavily import TavilyClient
from dotenv import load_dotenv
import re
import os

load_dotenv()

mcp    = FastMCP("research-server")
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

COMPETITORS = ["hootsuite", "buffer", "sprout social"]

def filter_competitors(results):
    return [
        r for r in results
        if not any(c in r.get("content", "").lower() for c in COMPETITORS)
    ]

def extract_hashtags(results,max_count=5):
    all_tags = []
    for r in results:
        tags = re.findall(r'#\w+', r.get("content", ""))
        all_tags.extend(tags)
    return list(set(all_tags))[:max_count]

@mcp.tool
def search_trending_topics(query:str,platform:str) -> str:
    """Search for trending topics on a specific social media platform"""
    results = tavily.search(
        query=f"trending {query} on {platform} 2025",
        max_results=7
    )["results"]

    filtered = filter_competitors(results)
    output   = "\n\n".join([
        f"- {r['title']}: {r['content'][:200]}"
        for r in filtered[:5]
    ])
    return output

@mcp.tool
def find_hashtags(topic: str, max_hashtags: int = 5) -> str:
    """Find the best hashtags for a given topic"""
    results  = tavily.search(
        query=f"best hashtags {topic} social media 2025",
        max_results=5
    )["results"]

    hashtags = extract_hashtags(results, max_hashtags)

    if len(hashtags) < 3:
        words    = topic.split()
        hashtags = [f"#{w.lower()}" for w in words] + hashtags
        hashtags = list(set(hashtags))[:max_hashtags]

    return f"Recommended hashtags: {' '.join(hashtags)}"

@mcp.tool()
def get_latest_news(topic: str) -> str:
    """Get latest news about a topic"""
    results  = tavily.search(
        query=f"latest news {topic} 2025",
        max_results=5
    )["results"]

    filtered = filter_competitors(results)
    output   = "\n\n".join([
        f"- {r['title']}: {r['content'][:200]}"
        for r in filtered[:3]
    ])
    return output

@mcp.tool()
def full_research(query: str, platform: str) -> str:
    """Do complete research — trends, hashtags, and news in one call"""
    trending = tavily.search(
        query=f"trending {query} {platform} 2025",
        max_results=5
    )["results"]

    hashtag_results = tavily.search(
        query=f"best hashtags {query} 2025",
        max_results=3
    )["results"]

    news = tavily.search(
        query=f"latest news {query} 2025",
        max_results=3
    )["results"]

    filtered_trending = filter_competitors(trending)[:3]
    hashtags          = extract_hashtags(hashtag_results, 5)
    filtered_news     = filter_competitors(news)[:2]

    output = f"""
        TRENDING TOPICS:
        {chr(10).join([f"- {r['title']}" for r in filtered_trending])}

        HASHTAGS:
        {' '.join(hashtags)}

        LATEST NEWS:
        {chr(10).join([f"- {r['title']}" for r in filtered_news])}
            """
    
    return output.strip()

if __name__ == "__main__":
    mcp.run()

