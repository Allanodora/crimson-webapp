#!/usr/bin/env python3
"""
Orchestrates scraping sources, scores content, and emits 5 TrendStage topics.
Supports LIVE/CACHED/HISTORICAL modes and optional TrendStage per-story output.
"""

from pathlib import Path
import json
import sys
import os
from datetime import datetime
import time

# Add pipeline root to path
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

MIN_SCORE = getattr(CONFIG, "MIN_SCORE", 70)
STORIES_PER_SESSION = getattr(CONFIG, "STORIES_PER_SESSION", 5)
OUTPUT_DIR = Path(getattr(CONFIG, "OUTPUT_DIR", "output"))
TRENDSTAGE_TOPICS_PATH = getattr(CONFIG, "TRENDSTAGE_TOPICS_PATH", "")
PIPELINE_MODE = getattr(CONFIG, "PIPELINE_MODE", "LIVE")
SCHEDULE_INTERVAL = getattr(CONFIG, "SCHEDULE_INTERVAL", 300)

# Import fetchers
try:
    from source_fetchers.google_trends import fetch_trending as fetch_google
except Exception:
    fetch_google = lambda: []

try:
    from source_fetchers.bbc_sport import fetch_premier_league_news as fetch_bbc
except Exception:
    fetch_bbc = lambda: []

# Import scorer
try:
    from scoring.content_scorer import ContentScorer
except Exception:

    class ContentScorer:
        def score(self, content):
            return {
                "content": content,
                "score": 0,
                "flags": [],
                "breakdown": {},
                "verdict": "FAIL",
            }


def get_all_sources():
    """Gather content from all sources based on mode."""
    items = []

    if PIPELINE_MODE == "LIVE":
        for src in (fetch_google(), fetch_bbc()):
            if isinstance(src, list):
                items.extend(src)
            elif isinstance(src, dict):
                items.append(src)
    else:
        items = load_cached()

    return items


def load_cached():
    """Load cached content for CACHED/HISTORICAL modes."""
    cached_path = OUTPUT_DIR / "cached_content.json"
    if cached_path.exists():
        with cached_path.open() as f:
            return json.load(f)
    return []


