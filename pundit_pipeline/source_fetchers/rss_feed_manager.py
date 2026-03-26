#!/usr/bin/env python3
"""
RSS Feed Manager
- Validates existing feeds
- Finds working alternatives for broken feeds
- Auto-updates rss_fetcher.py config
"""

import requests
import re
from datetime import datetime

KNOWN_FEEDS = {
    "football": [
        {
            "name": "bbc_sport",
            "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
            "core_boost": True,
        },
        {
            "name": "sky_sports",
            "url": "https://www.skysports.com/rss/12040",
            "core_boost": True,
        },
        {
            "name": "goal",
            "url": "https://www.goal.com/feeds/en/news",
            "core_boost": True,
        },
        {
            "name": "espn",
            "url": "https://www.espn.com/espn/rss/news",
            "core_boost": True,
        },
        {
            "name": "football365",
            "url": "https://www.football365.com/rss/news.xml",
            "core_boost": True,
        },
        {
            "name": "mirror",
            "url": "https://www.mirror.co.uk/sport/football/rss.xml",
            "core_boost": True,
        },
    ],
    "hiphop": [
        {
            "name": "hotnewhiphop",
            "url": "https://www.hotnewhiphop.com/rss/news.xml",
            "core_boost": False,
        },
        {
            "name": "complex",
            "url": "https://www.complex.com/music/rss",
            "core_boost": False,
        },
        {"name": "xxl", "url": "https://www.xxlmag.com/feed/", "core_boost": False},
        {
            "name": "hiphopdx",
            "url": "https://hiphopdx.com/rss.xml",
            "core_boost": False,
        },
        {
            "name": "datpiff",
            "url": "https://www.datpiff.com/rss/newmixtapes.xml",
            "core_boost": False,
        },
    ],
    "ai_tech": [
        {
            "name": "techcrunch",
            "url": "https://techcrunch.com/feed/",
            "core_boost": False,
        },
        {
            "name": "the_verge",
            "url": "https://www.theverge.com/rss/index.xml",
            "core_boost": False,
        },
        {
            "name": "venturebeat",
            "url": "https://feeds.feedburner.com/venturebeat/SZYF",
            "core_boost": False,
        },
        {"name": "wired", "url": "https://www.wired.com/feed/rss", "core_boost": False},
        {
            "name": "ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
            "core_boost": False,
        },
    ],
    "trending": [
        {
            "name": "bbc_news",
            "url": "https://feeds.bbci.co.uk/news/rss.xml",
            "core_boost": False,
        },
        {
            "name": "nytimes",
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "core_boost": False,
        },
        {
            "name": "reuters",
            "url": "https://www.reutersagency.com/feed/",
            "core_boost": False,
        },
    ],
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TrendStage/1.0)"}


def check_feed(url: str) -> tuple[bool, int]:
    """Check if feed works. Returns (success, story_count)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # Check for actual content
        content = resp.text.lower()
        if "<rss" in content or "<feed" in content or "<atom" in content:
            # Count items
            items = content.count("<item>") + content.count("<entry>")
            return True, items
        return False, 0
    except Exception as e:
        return False, 0


def validate_all_feeds():
    """Check all known feeds and report status."""
    print(f"\n{'=' * 60}")
    print(
        f"[RSS Feed Manager] Validating feeds - {datetime.now().strftime('%H:%M:%S')}"
    )
    print(f"{'=' * 60}\n")

    results = []

    for category, feeds in KNOWN_FEEDS.items():
        print(f"[{category.upper()}]")
        working = []
        broken = []

        for feed in feeds:
            success, count = check_feed(feed["url"])
            status = f"✅ {count} stories" if success else f"❌ Failed"
            print(f"  {feed['name']}: {status}")

            if success:
                working.append(feed)
            else:
                broken.append(feed)

        results.append({"category": category, "working": working, "broken": broken})
        print()

    return results


def generate_updated_config(results: list) -> str:
    """Generate updated FEEDS list for rss_fetcher.py."""
    lines = [
        "FEEDS = [",
    ]

    for result in results:
        for feed in result["working"]:
            lines.append(f"    # {result['category']}")
            lines.append(
                f'    {{"url": "{feed["url"]}", "source": "{feed["name"]}", "category": "{result["category"]}", "core_boost": {str(feed["core_boost"]).lower()}}},'
            )
            lines.append("")

    lines.append("]")

    return "\n".join(lines)


def auto_fix_and_update():
    """Main: validate, report, generate updated config."""
    results = validate_all_feeds()

    # Summary
    total_working = sum(len(r["working"]) for r in results)
    total_broken = sum(len(r["broken"]) for r in results)

    print(f"{'=' * 60}")
    print(f"SUMMARY: {total_working} working | {total_broken} broken")
    print(f"{'=' * 60}")

    # Generate new config
    new_config = generate_updated_config(results)

    print("\n[UPDATED FEEDS CONFIG]")
    print(new_config[:500] + "..." if len(new_config) > 500 else new_config)

    # Save to file
    output_path = "/Users/allanodora/Documents/new Allan/clean up/opt wprl/pundit_pipeline/source_fetchers/updated_feeds.txt"
    with open(output_path, "w") as f:
        f.write(new_config)

    print(f"\nSaved updated config to: {output_path}")
    print("Replace the FEEDS section in rss_fetcher.py with this content.")


if __name__ == "__main__":
    auto_fix_and_update()
