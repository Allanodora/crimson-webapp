"""
Two-Tier Content Scorer
Tier 1: score >= 70 → rich AI talking points (slots 1-3)
Tier 2: score >= 45 → rule-based talking points (slots 4-5)
Slow News Day: score >= 30 → clickbait wildcard allowed (slot 5 only)
"""

import re
import sys
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import config as CONFIG
except Exception:
    class _C:
        SCORING_WEIGHTS = {}
        CORE_TOPICS = []
        CONSPIRACY_CHANCE = 0.05
    CONFIG = _C()

SCORING_WEIGHTS = getattr(CONFIG, "SCORING_WEIGHTS", {
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
})

CORE_TOPICS = getattr(CONFIG, "CORE_TOPICS", ["chelsea", "premier league", "var", "cfc"])
CONSPIRACY_CHANCE = getattr(CONFIG, "CONSPIRACY_CHANCE", 0.05)

# Tier thresholds
TIER_1 = 70   # Best stories
TIER_2 = 45   # Decent stories
SLOW_DAY = 30 # Clickbait valve threshold


class TwoTierScorer:
    NUMBER_PATTERNS = [
        r"\d+%", r"\d+\s*(goals?|points?|errors?|wins?|losses?|million|billion)",
        r"#\d+", r"\d+\s*(times|more|less|increase|decrease|x)",
        r"ranked?\s*\d+", r"\d+/\d+", r"\$[\d,]+",
    ]

    CLICKBAIT_PATTERNS = [
        r"you won't believe", r"what happens next", r"the answer will surprise",
        r"\?!\?", r"incredible", r"mind.?blow", r"gone wrong",
        r"reacts to", r"destroys", r"exposes", r"secret", r"leaked",
    ]

    DEBATABLE_PATTERNS = [
        r"is\s+\w+\s+(the\s+)?(best|worst|greatest|most overrated)",
        r"debate", r"controvers", r"hot take", r"agree|disagree",
        r"overrated|underrated", r"should (he|she|they|it)",
        r"was (he|she|it) right", r"unpopular opinion",
    ]

    EMOTIONAL_WORDS = [
        "meltdown", "rage", "furious", "shocked", "stunned", "insane",
        "crazy", "wild", "disaster", "humiliated", "outrage", "scandal",
        "ban", "sacked", "fired", "exposed", "beef", "drama", "clap back",
        "slammed", "blasted", "roasted", "destroyed",
    ]

    VILLAIN_PATTERNS = [
        r"blame", r"fault", r"cost\s+(them|us)", r"ruined",
        r"terrible|awful|disgrace|shambles", r"referee|ref|VAR|official",
        r"robbed", r"cheated", r"rigged",
    ]

    PUNDIT_NAMES = [
        "neville", "carragher", "kane", "shearer", "lineker", "morgan",
        "rooney", "ferdinand", "terry", "lampard", "gerrard", "wright",
        "merson", "redknapp", "souness", "keane", r"kendrick", r"drake",
        r"akademiks", r"charlamagne",
    ]

    def score(self, content: dict) -> dict:
        score = 0
        flags = []
        breakdown = {}

        title = content.get("title", "").lower()
        description = content.get("description", "").lower()
        full_text = f"{title} {description}"

        # 1. Numbers/stats
        has_numbers = self._match_any(full_text, self.NUMBER_PATTERNS)
        if has_numbers:
            score += SCORING_WEIGHTS.get("has_numbers", 15)
            flags.append("has_stats")
        breakdown["has_numbers"] = has_numbers

        # 2. Source/graph
        has_source = bool(content.get("has_graph") or content.get("has_data_viz"))
        if has_source:
            score += SCORING_WEIGHTS.get("has_source", 10)
            flags.append("has_source")
        breakdown["has_source"] = has_source

        # 3. Debatable
        is_debatable = self._match_any(full_text, self.DEBATABLE_PATTERNS)
        if is_debatable:
            score += SCORING_WEIGHTS.get("is_debatable", 15)
            flags.append("debatable")
        breakdown["is_debatable"] = is_debatable

        # 4. Trending/engagement
        is_trending = content.get("is_trending", False)
        eng = content.get("engagement", {})
        if eng.get("likes", 0) > 1000 or eng.get("shares", 0) > 500:
            is_trending = True
        if is_trending:
            score += SCORING_WEIGHTS.get("is_trending", 15)
            flags.append("trending")
        breakdown["is_trending"] = is_trending

        # 5. Emotional
        has_emotion = any(w in full_text for w in self.EMOTIONAL_WORDS)
        if has_emotion:
            score += SCORING_WEIGHTS.get("emotional_trigger", 10)
            flags.append("emotional")
        breakdown["has_emotion"] = has_emotion

        # 6. Recency
        recency_score = self._recency(content.get("timestamp"))
        score += recency_score
        if recency_score > 0:
            flags.append("fresh")
        breakdown["recency_score"] = recency_score

        # 7. Pundit quote
        has_pundit = self._match_any(full_text, self.PUNDIT_NAMES)
        if not has_pundit:
            has_pundit = bool(re.search(r"(says?|said|claims?|insists?|slams?|hits? out|reacts?)", full_text))
        if has_pundit:
            score += SCORING_WEIGHTS.get("pundit_quote", 5)
            flags.append("pundit_quote")
        breakdown["has_pundit"] = has_pundit

        # 8. Core relevance (Chelsea/PL)
        is_core = content.get("core_relevant", False) or any(t in full_text for t in CORE_TOPICS)
        if is_core:
            score += SCORING_WEIGHTS.get("core_relevant", 10)
            flags.append("core_topic")
        breakdown["is_core"] = is_core

        # 9. Villain
        has_villain = self._match_any(full_text, self.VILLAIN_PATTERNS)
        if has_villain:
            score += SCORING_WEIGHTS.get("has_villain", 3)
            flags.append("has_villain")
        breakdown["has_villain"] = has_villain

        # 10. Visual ready
        if content.get("has_image"):
            score += SCORING_WEIGHTS.get("visual_ready", 2)
            flags.append("visual_ready")
        breakdown["visual_ready"] = content.get("has_image", False)

        # 11. Story potential
        story_words = ["because", "but then", "however", "result", "after",
                       "leading to", "consequence", "reaction", "backlash",
                       "response", "following", "amid"]
        story_hits = sum(1 for w in story_words if w in full_text)
        has_story = story_hits >= 2
        if has_story:
            score += SCORING_WEIGHTS.get("story_potential", 15)
            flags.append("story_potential")
        breakdown["has_story"] = has_story

        # 12. Take angle
        take_words = ["hot take", "here's why", "the truth", "unpopular opinion",
                      "controversial", "thoughts?", "explain", "breakdown", "thread"]
        has_take = any(w in full_text for w in take_words)
        if has_take:
            score += SCORING_WEIGHTS.get("has_take_angle", 10)
            flags.append("take_angle")
        breakdown["has_take"] = has_take

        # 13. Cross-pollination
        cross_topics = ["science", "ai", "tech", "politics", "culture",
                        "gaming", "business", "crypto", "finance"]
        cross_hits = [t for t in cross_topics if t in full_text]
        if len(cross_hits) >= 2 or (len(cross_hits) >= 1 and is_core):
            score += SCORING_WEIGHTS.get("cross_pollination", 10)
            flags.append("cross_pollination")
        breakdown["cross_pollination"] = len(cross_hits) > 0

        # 14. Clickbait check
        is_clickbait = self._match_any(full_text, self.CLICKBAIT_PATTERNS)
        if not is_clickbait:
            score += SCORING_WEIGHTS.get("not_clickbait", 10)
            flags.append("legit")
        else:
            flags.append("clickbait")
        breakdown["is_clickbait"] = is_clickbait

        # 15. Conspiracy sprinkle
        conspiracy_words = ["conspiracy", "cover up", "they don't want", "rigged",
                            "fixed", "behind closed doors", "corrupt", "agenda", "wake up"]
        is_conspiracy = any(w in full_text for w in conspiracy_words)
        if is_conspiracy and random.random() < CONSPIRACY_CHANCE:
            score += SCORING_WEIGHTS.get("conspiracy_sprinkle", 5)
            flags.append("conspiracy")
        breakdown["is_conspiracy"] = is_conspiracy

        score = min(score, 100)

        # Determine tier
        if score >= TIER_1:
            tier = 1
            verdict = "PASS_T1"
        elif score >= TIER_2:
            tier = 2
            verdict = "PASS_T2"
        elif score >= SLOW_DAY and is_clickbait:
            tier = 3
            verdict = "SLOW_DAY_WILDCARD"
        else:
            tier = 0
            verdict = "FAIL"

        return {
            "content": content,
            "score": score,
            "tier": tier,
            "flags": flags,
            "breakdown": breakdown,
            "verdict": verdict,
            "is_clickbait": is_clickbait,
        }

    def _match_any(self, text: str, patterns: list) -> bool:
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return True
        return False

    def _recency(self, timestamp) -> int:
        if not timestamp:
            return 0
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except Exception:
                return 0
        try:
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        except Exception:
            return 0
        w = SCORING_WEIGHTS.get("recency", 10)
        if age_hours <= 6:
            return w
        elif age_hours <= 24:
            return w
        elif age_hours <= 48:
            return w // 2
        elif age_hours <= 72:
            return w // 4
        return 0


