import requests
from groq import Groq

class FacebookReelAnalyzer:
    def __init__(self, access_token: str, page_id: str):
        self.access_token = access_token
        self.page_id = page_id
        self.groq_client = Groq()
        self.base_url = "https://graph.instagram.com/v18.0"
    
    def fetch_trending_reels(self) -> list:
        """Facebook-ээс trending reels авах"""
        url = f"{self.base_url}/{self.page_id}/media"
        params = {
            "fields": "id,caption,media_type,like_count,comments_count,timestamp",
            "access_token": self.access_token,
            "media_type": "VIDEO"  # Reels = videos
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(f"Error fetching reels: {e}")
            return []
    
    def analyze_reel_performance(self, reels: list) -> dict:
        """Reels үзүүлэлт анализ"""
        analysis = {
            "total_reels": len(reels),
            "avg_likes": 0,
            "avg_comments": 0,
            "top_reels": [],
            "trends": []
        }
        
        if not reels:
            return analysis
        
        likes = [r.get("like_count", 0) for r in reels]
        comments = [r.get("comments_count", 0) for r in reels]
        
        analysis["avg_likes"] = sum(likes) / len(likes)
        analysis["avg_comments"] = sum(comments) / len(comments)
        analysis["top_reels"] = sorted(reels, key=lambda x: x.get("like_count", 0), reverse=True)[:5]
        
        return analysis
    
    def analyze_with_ai(self, reel_data: dict) -> str:
        """AI-р reels анализ хийх"""
        prompt = f"""
        Analyze these Facebook Reels performance data:
        
        Total Reels: {reel_data['total_reels']}
        Average Likes: {reel_data['avg_likes']:.0f}
        Average Comments: {reel_data['avg_comments']:.0f}
        
        Top performing reels:
        {str(reel_data['top_reels'])}
        
        Provide:
        1. Key insights
        2. What makes reels successful
        3. Recommendations for new content
        4. Trending patterns
        
        Хариулт монгол хэлээр өг.
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
