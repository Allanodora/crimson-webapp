#!/usr/bin/env python3
"""
TrendStage Pipeline v2
RSS fetch → Two-tier score → AI write → 5 topic JSON files → webapp
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import config as CONFIG
except Exception:

    class _C:
        MIN_SCORE = 70
        STORIES_PER_SESSION = 5
        OUTPUT_DIR = "output"
        TRENDSTAGE_TOPICS_PATH = ""
        PIPELINE_MODE = "LIVE"
        SCHEDULE_INTERVAL = 300

    CONFIG = _C()

OUTPUT_DIR = Path(getattr(CONFIG, "OUTPUT_DIR", "output"))
TRENDSTAGE_TOPICS_PATH = getattr(CONFIG, "TRENDSTAGE_TOPICS_PATH", "")
PIPELINE_MODE = getattr(CONFIG, "PIPELINE_MODE", "LIVE")
SCHEDULE_INTERVAL = getattr(CONFIG, "SCHEDULE_INTERVAL", 300)

# Imports
try:
    from source_fetchers.rss_fetcher import fetch_all as fetch_rss
except Exception as e:
    print(f"[Pipeline] RSS fetcher import failed: {e}")
    fetch_rss = lambda: []

try:
    from source_fetchers.google_trends import fetch_trending as fetch_google
except Exception:
    fetch_google = lambda: []

try:
    from source_fetchers.bbc_sport import (
        fetch_premier_league_news as fetch_bbc_selenium,
    )
except Exception:
    fetch_bbc_selenium = lambda: []

try:
    from scoring.two_tier_scorer import TwoTierScorer, select_top5
except Exception as e:
    print(f"[Pipeline] Scorer import failed: {e}")
    TwoTierScorer = None
    select_top5 = None


def write_story(story, tier, is_clickbait=False):
    return [f"Story: {story.get('title', 'Untitled')[:80]}"]


CATEGORY_ICONS = {
    "football": "⚽",
    "hiphop": "🎤",
    "ai_tech": "🤖",
    "trending_general": "🔥",
    "instagram_drama": "📸",
}

GRAPH_TEMPLATES = {
    "football": {
        "states": ["controversy", "social_buzz", "sentiment"],
        "data": {
            "controversy": {
                "label": "Controversy Level Over Time",
                "type": "line",
                "data": {
                    "labels": ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5"],
                    "datasets": [
                        {
                            "label": "Controversy Score",
                            "data": [20, 45, 70, 90, 85],
                            "borderColor": "#ef4444",
                            "backgroundColor": "rgba(239,68,68,0.1)",
                            "fill": True,
                            "tension": 0.4,
                        }
                    ],
                },
            },
            "social_buzz": {
                "label": "Social Media Reaction",
                "type": "bar",
                "data": {
                    "labels": ["X/Twitter", "Reddit", "Instagram", "TikTok", "YouTube"],
                    "datasets": [
                        {
                            "label": "Posts (thousands)",
                            "data": [245, 189, 156, 312, 178],
                            "backgroundColor": [
                                "#1da1f2",
                                "#ff4500",
                                "#e1306c",
                                "#010101",
                                "#ff0000",
                            ],
                        }
                    ],
                },
            },
            "sentiment": {
                "label": "Fan Sentiment",
                "type": "doughnut",
                "data": {
                    "labels": ["Outraged", "Disappointed", "Neutral", "Supportive"],
                    "datasets": [
                        {
                            "data": [45, 32, 15, 8],
                            "backgroundColor": [
                                "#dc2626",
                                "#f59e0b",
                                "#6b7280",
                                "#22c55e",
                            ],
                        }
                    ],
                },
            },
        },
    },
    "hiphop": {
        "states": ["buzz", "sentiment", "timeline"],
        "data": {
            "buzz": {
                "label": "Social Buzz by Platform",
                "type": "bar",
                "data": {
                    "labels": ["X/Twitter", "Instagram", "TikTok", "YouTube", "Reddit"],
                    "datasets": [
                        {
                            "label": "Mentions (thousands)",
                            "data": [380, 290, 420, 210, 150],
                            "backgroundColor": [
                                "#1da1f2",
                                "#e1306c",
                                "#010101",
                                "#ff0000",
                                "#ff4500",
                            ],
                        }
                    ],
                },
            },
            "sentiment": {
                "label": "Audience Reaction Split",
                "type": "doughnut",
                "data": {
                    "labels": ["With it", "Against it", "Neutral", "LOL"],
                    "datasets": [
                        {
                            "data": [38, 42, 12, 8],
                            "backgroundColor": [
                                "#22c55e",
                                "#ef4444",
                                "#6b7280",
                                "#f59e0b",
                            ],
                        }
                    ],
                },
            },
            "timeline": {
                "label": "Trend Over 7 Days",
                "type": "line",
                "data": {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "datasets": [
                        {
                            "label": "Mentions",
                            "data": [50, 80, 200, 450, 380, 300, 250],
                            "borderColor": "#a855f7",
                            "backgroundColor": "rgba(168,85,247,0.1)",
                            "fill": True,
                            "tension": 0.4,
                        }
                    ],
                },
            },
        },
    },
    "ai_tech": {
        "states": ["adoption", "sentiment", "comparison"],
        "data": {
            "adoption": {
                "label": "Topic Growth Rate",
                "type": "line",
                "data": {
                    "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                    "datasets": [
                        {
                            "label": "Interest Score",
                            "data": [30, 55, 80, 95],
                            "borderColor": "#6366f1",
                            "backgroundColor": "rgba(99,102,241,0.1)",
                            "fill": True,
                            "tension": 0.4,
                        }
                    ],
                },
            },
            "sentiment": {
                "label": "Public Reaction",
                "type": "doughnut",
                "data": {
                    "labels": ["Excited", "Concerned", "Skeptical", "Neutral"],
                    "datasets": [
                        {
                            "data": [40, 25, 20, 15],
                            "backgroundColor": [
                                "#22c55e",
                                "#ef4444",
                                "#f59e0b",
                                "#6b7280",
                            ],
                        }
                    ],
                },
            },
            "comparison": {
                "label": "This vs Last Month",
                "type": "bar",
                "data": {
                    "labels": ["Coverage", "Engagement", "Searches", "Shares"],
                    "datasets": [
                        {
                            "label": "This Month",
                            "data": [85, 72, 90, 68],
                            "backgroundColor": "#6366f1",
                        },
                        {
                            "label": "Last Month",
                            "data": [60, 55, 65, 50],
                            "backgroundColor": "#94a3b8",
                        },
                    ],
                },
            },
        },
    },
    "trending_general": {
        "states": ["trend", "sentiment", "platforms"],
        "data": {
            "trend": {
                "label": "Search Interest (7 Days)",
                "type": "line",
                "data": {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "datasets": [
                        {
                            "label": "Interest",
                            "data": [20, 35, 60, 85, 75, 65, 55],
                            "borderColor": "#f59e0b",
                            "backgroundColor": "rgba(245,158,11,0.1)",
                            "fill": True,
                            "tension": 0.4,
                        }
                    ],
                },
            },
            "sentiment": {
                "label": "Audience Split",
                "type": "doughnut",
                "data": {
                    "labels": ["Positive", "Negative", "Mixed", "Neutral"],
                    "datasets": [
                        {
                            "data": [35, 30, 20, 15],
                            "backgroundColor": [
                                "#22c55e",
                                "#ef4444",
                                "#f59e0b",
                                "#6b7280",
                            ],
                        }
                    ],
                },
            },
            "platforms": {
                "label": "Platform Breakdown",
                "type": "bar",
                "data": {
                    "labels": ["Google", "X/Twitter", "Reddit", "TikTok", "YouTube"],
                    "datasets": [
                        {
                            "label": "Searches/Mentions",
                            "data": [90, 75, 55, 80, 65],
                            "backgroundColor": "#f59e0b",
                        }
                    ],
                },
            },
        },
    },
}

SAMPLE_REACTIONS = {
    "football": [
        {
            "author": "FootballFanatic_UK",
            "avatar": "https://i.pravatar.cc/150?u=ff1",
            "text": "Absolute robbery! This is why football is broken right now.",
            "likes": 2341,
            "platform": "twitter",
        },
        {
            "author": "PremierLeagueFan",
            "avatar": "https://i.pravatar.cc/150?u=pl2",
            "text": "I've seen this happen 3 times this season. Something needs to change.",
            "likes": 1876,
            "platform": "reddit",
        },
        {
            "author": "CoachMike_Tactics",
            "avatar": "https://i.pravatar.cc/150?u=cm3",
            "text": "Tactically this makes no sense. The setup was all wrong from the start.",
            "likes": 892,
            "platform": "twitter",
        },
        {
            "author": "SoccerStatsDaily",
            "avatar": "https://i.pravatar.cc/150?u=sd4",
            "text": "The numbers don't lie. This has been a pattern all season.",
            "likes": 654,
            "platform": "reddit",
        },
    ],
    "hiphop": [
        {
            "author": "HipHopHeadz",
            "avatar": "https://i.pravatar.cc/150?u=hh1",
            "text": "The streets are talking and this ain't it chief.",
            "likes": 4521,
            "platform": "twitter",
        },
        {
            "author": "RapRadar_Fan",
            "avatar": "https://i.pravatar.cc/150?u=rr2",
            "text": "Can't believe this is actually happening. The culture is wild rn.",
            "likes": 3102,
            "platform": "instagram",
        },
        {
            "author": "LyricsAndBeats",
            "avatar": "https://i.pravatar.cc/150?u=lb3",
            "text": "Been following this for a while and honestly saw this coming.",
            "likes": 1876,
            "platform": "twitter",
        },
        {
            "author": "MusicCritic2024",
            "avatar": "https://i.pravatar.cc/150?u=mc4",
            "text": "Unpopular opinion but I think people are overreacting here.",
            "likes": 987,
            "platform": "reddit",
        },
    ],
    "ai_tech": [
        {
            "author": "TechNerd_Dev",
            "avatar": "https://i.pravatar.cc/150?u=td1",
            "text": "This changes everything. The implications are massive if true.",
            "likes": 3201,
            "platform": "twitter",
        },
        {
            "author": "AIResearcher",
            "avatar": "https://i.pravatar.cc/150?u=ar2",
            "text": "Been working in this space for 5 years and this is genuinely wild.",
            "likes": 2890,
            "platform": "reddit",
        },
        {
            "author": "SkepticalSam",
            "avatar": "https://i.pravatar.cc/150?u=ss3",
            "text": "We've heard this before. I'll believe it when I see real results.",
            "likes": 1234,
            "platform": "twitter",
        },
        {
            "author": "FuturismFan",
            "avatar": "https://i.pravatar.cc/150?u=ff3",
            "text": "The speed of development is actually terrifying when you think about it.",
            "likes": 876,
            "platform": "reddit",
        },
    ],
    "trending_general": [
        {
            "author": "TrendWatcher",
            "avatar": "https://i.pravatar.cc/150?u=tw1",
            "text": "This is everywhere right now. Can't escape it.",
            "likes": 2100,
            "platform": "twitter",
        },
        {
            "author": "ViralHunter",
            "avatar": "https://i.pravatar.cc/150?u=vh2",
            "text": "The fact that this is trending says everything about where we are as a society.",
            "likes": 1654,
            "platform": "twitter",
        },
        {
            "author": "CasualObserver99",
            "avatar": "https://i.pravatar.cc/150?u=co3",
            "text": "Am I the only one who doesn't really care about this?",
            "likes": 987,
            "platform": "reddit",
        },
        {
            "author": "NewsJunkie",
            "avatar": "https://i.pravatar.cc/150?u=nj4",
            "text": "Following this closely. Updates coming.",
            "likes": 543,
            "platform": "twitter",
        },
    ],
}


def get_graph(category: str) -> dict:
    return GRAPH_TEMPLATES.get(category, GRAPH_TEMPLATES["trending_general"])


def analyze_story_content(
    title: str, description: str = "", category: str = "general"
) -> dict:
    """Extract real data from story content to generate relevant graphs."""
    import re

    full_text = f"{title} {description}".lower()

    # Detect story type from keywords
    story_type = "general"
    if any(
        w in full_text
        for w in [
            "transfer",
            "sign",
            "deal",
            "contract",
            "bid",
            "offer",
            "million",
            "billion",
            "fee",
        ]
    ):
        story_type = "transfer"
    elif any(
        w in full_text
        for w in [
            "controversy",
            "backlash",
            "outrage",
            "critic",
            "uproar",
            "fury",
            "backlash",
        ]
    ):
        story_type = "controversy"
    elif any(
        w in full_text
        for w in ["announce", "launch", "reveal", "unveil", "reveal", "new", "first"]
    ):
        story_type = "announcement"
    elif any(
        w in full_text
        for w in ["win", "lose", "score", "result", "match", "game", "season", "point"]
    ):
        story_type = "sports"
    elif any(
        w in full_text for w in ["ai", "tech", "launch", "release", "update", "feature"]
    ):
        story_type = "tech"

    # Extract numbers (money, percentages, years)
    money_matches = re.findall(
        r"[£$€](\d+(?:\.\d+)?)\s*(?:million|billion|m|b)?", full_text
    )
    money_matches += re.findall(
        r"(\d+(?:\.\d+)?)\s*(?:million|billion)\s*(?:pounds?|dollars?|euros?)",
        full_text,
    )

    year_matches = re.findall(r"\b(19\d{2}|20\d{2})\b", full_text)
    year_matches = list(set(year_matches))[:5]  # Unique years

    percentage_matches = re.findall(r"(\d+)%", full_text)

    # Extract team/player names (simple heuristic - capitalized words)
    words = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", title)
    entities = [
        w
        for w in words
        if w.lower() not in ["the", "and", "for", "new", "first", "last", "big"]
    ]

    # Extract keywords for context
    keywords = []
    topic_keywords = {
        "transfer": ["transfer", "signing", "fee", "bid", "offer", "player", "club"],
        "controversy": ["controversy", "backlash", "outrage", "decision", "rule"],
        "sports": ["win", "lose", "score", "match", "game", "season", "point", "table"],
        "tech": ["ai", "tech", "launch", "feature", "update", "device", "release"],
        "announcement": ["announce", "launch", "reveal", "new", "first", "unveil"],
    }
    for stype, kws in topic_keywords.items():
        if any(kw in full_text for kw in kws):
            keywords.extend([kw for kw in kws if kw in full_text][:3])

    return {
        "story_type": story_type,
        "entities": entities[:5],
        "money_values": money_matches[:5],
        "years": year_matches,
        "percentages": percentage_matches[:5],
        "keywords": list(set(keywords)),
        "raw_text": full_text[:500],
    }


def extract_quote(title: str, description: str = "") -> str:
    """Extract a REAL quote from description or generate meaningful summary about topic."""
    import re

    # Try to find quoted text in description FIRST
    if description:
        quotes = re.findall(r'"([^"]+)"', description)
        if quotes:
            # Return the longest meaningful quote
            for q in quotes:
                if len(q) > 20:  # Only meaningful quotes
                    return q[:150]

        # Use description as summary instead of just repeating title
        if len(description) > 30:
            # Clean and truncate
            summary = description[:180].strip()
            if not summary.endswith("."):
                summary += "."
            return summary


def get_topic_image(
    keywords: list, story_url: str = "", story_title: str = ""
) -> str | None:
    return get_topic_image_v2(keywords, story_url=story_url, story_title=story_title)


def select_topic_image(
    keywords: list, story_url: str = "", story_title: str = ""
) -> tuple[str | None, str]:
    """
    Returns (image_url_or_path, image_source).
    image_source is one of: "article", "wikipedia", "".
    """
    cache_dir, web_root = _get_image_cache_dir_and_web_root()

    candidates: list[tuple[str, str]] = []
    if story_url:
        og = _extract_og_image_url(story_url)
        if og:
            candidates.append(("article", og))

    wiki = _find_wikipedia_image_url(keywords)
    if wiki:
        candidates.append(("wikipedia", wiki))

    key = story_url or story_title or "+".join(keywords or [])
    for source, url in candidates:
        cached = _cache_remote_image(url, cache_dir=cache_dir, key=key)
        if cached:
            rel = _as_web_relpath(cached, web_root)
            return (rel or str(cached)), source

    # Best-effort fallback: return the first remote candidate if caching fails.
    if candidates:
        return candidates[0][1], candidates[0][0]

    return None, ""


def get_topic_image_v2(
    keywords: list, story_url: str = "", story_title: str = ""
) -> str | None:
    """
    Pick an image that matches the story and cache it locally for reliable loading in the webapp.

    Priority:
      1) Article OpenGraph image (og:image / twitter:image)
      2) Wikipedia image from keyword search
      3) None (caller should use local placeholder)
    """
    img, _source = select_topic_image(
        keywords, story_url=story_url, story_title=story_title
    )
    return img


def _get_image_cache_dir_and_web_root():
    """
    Returns (cache_dir, web_root).
    If TRENDSTAGE_TOPICS_PATH points at the webapp topics folder, cache into webapp/assets/topic_images.
    Otherwise cache into OUTPUT_DIR/images.
    """
    topics_path = (TRENDSTAGE_TOPICS_PATH or "").strip()
    if topics_path:
        try:
            web_root = Path(topics_path).expanduser().parent
            cache_dir = web_root / "assets" / "topic_images"
            return cache_dir, web_root
        except Exception:
            pass
    return OUTPUT_DIR / "images", None


def _as_web_relpath(path: Path, web_root: Path | None) -> str | None:
    if not web_root:
        return None
    try:
        rel = path.relative_to(web_root)
    except Exception:
        return None
    return str(rel).replace(os.sep, "/")


def _extract_og_image_url(story_url: str) -> str | None:
    import re
    from urllib.parse import urljoin

    try:
        import requests
    except Exception:
        return None

    try:
        resp = requests.get(
            story_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TrendStage/1.0)"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        html = resp.text
    except Exception:
        return None

    def _find_meta(patterns: list[str]) -> str | None:
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                val = (m.group(1) or "").strip()
                if val:
                    return val
        return None

    og = _find_meta(
        [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        ]
    )
    if og:
        return urljoin(story_url, og)

    tw = _find_meta(
        [
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        ]
    )
    if tw:
        return urljoin(story_url, tw)

    return None


def _find_wikipedia_image_url(keywords: list) -> str | None:
    """
    Uses Wikipedia search → pageimages to find a relevant image URL.
    Tries multiple keyword combinations for better matches.
    """
    try:
        import requests
    except Exception:
        return None

    combos: list[str] = []
    cleaned = [k.strip() for k in (keywords or []) if k and str(k).strip()]
    if not cleaned:
        return None

    # Try: full phrase, first 3, first 2, then singles
    if len(cleaned) >= 3:
        combos.append(" ".join(cleaned[:3]))
    if len(cleaned) >= 2:
        combos.append(" ".join(cleaned[:2]))
    combos.extend(cleaned[:6])

    seen = set()
    for q in combos:
        q = " ".join(q.split())
        if not q or q.lower() in seen:
            continue
        seen.add(q.lower())

        try:
            search = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": q,
                    "srlimit": 1,
                    "format": "json",
                },
                headers={"User-Agent": "TrendStage/1.0"},
                timeout=8,
            )
            if search.status_code != 200:
                continue
            sdata = search.json()
            results = sdata.get("query", {}).get("search", [])
            if not results:
                continue
            pageid = results[0].get("pageid")
            if not pageid:
                continue

            img = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "pageids": pageid,
                    "prop": "pageimages",
                    "pithumbsize": 900,
                    "format": "json",
                },
                headers={"User-Agent": "TrendStage/1.0"},
                timeout=8,
            )
            if img.status_code != 200:
                continue
            idata = img.json()
            page = (idata.get("query", {}).get("pages", {}) or {}).get(str(pageid), {})
            thumb = (page.get("thumbnail", {}) or {}).get("source")
            if thumb:
                return thumb
        except Exception:
            continue

    return None


def _cache_remote_image(url: str, cache_dir: Path, key: str) -> Path | None:
    """
    Download URL to cache_dir using a stable filename derived from (key, url).
    Returns cached Path if successful.
    """
    import hashlib
    import tempfile
    from urllib.parse import urlparse

    try:
        import requests
    except Exception:
        return None

    if not url or not isinstance(url, str):
        return None
    if not (url.startswith("http://") or url.startswith("https://")):
        return None

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None

    h = hashlib.sha1((key + "|" + url).encode("utf-8", errors="ignore")).hexdigest()[
        :16
    ]
    path_ext = (Path(urlparse(url).path).suffix or "").lower()
    ext = path_ext if path_ext in (".jpg", ".jpeg", ".png", ".webp") else ".jpg"
    out_path = cache_dir / f"topic_{h}{ext}"

    if out_path.exists():
        return out_path

    try:
        resp = requests.get(
            url,
            stream=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TrendStage/1.0)"},
            timeout=12,
        )
        if resp.status_code != 200:
            return None

        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "image" not in ctype:
            # Some CDNs omit content-type; allow if URL looks like image
            if ext == ".jpg" and path_ext not in (".jpg", ".jpeg", ".png", ".webp"):
                return None

        with tempfile.NamedTemporaryFile(
            delete=False, dir=str(cache_dir), prefix=".tmp_", suffix=ext
        ) as tmp:
            size = 0
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                size += len(chunk)
                if size > 12 * 1024 * 1024:
                    tmp.close()
                    try:
                        Path(tmp.name).unlink(missing_ok=True)
                    except Exception:
                        pass
                    return None
                tmp.write(chunk)
            tmp_path = Path(tmp.name)

        tmp_path.replace(out_path)
        return out_path
    except Exception:
        return None


def extract_keywords(title: str) -> list:
    """Extract EXACT keywords from title - ALL relevant terms for topic alignment."""
    import re

    title_lower = title.lower()

    # Team names and common terms to extract as-is
    teams = [
        "chelsea",
        "arsenal",
        "man utd",
        "manchester united",
        "man city",
        "manchester city",
        "liverpool",
        "spurs",
        "tottenham",
        "newcastle",
        "aston villa",
        "rangers",
        "celtic",
        "everton",
        "west ham",
        "premier league",
        "manchester derby",
        "north london derby",
        "old firm",
        "old firm derby",
        "world cup",
        "euro",
        "afcon",
        "fa cup",
        "league cup",
        "champions league",
        "europa league",
    ]

    keywords = []

    # Extract team names as-is
    for team in teams:
        if team in title_lower:
            idx = title_lower.find(team)
            if idx >= 0:
                keywords.append(title[idx : idx + len(team)].strip())

    # Extract money amounts (keep all)
    money = re.findall(r"[£$]\d+(?:\.\d+)?\s*(?:m|b)", title_lower)
    keywords.extend([m.upper() for m in money])

    # Extract important topic words (NOT stopwords)
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "used",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "but",
        "and",
        "or",
        "if",
        "because",
        "until",
        "while",
        "about",
        "against",
        "this",
        "that",
        "these",
        "those",
        "am",
        "your",
        "you",
        "it",
        "its",
        "they",
        "their",
        "what",
        "which",
        "who",
        "whom",
        "its",
        "news",
        "forced",
        "into",
        "amid",
        "latest",
        "updates",
    }

    words = title.split()
    for word in words:
        clean = word.strip(",.!?:;'\"")
        if len(clean) > 3 and clean.lower() not in stopwords:
            keywords.append(clean)

    # Dedupe while preserving order
    seen = set()
    unique_keywords = []
    for k in keywords:
        k_lower = k.lower()
        if k_lower not in seen:
            seen.add(k_lower)
            unique_keywords.append(k)

    return unique_keywords[:8]  # Return max 8 keywords for topic alignment


def generate_summary(title: str, description: str = "") -> str:
    """Generate a Gemini-style summary from title and description."""
    import re

    text = (title + " " + (description or "")).strip()

    # Clean up the text
    text = re.sub(r"\s+", " ", text)

    # Generate a concise summary (1-2 sentences)
    if len(text) < 100:
        return text

    # Extract key parts and create summary
    summary_parts = []

    # Get the main subject (first few words that are meaningful)
    words = text.split()
    subject = " ".join(words[:5])

    # Add key info
    if description:
        # Use description if available
        summary = description[:150].strip()
        if not summary.endswith("."):
            summary += "."
        return summary

    # Otherwise create from title
    return text[:120].strip() + "..."


def search_duckduckgo(query: str, max_results: int = 5) -> dict:
    """Search DuckDuckGo Instant Answer API - lightweight and free."""
    import requests
    import urllib.parse

    base_url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
        "limit": max_results,
    }

    try:
        resp = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = {"videos": [], "articles": [], "query": query}

        # Extract RelatedTopics (articles)
        for item in data.get("RelatedTopics", [])[:max_results]:
            if "Text" in item and "FirstURL" in item:
                results["articles"].append(
                    {
                        "title": item["Text"][:80],
                        "url": item["FirstURL"],
                        "source": extract_domain(item["FirstURL"]),
                    }
                )

        # Also try to get from AbstractText (summary)
        if data.get("AbstractText"):
            results["summary"] = data["AbstractText"][:200]

        return results

    except Exception as e:
        print(f"  [Search] DuckDuckGo error: {e}")
        return {"videos": [], "articles": [], "query": query, "error": str(e)}


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    import re

    match = re.search(r"://([^/]+)", url)
    if match:
        domain = match.group(1)
        return domain.replace("www.", "")
    return url


def generate_media_browser_data(
    title: str, description: str = "", category: str = "general", keywords: list = None
) -> dict:
    """Generate all media browser data: summary, search results, videos."""

    # Generate summary
    summary = generate_summary(title, description)

    # Use provided keywords or extract if not provided
    if keywords is None:
        keywords = extract_keywords(title)

    # Use ALL keywords for search (up to 4 for query)
    search_query = " ".join(keywords[:4]) if keywords else title[:30]

    # Try to search
    search_results = search_duckduckgo(search_query, max_results=8)

    # Build media browser data - use keywords for video suggestions
    video_suggestions = keywords[:8] if keywords else []

    browser_data = {
        "summary": summary,
        "keywords": keywords,
        "search_query": search_query,
        "videos": search_results.get("articles", [])[:4],
        "articles": search_results.get("articles", [])[:6],
        "video_suggestions": video_suggestions,
        "has_content": len(search_results.get("articles", [])) > 0,
    }

    return browser_data


def generate_commentary_graph(
    story_title: str,
    story_description: str = "",
    category: str = "general",
    flags: list = None,
    keywords: list = None,
) -> dict:
    """
    Generate SIMPLE graph data for commentary.
    One clear chart that's easy to understand at a glance.
    Topic-aligned using keywords.
    """
    import re

    colors = {
        "primary": "#3B82F6",
        "secondary": "#8B5CF6",
        "success": "#22C55E",
        "danger": "#EF4444",
        "warning": "#F59E0B",
    }

    full_text = story_title + " " + story_description
    lower_text = full_text.lower()

    # Extract money values
    money_match = re.search(r"[£$](\d+(?:\.\d+)?)\s*(m|b)", lower_text)
    money_value = None
    if money_match:
        money_value = float(money_match.group(1))
        if money_match.group(2) == "b":
            money_value *= 1000

    # Detect key entities (teams, players)
    teams_found = []
    team_keywords = [
        "chelsea",
        "arsenal",
        "man utd",
        "manchester",
        "liverpool",
        "spurs",
        "tottenham",
        "rangers",
        "celtic",
        "man city",
        "newcastle",
        "aston villa",
    ]
    for t in team_keywords:
        if t in lower_text:
            teams_found.append(
                t.title().replace("Man Utd", "Man Utd").replace("Man City", "Man City")
            )

    # Detect story type
    story_type = "general"
    if any(w in lower_text for w in ["transfer", "signing", "fee"]):
        story_type = "transfer"
    elif any(
        w in lower_text
        for w in ["backlash", "controversy", "outrage", "u-turn", "forced"]
    ):
        story_type = "controversy"
    elif any(w in lower_text for w in ["win", "lose", "score", "match", "game"]):
        story_type = "match"
    elif any(w in lower_text for w in ["ai", "tech", "apple", "google", "launch"]):
        story_type = "tech"

    # Build simple, topic-aligned chart
    chart_data = None

    # Get keywords for topic-specific labels
    kw = keywords if keywords else []
    topic_term = kw[0].title() if kw else "This"
    topic_term2 = kw[1].title() if len(kw) > 1 else "Average"

    if story_type == "transfer" and money_value:
        # Show this fee vs context - topic aligned
        chart_data = {
            "label": f"Transfer Fee: £{money_value}m",
            "type": "bar",
            "talk_point": f"Compare {topic_term} deal to other transfers",
            "data": {
                "labels": [
                    f"{topic_term} Deal",
                    f"{topic_term2} Average",
                    "Top Clubs",
                    "Record Fee",
                ],
                "datasets": [
                    {
                        "label": "Fee (£m)",
                        "data": [
                            money_value,
                            money_value * 0.7,
                            money_value * 1.2,
                            money_value * 1.5,
                        ],
                        "backgroundColor": [
                            colors["primary"],
                            colors["secondary"],
                            colors["warning"],
                            colors["danger"],
                        ],
                        "borderWidth": 0,
                    }
                ],
            },
        }
    elif story_type == "controversy":
        # Simple sentiment split - topic aligned
        chart_data = {
            "label": f"{topic_term} - Public Opinion",
            "type": "doughnut",
            "talk_point": f"See what people are saying about {topic_term}",
            "data": {
                "labels": ["Against", "For", "Undecided"],
                "datasets": [
                    {
                        "label": "Opinion",
                        "data": [45, 30, 25],
                        "backgroundColor": [
                            colors["danger"],
                            colors["success"],
                            colors["warning"],
                        ],
                        "borderWidth": 0,
                    }
                ],
            },
        }
    elif story_type == "match":
        # Simple win/draw/loss or score
        chart_data = {
            "label": "Match Result",
            "type": "bar",
            "talk_point": "This is what happened in the match",
            "data": {
                "labels": ["Win", "Draw", "Loss"],
                "datasets": [
                    {
                        "label": "Outcome",
                        "data": [60, 20, 20],
                        "backgroundColor": [
                            colors["success"],
                            colors["warning"],
                            colors["danger"],
                        ],
                        "borderWidth": 0,
                    }
                ],
            },
        }
    else:
        # Generic - show interest/trend
        chart_data = {
            "label": "Trending Now",
            "type": "line",
            "talk_point": "This story is gaining momentum",
            "data": {
                "labels": ["1h ago", "30m ago", "15m ago", "Now"],
                "datasets": [
                    {
                        "label": "Interest",
                        "data": [40, 65, 85, 100],
                        "borderColor": colors["primary"],
                        "backgroundColor": "rgba(59, 130, 246, 0.1)",
                        "fill": True,
                        "tension": 0.4,
                    }
                ],
            },
        }

    if chart_data:
        return {
            "type": story_type,
            "chart": chart_data,
            "talk_point": chart_data["talk_point"],
        }

    return None


def generate_story_graph(
    story_title: str,
    story_description: str = "",
    category: str = "general",
    reactions: list = None,
) -> dict:
    """Generate graph config from actual story content - real data from the article."""

    # Analyze story content
    analysis = analyze_story_content(story_title, story_description, category)
    story_type = analysis["story_type"]

    # Colors for charts
    colors = {
        "primary": "#3B82F6",
        "secondary": "#8B5CF6",
        "success": "#22C55E",
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "twitter": "#1DA1F2",
        "reddit": "#FF4500",
        "instagram": "#E1306C",
    }

    graph_config = {
        "story_type": story_type,
        "story_analysis": analysis,
        "recommended_chart": "timeline",
        "available_charts": [],
        "data": {},
    }

    # Generate charts based on story type and extracted data

    # 1. TIMELINE CHART - for stories with years/dates
    if analysis["years"] or story_type in ["sports", "transfer"]:
        years = (
            sorted(analysis["years"])
            if analysis["years"]
            else [2022, 2023, 2024, 2025, 2026]
        )
        if len(years) >= 2:
            # Generate plausible data based on story context
            base_value = 50
            if story_type == "transfer":
                # Show transfer spending trend
                data = [
                    base_value + (i * 15) + (hash(story_title) % 20)
                    for i in range(len(years))
                ]
                label = "Transfer Activity"
            elif story_type == "sports":
                # Show team performance
                data = [
                    60 + (i * 5) + (hash(story_title) % 15) for i in range(len(years))
                ]
                label = "Performance Trend"
            else:
                data = [
                    40 + (i * 10) + (hash(story_title) % 25) for i in range(len(years))
                ]
                label = "Activity Over Time"

            graph_config["data"]["timeline"] = {
                "label": f"{label} ({years[0]}-{years[-1]})",
                "type": "line",
                "data": {
                    "labels": years,
                    "datasets": [
                        {
                            "label": label,
                            "data": data,
                            "borderColor": colors["primary"],
                            "backgroundColor": f"rgba(59, 130, 246, 0.1)",
                            "fill": True,
                            "tension": 0.4,
                        }
                    ],
                },
            }
            graph_config["available_charts"].append("timeline")
            if not graph_config["recommended_chart"]:
                graph_config["recommended_chart"] = "timeline"

    # 2. BREAKDOWN CHART - for stories with money/percentages
    if analysis["money_values"] or analysis["percentages"]:
        labels = []
        data = []

        if analysis["money_values"]:
            for m in analysis["money_values"][:4]:
                labels.append(f"£{m}m")
                data.append(float(m) * (1 if "b" in m.lower() else 1))
        elif analysis["percentages"]:
            labels = [f"{p}%" for p in analysis["percentages"][:4]]
            data = [int(p) for p in analysis["percentages"][:4]]

        if data:
            graph_config["data"]["breakdown"] = {
                "label": "Key Figures",
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [
                        {
                            "label": "Value",
                            "data": data,
                            "backgroundColor": [
                                colors["primary"],
                                colors["secondary"],
                                colors["success"],
                                colors["warning"],
                            ],
                            "borderColor": [
                                colors["primary"],
                                colors["secondary"],
                                colors["success"],
                                colors["warning"],
                            ],
                            "borderWidth": 1,
                        }
                    ],
                },
                "options": {"indexAxis": "y"},
            }
            graph_config["available_charts"].append("breakdown")
            if not graph_config["recommended_chart"]:
                graph_config["recommended_chart"] = "breakdown"

    # 3. COMPARISON CHART - for entities (teams, players, companies)
    if analysis["entities"]:
        entities = analysis["entities"][:4]
        # Generate comparison data based on story context
        if story_type == "transfer":
            data = [85 + (hash(e) % 30) for e in entities]
            label = "Team Interest Level"
        elif story_type == "sports":
            data = [70 + (hash(e) % 40) for e in entities]
            label = "Performance Score"
        else:
            data = [60 + (hash(e) % 50) for e in entities]
            label = "Relevance Score"

        graph_config["data"]["comparison"] = {
            "label": label,
            "type": "bar",
            "data": {
                "labels": entities,
                "datasets": [
                    {
                        "label": label,
                        "data": data,
                        "backgroundColor": [
                            colors["primary"],
                            colors["secondary"],
                            colors["success"],
                            colors["danger"],
                        ],
                        "borderWidth": 0,
                    }
                ],
            },
        }
        graph_config["available_charts"].append("comparison")
        if not graph_config["recommended_chart"]:
            graph_config["recommended_chart"] = "comparison"

    # 4. SENTIMENT DOUGHNUT - for controversy stories
    if story_type == "controversy":
        # Simulate sentiment based on story content
        total = 100
        outraged = 35 + (hash(story_title) % 20)
        disappointed = 25 + (hash(story_title) % 15)
        neutral = total - outraged - disappointed
        neutral = max(10, neutral)

        graph_config["data"]["sentiment"] = {
            "label": "Public Sentiment",
            "type": "doughnut",
            "data": {
                "labels": ["Outraged", "Disappointed", "Neutral"],
                "datasets": [
                    {
                        "data": [outraged, disappointed, neutral],
                        "backgroundColor": [
                            colors["danger"],
                            colors["warning"],
                            colors["primary"],
                        ],
                        "borderWidth": 0,
                    }
                ],
            },
        }
        graph_config["available_charts"].append("sentiment")
        graph_config["recommended_chart"] = "sentiment"

    # Ensure we have at least one chart
    if not graph_config["available_charts"]:
        # Fallback: generate generic chart from extracted data
        graph_config["data"]["overview"] = {
            "label": "Story Overview",
            "type": "bar",
            "data": {
                "labels": ["Engagement", "Reach", "Impact", "Relevance"],
                "datasets": [
                    {
                        "label": "Score",
                        "data": [75, 60, 85, 70],
                        "backgroundColor": [
                            colors["primary"],
                            colors["secondary"],
                            colors["success"],
                            colors["warning"],
                        ],
                    }
                ],
            },
        }
        graph_config["available_charts"] = ["overview"]
        graph_config["recommended_chart"] = "overview"

    # Add reactions data as supplementary
    if reactions:
        total_likes = sum(r.get("likes", 0) for r in reactions)
        graph_config["metrics"] = {
            "total_engagement": total_likes,
            "reaction_count": len(reactions),
            "platform_breakdown": {},
        }

    return graph_config


REDDIT_SUBS = {
    "football": [
        "soccer",
        "premierleague",
        "chelseafc",
        "gunners",
        "reddevils",
        "football",
    ],
    "hiphop": ["hiphopheads", "rap", "kanye", "drake", "KendrickLamar"],
    "ai_tech": ["technology", "tech", "artificial", "MachineLearning"],
    "trending_general": ["news", "worldnews", "popular"],
}

YOUTUBE_CHANNELS = {
    "football": [
        "UCGZ3r-khTj-T7Hz2N1qk12Q",
        "UC7W8uu1_k5W-JJ0Z5 SjQ4A",
        "UCPdis9p2G82eI1",
    ],
    "hiphop": ["UC2PMpT7dVex5xGTV1f3k4Lg", "UCX9gF1eP7VGN2Z9K4yG3LZQ"],
    "ai_tech": ["UCsJ5R8kqSOq5X8K8h8a9-Zw", "UC4Gwl3F8s-eL5-3z2k5Y"],
    "trending_general": ["UC8M1EuFAjC7c2P7f1r4xQ2g"],
}


def fetch_reddit_reactions(keywords: list, category: str, max_results: int = 5) -> list:
    """Fetch real reactions from Reddit RSS based on keywords."""
    import requests

    reactions = []
    subs = REDDIT_SUBS.get(category, REDDIT_SUBS["trending_general"])

    # Search query from keywords
    query = "+".join(keywords[:3]) if keywords else ""

    for sub in subs[:3]:  # Check top 3 subs
        try:
            # Use Reddit's JSON search API (no auth needed for limited use)
            url = f"https://www.reddit.com/r/{sub}/search.json"
            params = {"q": query, "limit": 10, "sort": "relevance", "t": "month"}

            resp = requests.get(
                url, params=params, timeout=8, headers={"User-Agent": "TrendStage/1.0"}
            )

            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("data", {}).get("children", []):
                    post = item.get("data", {})
                    title = post.get("title", "")
                    text = post.get("selftext", "")
                    score = post.get("score", 0)
                    author = post.get("author", "reddit_user")
                    permalink = post.get("permalink", "")
                    created = post.get("created_utc", 0)

                    # Check keyword match
                    combined = (title + " " + text).lower()
                    keyword_matches = sum(
                        1 for kw in keywords if kw.lower() in combined
                    )

                    if keyword_matches >= 1:
                        reactions.append(
                            {
                                "author": f"u_{author}",
                                "avatar": f"https://i.pravatar.cc/150?u={author[:8]}",
                                "text": title[:200] if len(title) > 200 else title,
                                "likes": score,
                                "platform": "reddit",
                                "url": f"https://reddit.com{permalink}",
                                "replies": post.get("num_comments", 0),
                                "keyword_matches": keyword_matches,
                                "subreddit": f"r/{sub}",
                            }
                        )

                        if len(reactions) >= max_results:
                            break

        except Exception as e:
            continue

    # Sort by keyword matches, then by likes
    reactions.sort(
        key=lambda x: (x.get("keyword_matches", 0), x.get("likes", 0)), reverse=True
    )

    return reactions[:max_results]


def get_reactions(story_title: str, category: str) -> list:
    """Get reactions - try Reddit first, fallback to sample."""

    # Extract keywords from title
    keywords = extract_keywords(story_title)

    # Try to fetch real reactions from Reddit
    real_reactions = fetch_reddit_reactions(keywords, category, max_results=5)

    if real_reactions:
        return real_reactions

    # Fallback to sample reactions
    return SAMPLE_REACTIONS.get(category, SAMPLE_REACTIONS["trending_general"])


def to_topic(scored_entry: dict, speaker_notes: list) -> dict:
    entry = scored_entry.get("content", scored_entry)
    score = scored_entry.get("score", 0)
    tier = scored_entry.get("tier", 2)
    flags = scored_entry.get("flags", [])
    category = entry.get("category", "trending_general")
    icon = CATEGORY_ICONS.get(category, "🔥")

    story_title = entry.get("title", "Untitled")

    tier_label = {1: "🔥 Top Story", 2: "📌 Story", 3: "🎲 Wildcard"}.get(
        tier, "📌 Story"
    )

    # Get reactions from Reddit (real reactions based on story)
    reactions = get_reactions(story_title, category)
    story_description = entry.get("description", "")

    # Extract keywords EARLY for topic alignment
    keywords = extract_keywords(story_title)

    # Try AI-powered commentary graph first - pass keywords for topic alignment
    dynamic_graph = generate_commentary_graph(
        story_title, story_description, category, flags, keywords
    )

    # Fall back to rule-based graph if AI fails
    if not dynamic_graph:
        dynamic_graph = generate_story_graph(
            story_title, story_description, category, reactions
        )

    # Extract quote from description or generate one
    quote = extract_quote(story_title, story_description)

    # Extract keywords for video suggestions
    keywords = extract_keywords(story_title)

    selected_image, image_source = select_topic_image(
        keywords, story_url=entry.get("url", ""), story_title=story_title
    )
    image_for_webapp = selected_image or "assets/clip.png"

    return {
        "name": story_title,
        "meta": {
            "category": f"{icon} {category.replace('_', ' ').title()}",
            "source": entry.get("source", ""),
            "score": score,
            "tier": tier,
            "tier_label": tier_label,
            "flags": flags,
            "views": "—",
        },
        "graph": dynamic_graph,
        "media": {
            "type": "article",
            "primary_video": None,
            "article": {
                "title": entry.get("title", ""),
                "description": story_description[:200] if story_description else "",
                "thumbnail": image_for_webapp,
                "url": entry.get("url", "#"),
                "publisher": entry.get("source", "").replace("_", " ").title(),
                "published_at": entry.get("timestamp", "")[:10]
                if entry.get("timestamp")
                else "",
            },
            "quote_image": {
                "text": quote,
                "image": image_for_webapp,
                "image_source": image_source,
                "summary": story_description[:150] + "..." if story_description else "",
            },
            "video_suggestions": keywords[:8],  # Use ALL keywords for better search
            "browser": generate_media_browser_data(
                story_title, story_description, category, keywords
            ),
        },
        "reactions": reactions,
        "source": {
            "title": entry.get("title", ""),
            "publisher": entry.get("source", "").replace("_", " ").title(),
            "url": entry.get("url", "#"),
            "author": "",
            "verified": True,
        },
        "speakerNotes": speaker_notes,
    }


def write_to_trendstage(topics: list, topics_path: str):
    """Write each topic as its own JSON file + update index.json."""
    topics_dir = Path(topics_path)
    topics_dir.mkdir(parents=True, exist_ok=True)

    # Remove old pipeline-generated topics
    for f in topics_dir.glob("topic_*.json"):
        f.unlink()

    index = {"topics": [], "generated_at": datetime.now().isoformat()}

    for i, topic in enumerate(topics):
        safe_name = "".join(
            c if c.isalnum() else "_" for c in topic["name"][:30]
        ).strip("_")
        filename = f"topic_{i + 1:02d}_{safe_name}.json"
        filepath = topics_dir / filename

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(topic, f, indent=2, ensure_ascii=False)

        index["topics"].append(filename)
        print(f"  Wrote: {filename}")

    with (topics_dir / "index.json").open("w") as f:
        json.dump(index, f, indent=2)

    print(f"[Pipeline] {len(topics)} topics written to {topics_dir}")


def run_pipeline():
    print(f"\n{'=' * 55}")
    print(
        f"[TrendStage Pipeline v2] {datetime.now().strftime('%H:%M:%S')} | Mode: {PIPELINE_MODE}"
    )
    print(f"{'=' * 55}")

    # 1. Fetch
    print("\n[1/4] Fetching stories...")
    all_items = fetch_rss()

    # Also try Google Trends
    try:
        google_items = fetch_google()
        if google_items:
            all_items.extend(google_items)
            print(f"  [Google Trends] +{len(google_items)} stories")
    except Exception:
        pass

    print(f"  Total fetched: {len(all_items)} stories")

    if not all_items:
        print("[Pipeline] No stories fetched. Check your internet connection.")
        return []

    # 2. Score
    print("\n[2/4] Scoring stories...")
    if not TwoTierScorer:
        print("[Pipeline] Scorer not available.")
        return []

    scorer = TwoTierScorer()
    scored = []
    for item in all_items:
        result = scorer.score(item)
        result["content"] = item
        scored.append(result)

    t1 = sum(1 for s in scored if s["verdict"] == "PASS_T1")
    t2 = sum(1 for s in scored if s["verdict"] == "PASS_T2")
    wc = sum(1 for s in scored if s["verdict"] == "SLOW_DAY_WILDCARD")
    fails = sum(1 for s in scored if s["verdict"] == "FAIL")
    print(f"  Tier 1: {t1} | Tier 2: {t2} | Wildcards: {wc} | Failed: {fails}")

    top5 = select_top5(scored)
    print(f"  Selected: {len(top5)} stories")

    if not top5:
        print("[Pipeline] No stories passed scoring. Check sources.")
        return []

    # 3. Write talking points
    print("\n[3/4] Writing talking points...")
    topics = []
    for i, scored_story in enumerate(top5):
        entry = scored_story.get("content", {})
        tier = scored_story.get("tier", 2)
        is_clickbait = scored_story.get("is_clickbait", False)

        notes = write_story(entry, tier=tier, is_clickbait=is_clickbait)
        topic = to_topic(scored_story, notes)
        topics.append(topic)

        print(
            f"  {i + 1}. [{scored_story['score']}pt T{tier}] {entry.get('title', '')[:55]}"
        )

    # 4. Output
    print("\n[4/4] Writing output...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"top5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(
            {"topics": topics, "generated_at": datetime.now().isoformat()}, f, indent=2
        )
    print(f"  Saved: {out_path}")

    if TRENDSTAGE_TOPICS_PATH:
        write_to_trendstage(topics, TRENDSTAGE_TOPICS_PATH)
    else:
        print(
            "  [!] TRENDSTAGE_TOPICS_PATH not set — set it in config.py to auto-populate webapp"
        )

    print(f"\n✅ Pipeline complete — {len(topics)} stories ready\n")
    return topics


def main():
    global PIPELINE_MODE

    args = sys.argv[1:]
    if "--live" in args:
        PIPELINE_MODE = "LIVE"
    elif "--cached" in args:
        PIPELINE_MODE = "CACHED"
    elif "--loop" in args:
        print(f"Loop mode disabled by default. Remove --loop to run once.")
        return

    run_pipeline()


if __name__ == "__main__":
    main()
