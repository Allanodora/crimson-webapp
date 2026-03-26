"""
Google Trends Fetcher
Fetches trending football/entertainment topics
"""

import requests
from datetime import datetime


def fetch_trending() -> list:
    """Fetch trending topics from Google Trends."""
    stories = []

    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=0)

        # Football-related keywords
        keywords = ["Premier League", "Chelsea FC", "VAR", "football transfers"]
        pytrends.build_payload(keywords, cat=20, timeframe="now 1-d")

        trending = pytrends.trending_searches(pn="united_states")

        for idx, row in trending.iterrows():
            stories.append(
                {
                    "title": row[0] if isinstance(row[0], str) else str(row[0]),
                    "description": f"Trending on Google: {row[0]}",
                    "source": "google_trends",
                    "category": "trending_general",
                    "timestamp": datetime.now().isoformat(),
                    "is_trending": True,
                    "has_graph": False,
                    "url": f"https://trends.google.com/trends/explore?q={row[0]}",
                }
            )

    except ImportError:
        print("[Google Trends] pytrends not installed, skipping")
    except Exception as e:
        print(f"[Google Trends] Error: {e}")

    return stories


def fetch_related_queries(topic: str) -> list:
    """Get related queries for a specific topic."""
    stories = []

    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=0)
        pytrends.build_payload([topic], timeframe="now 1-d")

        related = pytrends.related_queries()
        if topic in related and related[topic].get("rising") is not None:
            for _, row in related[topic]["rising"].iterrows():
                stories.append(
                    {
                        "title": f"{row['query']} (+{row['value']}%)",
                        "description": f"Rising search: {row['query']}",
                        "source": "google_trends",
                        "category": "trending_general",
                        "timestamp": datetime.now().isoformat(),
                        "is_trending": True,
                    }
                )

    except Exception as e:
        print(f"[Google Trends] Error fetching related queries: {e}")

    return stories


if __name__ == "__main__":
    results = fetch_trending()
    print(f"Found {len(results)} trending topics")
    for r in results[:5]:
        print(f"  - {r['title']}")
