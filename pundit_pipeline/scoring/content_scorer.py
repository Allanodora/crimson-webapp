"""
Content Scorer - Evaluates content for pipeline inclusion
"""

import re
from datetime import datetime, timedelta
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import config as CONFIG
except Exception:

    class _C:
        SCORING_WEIGHTS = {}
        CORE_TOPICS = []
        CONSPIRACY_CHANCE = 0.05

    CONFIG = _C()

SCORING_WEIGHTS = getattr(
    CONFIG,
    "SCORING_WEIGHTS",
    {
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
    },
)

CORE_TOPICS = getattr(
    CONFIG, "CORE_TOPICS", ["chelsea", "premier league", "var", "cfc"]
)
CONSPIRACY_CHANCE = getattr(CONFIG, "CONSPIRACY_CHANCE", 0.05)


class ContentScorer:
    """Scores content based on fact-richness and engagement potential."""

    NUMBER_PATTERNS = [
        r"\d+%",
        r"\d+\s*(goals?|points?|errors?|wins?|losses?)",
        r"#\d+",
        r"\d+\s*(times|more|less|increase|decrease)",
        r"ranked?\s*\d+",
        r"\d+/\d+",
    ]

    CLICKBAIT_PATTERNS = [
        r"you won't believe",
        r"shocking",
        r"what happens next",
        r"the answer will surprise you",
        r"\?\!\?",
        r"incredible",
    ]

    DEBATABLE_PATTERNS = [
        r"is\s+\w+\s+(the\s+)?(best|worst|greatest)",
        r"debate",
        r"controvers",
        r"argu",
        r"hot take",
        r"agree|disagree",
        r"overrated|underrated",
    ]

    EMOTIONAL_WORDS = [
        "meltdown",
        "rage",
        "furious",
        "shocked",
        "stunned",
        "unbelievable",
        "insane",
        "crazy",
        "wild",
        "disaster",
        "humiliated",
        "embarrassed",
        "outrage",
        "scandal",
        "ban",
        "sacked",
        "fired",
    ]

    VILLAIN_PATTERNS = [
        r"blame",
        r"fault",
        r"cost\s+(them|us)",
        r"ruined",
        r"terrible|awful|disgrace|shambles",
        r"referee|ref|VAR|official",
    ]

    def score(self, content: dict) -> dict:
        score = 0
        flags = []
        breakdown = {}

        title = content.get("title", "").lower()
        description = content.get("description", "").lower()
        full_text = f"{title} {description}"

        # 1. Has numbers/stats
        has_numbers = self._check_numbers(full_text)
        if has_numbers:
            score += SCORING_WEIGHTS.get("has_numbers", 15)
            flags.append("has_stats")
        breakdown["has_numbers"] = has_numbers

        # 2. Has source/graph
        has_source = content.get("has_graph") or content.get("has_data_viz")
        if has_source:
            score += SCORING_WEIGHTS.get("has_source", 10)
            flags.append("has_source")
        breakdown["has_source"] = has_source

        # 3. Is debatable
        is_debatable = self._check_debatable(full_text)
        if is_debatable:
            score += SCORING_WEIGHTS.get("is_debatable", 15)
            flags.append("debatable")
        breakdown["is_debatable"] = is_debatable

        # 4. Is trending
        is_trending = content.get("is_trending", False)
        engagement = content.get("engagement", {})
        if engagement.get("likes", 0) > 1000 or engagement.get("shares", 0) > 500:
            is_trending = True
        if is_trending:
            score += SCORING_WEIGHTS.get("is_trending", 15)
            flags.append("trending")
        breakdown["is_trending"] = is_trending

        # 5. Emotional trigger
        has_emotion = self._check_emotional(full_text)
        if has_emotion:
            score += SCORING_WEIGHTS.get("emotional_trigger", 10)
            flags.append("emotional")
        breakdown["has_emotion"] = has_emotion

        # 6. Recency
        recency_score = self._check_recency(content.get("timestamp"))
        score += recency_score
        if recency_score > 0:
            flags.append("fresh")
        breakdown["recency_score"] = recency_score

        # 7. Pundit quote
        has_pundit = self._check_pundit(full_text)
        if has_pundit:
            score += SCORING_WEIGHTS.get("pundit_quote", 5)
            flags.append("pundit_quote")
        breakdown["has_pundit"] = has_pundit

        # 8. Core relevant (Chelsea/PL)
        is_core = self._check_core_relevant(full_text)
        if is_core:
            score += SCORING_WEIGHTS.get("core_relevant", 10)
            flags.append("core_topic")
        breakdown["is_core"] = is_core

        # 9. Has villain
        has_villain = self._check_villain(full_text)
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
        has_story = self._check_story_potential(full_text, content)
        if has_story:
            score += SCORING_WEIGHTS.get("story_potential", 15)
            flags.append("story_potential")
        breakdown["has_story"] = has_story

        # 12. Has take angle
        has_take = self._check_take_angle(full_text)
        if has_take:
            score += SCORING_WEIGHTS.get("has_take_angle", 10)
            flags.append("take_angle")
        breakdown["has_take"] = has_take

        # 13. Cross-pollination
        cross_score = self._check_cross_pollination(content)
        if cross_score > 0:
            score += cross_score
            flags.append("cross_pollination")
        breakdown["cross_pollination"] = cross_score > 0

        # 14. Not clickbait
        is_clickbait = self._check_clickbait(full_text)
        if not is_clickbait:
            score += SCORING_WEIGHTS.get("not_clickbait", 10)
            flags.append("legit")
        breakdown["is_clickbait"] = is_clickbait

        # 15. Conspiracy sprinkle (bonus, occasional)
        is_conspiracy = self._check_conspiracy(full_text)
        if is_conspiracy and random.random() < CONSPIRACY_CHANCE:
            score += SCORING_WEIGHTS.get("conspiracy_sprinkle", 5)
            flags.append("conspiracy")
        breakdown["is_conspiracy"] = is_conspiracy

        return {
            "content": content,
            "score": min(score, 100),
            "flags": flags,
            "breakdown": breakdown,
            "verdict": "PASS" if score >= 70 else "FAIL",
        }

    def _check_numbers(self, text: str) -> bool:
        for pattern in self.NUMBER_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _check_clickbait(self, text: str) -> bool:
        for pattern in self.CLICKBAIT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _check_debatable(self, text: str) -> bool:
        for pattern in self.DEBATABLE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _check_emotional(self, text: str) -> bool:
        for word in self.EMOTIONAL_WORDS:
            if word in text:
                return True
        return False

    def _check_pundit(self, text: str) -> bool:
        pundits = [
            "neville",
            "carragher",
            "kane",
            "shearer",
            "lineker",
            "morgan",
            "rooney",
            "ferdinand",
            "terry",
            "lampard",
            "gerrard",
            "wright",
            "merson",
            "redknapp",
        ]
        for pundit in pundits:
            if pundit in text:
                return True
        if re.search(r"(says?|said|claims?|insists?|slams?|hits? out)", text):
            return True
        return False

    def _check_core_relevant(self, text: str) -> bool:
        for topic in CORE_TOPICS:
            if topic in text:
                return True
        return False

    def _check_villain(self, text: str) -> bool:
        for pattern in self.VILLAIN_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _check_recency(self, timestamp) -> int:
        if not timestamp:
            return 0
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except:
                return 0

        age = datetime.now() - timestamp
        hours = age.total_seconds() / 3600

        recency_weight = SCORING_WEIGHTS.get("recency", 10)
        if hours <= 24:
            return recency_weight
        elif hours <= 48:
            return recency_weight // 2
        elif hours <= 72:
            return recency_weight // 4
        return 0

    def _check_story_potential(self, text: str, content: dict) -> bool:
        story_words = [
            "because",
            "but then",
            "however",
            "result",
            "after",
            "leading to",
            "consequence",
            "reaction",
            "backlash",
        ]
        score = 0
        for word in story_words:
            if word in text:
                score += 1
        return score >= 2

    def _check_take_angle(self, text: str) -> bool:
        take_words = [
            "opinion",
            "hot take",
            "my view",
            "here's why",
            "the truth",
            "let me explain",
            "unpopular opinion",
            "controversial",
            "debate this",
            "thoughts?",
        ]
        for word in take_words:
            if word in text:
                return True
        return False

    def _check_cross_pollination(self, content: dict) -> int:
        title = content.get("title", "").lower()
        cross_topics = [
            "science",
            "ai",
            "tech",
            "politics",
            "culture",
            "fashion",
            "gaming",
            "music",
            "business",
        ]

        found = [t for t in cross_topics if t in title]

        if len(found) >= 2:
            return SCORING_WEIGHTS.get("cross_pollination", 10)
        return 0

    def _check_conspiracy(self, text: str) -> bool:
        conspiracy_words = [
            "conspiracy",
            "cover up",
            "they don't want",
            "rigged",
            "fixed",
            "behind closed doors",
            "corrupt",
            "agenda",
            "wake up",
        ]
        for word in conspiracy_words:
            if word in text:
                return True
        return False


if __name__ == "__main__":
    scorer = ContentScorer()

    test_content = {
        "title": "VAR made 30% more errors this season - Pundits furious",
        "description": "According to BBC Sport data, VAR has overturned 45 decisions this season compared to 35 last year. Gary Neville calls it 'a disgrace'.",
        "source": "bbc",
        "timestamp": datetime.now().isoformat(),
        "has_graph": True,
        "is_trending": True,
        "engagement": {"likes": 5000, "shares": 1200},
    }

    result = scorer.score(test_content)
    print(f"Score: {result['score']}/100")
    print(f"Verdict: {result['verdict']}")
    print(f"Flags: {result['flags']}")