def save_cached(items):
    """Save fetched content for caching."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cached_path = OUTPUT_DIR / "cached_content.json"
    with cached_path.open("w") as f:
        json.dump(items, f, indent=2)


def to_topic(entry, score_entry, index):
    """Convert scored content to TrendStage topic format."""
    title = entry.get("title", "Untitled")
    source = entry.get("source", "")
    url = entry.get("url", "")
    category = entry.get("category", "general")
    score = score_entry.get("score", 0)

    flags = score_entry.get("flags", [])
    notes = []
    if "debatable" in flags:
        notes.append("Debatable topic - audience will have opinions")
    if "has_stats" in flags:
        notes.append("Key stat: includes numbers/data - use in graph")
    if "emotional" in flags:
        notes.append("Emotional trigger - play up the drama")
    if "pundit_quote" in flags:
        notes.append("Pundit involved - quote them directly")
    if "core_topic" in flags:
        notes.append("Chelsea/PL relevant - your audience cares")
    if "trending" in flags:
        notes.append("Trending now - freshness matters")
    if not notes:
        notes.append("Review and add your take")

    topic = {
        "name": title,
        "meta": {"category": category, "source": source, "score": score, "views": 0},
        "graph": {
            "states": ["full", "highlight", "zoom", "compare"],
            "data": {
                "full": {
                    "label": "Overview",
                    "type": "line",
                    "data": {
                        "labels": ["Start", "Mid", "End"],
                        "datasets": [{"label": "Trend", "data": [1, 3, 2]}],
                    },
                },
                "highlight": {
                    "label": "Key Point",
                    "type": "bar",
                    "data": {
                        "labels": ["Metric"],
                        "datasets": [{"label": "Value", "data": [75]}],
                    },
                },
                "zoom": {
                    "label": "Deep Dive",
                    "type": "bar",
                    "data": {
                        "labels": ["A", "B", "C"],
                        "datasets": [{"data": [20, 35, 45]}],
                    },
                },
                "compare": {
                    "label": "Compare",
                    "type": "bar",
                    "data": {
                        "labels": ["This", "Last"],
                        "datasets": [{"data": [75, 60]}],
                    },
                },
            },
        },
        "media": {
            "type": "article",
            "title": title,
            "description": entry.get("description", ""),
            "thumbnail": entry.get("thumbnail", "https://picsum.photos/800/450"),
            "publisher": source,
            "url": url,
            "published_at": entry.get("timestamp", ""),
        },
        "reactions": [],
        "source": {"title": source, "url": url, "author": "", "verified": True},
        "speakerNotes": notes,
    }
    return topic


def write_topics_to_trendstage(topics):
    """Write each topic as separate JSON file for TrendStage."""
    if not TRENDSTAGE_TOPICS_PATH:
        return

    topics_dir = Path(TRENDSTAGE_TOPICS_PATH)
    topics_dir.mkdir(parents=True, exist_ok=True)

    for f in topics_dir.glob("topic_*.json"):
        f.unlink()

    index = {"topics": []}

    for i, topic in enumerate(topics):
        safe_name = "".join(c if c.isalnum() else "_" for c in topic["name"][:30])
        filename = f"topic_{i + 1:02d}_{safe_name}.json"
        filepath = topics_dir / filename

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(topic, f, indent=2)

        index["topics"].append(filename)

    with (topics_dir / "index.json").open("w") as f:
        json.dump(index, f, indent=2)

    print(f"Wrote {len(topics)} topics to {topics_dir}")


def run_pipeline():
    """Run one iteration of the pipeline."""
    print(
        f"\n[{datetime.now().strftime('%H:%M:%S')}] Running pipeline in {PIPELINE_MODE} mode..."
    )

    items = get_all_sources()
    print(f"Fetched {len(items)} items from sources")

    if PIPELINE_MODE == "LIVE" and items:
        save_cached(items)

    if not items:
        print("No content fetched. Check sources.")
        return []

    scorer = ContentScorer()
    scored = []

    for it in items:
        content = {
            "title": it.get("title", ""),
            "description": it.get("description", ""),
            "source": it.get("source", ""),
            "timestamp": it.get("timestamp", datetime.now().isoformat()),
            "url": it.get("url", ""),
            "category": it.get("category", "general"),
            "has_graph": it.get("has_graph", False),
            "has_image": it.get("has_image", False),
            "engagement": it.get(
                "engagement", {"likes": 0, "shares": 0, "comments": 0}
            ),
        }
        score_res = scorer.score(content)
        score_res.update({"original": it})
        scored.append(score_res)

    scored = [
        s
        for s in scored
        if s.get("verdict") == "PASS" or s.get("score", 0) >= MIN_SCORE
    ]
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    top5 = scored[:STORIES_PER_SESSION]

    print(f"Top {len(top5)} stories by score:")
    for i, s in enumerate(top5):
        print(
            f"  {i + 1}. [{s.get('score')}] {s.get('original', {}).get('title', 'Untitled')[:50]}"
        )

    topics = []
    for i, s in enumerate(top5):
        entry = s.get("original", {})
        topic = to_topic(entry, s, i)
        topics.append(topic)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = (
        OUTPUT_DIR / f"top5_topics_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    )
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "topics": topics,
                "mode": PIPELINE_MODE,
                "timestamp": datetime.now().isoformat(),
            },
            f,
            indent=2,
        )

    print(f"Saved to {out_path}")

    if TRENDSTAGE_TOPICS_PATH:
        write_topics_to_trendstage(topics)

    return topics


def main():
    """Main entry point with mode switching."""
    global PIPELINE_MODE

    mode = os.environ.get("PIPELINE_MODE", PIPELINE_MODE)
    PIPELINE_MODE = mode

    if len(sys.argv) > 1:
        if sys.argv[1] == "--live":
            PIPELINE_MODE = "LIVE"
        elif sys.argv[1] == "--cached":
            PIPELINE_MODE = "CACHED"
        elif sys.argv[1] == "--historical":
            PIPELINE_MODE = "HISTORICAL"
        elif sys.argv[1] == "--loop":
            print(
                f"Starting continuous loop (interval: {SCHEDULE_INTERVAL}s, Ctrl+C to stop)"
            )
            while True:
                run_pipeline()
                time.sleep(SCHEDULE_INTERVAL)

    run_pipeline()


if __name__ == "__main__":
    main()
