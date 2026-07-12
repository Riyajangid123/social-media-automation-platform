from graph.state import GraphState
import json

class ReviewerAgent:

    def _safe_parse(self, raw):
        """
        Returns (parsed_data, normalized_string)
        parsed_data  → Python object (list or dict) for checking
        normalized   → JSON string safe to store in approved_posts
        """

        if isinstance(raw, list):
            return raw, json.dumps(raw)

        if isinstance(raw, dict):
            return raw, json.dumps(raw)

        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                return parsed, raw  
            except json.JSONDecodeError:
                return raw, raw     

        
        return str(raw), str(raw)

    def _check_competitors(self, text: str) -> list:
        competitors = ["hootsuite", "buffer", "sprout social"]
        return [
            f"Mentions competitor: {c}"
            for c in competitors
            if c in text.lower()
        ]

    def review(self, state: GraphState):
        draft_posts    = state.get("draft_posts", {})
        approved_posts = {}
        review_issues  = {}


        if "twitter" in draft_posts:
            parsed, normalized = self._safe_parse(draft_posts["twitter"])
            issues = []

            if isinstance(parsed, list):
                tweets = [str(t) for t in parsed]
            elif isinstance(parsed, str):
                tweets = [parsed]
            else:
                tweets = [str(parsed)]

           
            for i, tweet in enumerate(tweets):
                if len(tweet) > 280:
                    issues.append(
                        f"Tweet {i+1} too long ({len(tweet)}/280 chars)"
                    )

            
            all_text = " ".join(tweets)
            if all_text.count("#") > 5:
                issues.append("Too many hashtags (max 5)")

        
            issues.extend(self._check_competitors(all_text))

            print(f"Twitter: {len(tweets)} tweets, issues: {issues or 'none'}")

            if issues:
                review_issues["twitter"] = issues
            else:
                approved_posts["twitter"] = normalized

    
        if "linkedin" in draft_posts:
            parsed, normalized = self._safe_parse(draft_posts["linkedin"])
            issues = []


            if isinstance(parsed, dict):
                caption  = str(parsed.get("caption", ""))
                hashtags = parsed.get("hashtags", [])
                if not isinstance(hashtags, list):
                    hashtags = []
                full_text = f"{caption} {' '.join(str(h) for h in hashtags)}"
            else:
                caption   = str(parsed)
                full_text = caption

            if len(caption) > 3000:
                issues.append(
                    f"Post too long ({len(caption)}/3000 chars)"
                )

            issues.extend(self._check_competitors(full_text))

            print(f"LinkedIn: {len(caption)} chars, issues: {issues or 'none'}")

            if issues:
                review_issues["linkedin"] = issues
            else:
                approved_posts["linkedin"] = normalized


        if review_issues:
            print(f"Review failed: {review_issues}")
            return {
                "human_review_needed": True,
                "approved_posts":      approved_posts,
                "review_issues":       review_issues
            }

        print("All reviews passed!")
        return {
            "human_review_needed": False,
            "approved_posts":      approved_posts,
            "review_issues":       {}
        }