def select_top5(scored: list) -> list:
    """
    Pick 5 stories using two-tier logic.
    Slots 1-3: Tier 1 (score >= 70)
    Slots 4-5: Tier 1 or Tier 2 (score >= 45)
    Slot 5 fallback: slow news day wildcard if needed
    """
    tier1 = [s for s in scored if s["verdict"] == "PASS_T1"]
    tier2 = [s for s in scored if s["verdict"] == "PASS_T2"]
    wildcards = [s for s in scored if s["verdict"] == "SLOW_DAY_WILDCARD"]

    # Sort each tier by score desc
    for lst in (tier1, tier2, wildcards):
        lst.sort(key=lambda x: x["score"], reverse=True)

    selected = []

    # Fill slots 1-3 from tier1
    selected.extend(tier1[:3])

    # Fill slots 4-5 from remaining tier1 then tier2
    remaining_t1 = tier1[3:]
    pool45 = remaining_t1 + tier2
    pool45.sort(key=lambda x: x["score"], reverse=True)
    needed = 5 - len(selected)
    selected.extend(pool45[:needed])

    # Still need more? Use wildcards (slow news day)
    if len(selected) < 5 and wildcards:
        needed = 5 - len(selected)
        print(f"  [Scorer] Slow news day - letting {needed} wildcard(s) through")
        selected.extend(wildcards[:needed])

    return selected[:5]
