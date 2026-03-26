"""
Pundit Pipeline - Configuration
"""

import os

# Content categories
CONTENT_BUCKETS = [
    "football",
    "hiphop",
    "instagram_drama",
    "ai_tech",
    "trending_general",
]

# Core focus (bonus scoring)
CORE_TOPICS = ["chelsea", "premier league", "var", "cfc"]

# Story output
STORIES_PER_SESSION = 5
MIN_SCORE = 70

# Conspiracy wildcard percentage
CONSPIRACY_CHANCE = 0.05  # 5% of stories

# Scoring weights
SCORING_WEIGHTS = {
    "has_numbers": 15,
    "has_source": 10,
    "is_debatable": 15,
    "is_trending": 15,
    "emotional_trigger": 10,
    "recency": 10,
    "pundit_quote": 5,
    "core_relevant": 10,
    "has_villain": 3,
    "visual_ready": 2,
    "story_potential": 15,
    "has_take_angle": 10,
    "cross_pollination": 10,
    "not_clickbait": 10,
    "conspiracy_sprinkle": 5,
}

# Recency thresholds (hours)
RECENCY_FULL = 24
RECENCY_HALF = 48
RECENCY_OLD = 72

# Selenium paths (optional). Prefer env vars so this repo stays portable.
CHROME_PATH = os.environ.get("CHROME_PATH", "")
DRIVER_PATH = os.environ.get("DRIVER_PATH", "")

# Database
DB_PATH = "pipeline.db"

# Output
OUTPUT_DIR = "output"

# TrendStage per-story topic output path (optional)
# Example: export TRENDSTAGE_TOPICS_PATH="$(pwd)/webapp/topics"
TRENDSTAGE_TOPICS_PATH = os.environ.get("TRENDSTAGE_TOPICS_PATH", "")

# Pipeline modes
PIPELINE_MODE = os.environ.get("PIPELINE_MODE", "LIVE")  # LIVE, CACHED, HISTORICAL

# Scheduler interval (in seconds) for LIVE mode
SCHEDULE_INTERVAL = 300  # 5 minutes
