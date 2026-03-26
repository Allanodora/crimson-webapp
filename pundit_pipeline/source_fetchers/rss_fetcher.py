"""
RSS Fetcher - Multi-source, no Selenium needed
Pulls from BBC Sport, Sky Sports, ESPN, HotNewHipHop, TechCrunch, The Verge, etc.
Fast, reliable, lots of stories.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEEDS = [
    # Football
    {
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "source": "bbc_sport",
        "category": "football",
        "core_boost": True,
    },
    # Backup football source (keeps pipeline consistent if a major feed is down)
    {
        "url": "https://www.theguardian.com/football/rss",
        "source": "guardian_football",
        "category": "football",
        "core_boost": True,
    },
    {
        "url": "https://www.skysports.com/rss/12040",
        "source": "sky_sports",
        "category": "football",
        "core_boost": True,
    },
    {
        "url": "https://www.espn.com/espn/rss/news",
        "source": "espn",
        "category": "football",
        "core_boost": True,
    },
    {
        "url": "https://www.mirror.co.uk/sport/football/rss.xml",
        "source": "mirror",
        "category": "football",
        "core_boost": True,
    },
    # Hip-hop / Culture
    {
        "url": "https://www.xxlmag.com/feed/",
        "source": "xxl",
        "category": "hiphop",
        "core_boost": False,
    },
    # Backup hip-hop source
    {
        "url": "https://www.hotnewhiphop.com/rss.xml",
        "source": "hotnewhiphop",
        "category": "hiphop",
        "core_boost": False,
    },
    # AI / Tech
    {
        "url": "https://techcrunch.com/feed/",
        "source": "techcrunch",
        "category": "ai_tech",
        "core_boost": False,
    },
    {
        "url": "https://www.theverge.com/rss/index.xml",
        "source": "the_verge",
        "category": "ai_tech",
        "core_boost": False,
    },
    {
        "url": "https://feeds.feedburner.com/venturebeat/SZYF",
        "source": "venturebeat",
        "category": "ai_tech",
        "core_boost": False,
    },
    {
        "url": "https://www.wired.com/feed/rss",
        "source": "wired",
        "category": "ai_tech",
        "core_boost": False,
    },
    {
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "source": "ars_technica",
        "category": "ai_tech",
        "core_boost": False,
    },
    # Backup tech source (very reliable RSS)
    {
        "url": "https://news.ycombinator.com/rss",
        "source": "hackernews",
        "category": "ai_tech",
        "core_boost": False,
    },
    # General Trending
    {
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
        "source": "bbc_news",
        "category": "trending_general",
        "core_boost": False,
    },
    {
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "source": "nytimes",
        "category": "trending_general",
        "core_boost": False,
    },
    # Backup general news source
    {
        "url": "https://feeds.npr.org/1001/rss.xml",
        "source": "npr",
        "category": "trending_general",
        "core_boost": False,
    },
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TrendStage/1.0)"}


def parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str).replace(tzinfo=None)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    except Exception:
        return None


def fetch_feed(feed_config: dict) -> list:
    stories = []
    url = feed_config["url"]

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()

        # Handle Atom vs RSS
        root = ET.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # Detect feed type
        is_atom = root.tag in ("{http://www.w3.org/2005/Atom}feed", "feed")

        if is_atom:
            items = root.findall("{http://www.w3.org/2005/Atom}entry")
        else:
            items = root.findall(".//item")

        for item in items[:20]:
            try:
                if is_atom:
                    title = (
                        item.findtext("{http://www.w3.org/2005/Atom}title") or ""
                    ).strip()
                    description = (
                        item.findtext("{http://www.w3.org/2005/Atom}summary") or ""
                    ).strip()
                    link_el = item.find("{http://www.w3.org/2005/Atom}link")
                    link = link_el.get("href", "") if link_el is not None else ""
                    pub_date = (
                        item.findtext("{http://www.w3.org/2005/Atom}updated") or ""
                    )
                else:
                    title = (item.findtext("title") or "").strip()
                    description = (item.findtext("description") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    pub_date = item.findtext("pubDate") or ""

                # Strip HTML from description
                import re

                description = re.sub(r"<[^>]+>", "", description).strip()[:400]

                if not title or len(title) < 8:
                    continue

                timestamp = parse_date(pub_date) or datetime.now()

                stories.append(
                    {
                        "title": title,
                        "description": description,
                        "source": feed_config["source"],
                        "category": feed_config["category"],
                        "timestamp": timestamp.isoformat(),
                        "url": link,
                        "has_graph": False,
                        "has_image": False,
                        "is_trending": False,
                        "core_relevant": feed_config.get("core_boost", False),
                        "engagement": {"likes": 0, "shares": 0, "comments": 0},
                    }
                )

            except Exception:
                continue

        print(f"  [{feed_config['source']}] {len(stories)} stories")

    except Exception as e:
        print(f"  [{feed_config['source']}] Failed: {e}")

    return stories


def fetch_all() -> list:
    """Fetch from all RSS feeds. Returns flat list of stories."""
    all_stories = []
    print(f"[RSS Fetcher] Pulling from {len(FEEDS)} sources...")

    for feed in FEEDS:
        stories = fetch_feed(feed)
        all_stories.extend(stories)

    # De-dupe by URL (some sources syndicate the same story)
    deduped = []
    seen_urls = set()
    for s in all_stories:
        u = (s.get("url") or "").strip()
        if u and u in seen_urls:
            continue
        if u:
            seen_urls.add(u)
        deduped.append(s)

    print(f"[RSS Fetcher] Total: {len(deduped)} stories fetched")
    return deduped


if __name__ == "__main__":
    results = fetch_all()
    print(f"\nSample stories:")
    for r in results[:8]:
        print(f"  [{r['category']}] {r['title'][:70]}")
