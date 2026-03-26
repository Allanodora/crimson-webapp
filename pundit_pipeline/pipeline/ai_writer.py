"""
AI Writer - Generates conversational talking points per story.
No external API calls; uses rule-based notes for reliability.
"""

import re


def generate_tier1_notes(story: dict) -> list[str]:
    """
    Rich, conversational talking points for Tier 1 stories.
    Designed to let you go on tangents naturally.
    """
    return _rule_based_notes(story, tier=1)


def generate_tier2_notes(story: dict) -> list[str]:
    """
    Shorter, rule-based notes for Tier 2 stories.
    Still usable, just less rich.
    """
    return _rule_based_notes(story, tier=2)[:4]


def generate_wildcard_notes(story: dict) -> list[str]:
    """
    Hot-take framing for slow news day wildcards.
    Leans into the clickbait angle but keeps it entertaining.
    """
    title = story.get("title", "")
    return [
        "Slow news day so we're going here...",
        f"The story is: {title[:80]}",
        "Take this with a grain of salt but it's still kinda interesting.",
        "What do you think — is this worth talking about?",
    ]


def _rule_based_notes(story: dict, tier: int = 2) -> list[str]:
    """Fallback rule-based notes when API fails."""
    title = story.get("title", "Untitled")
    description = story.get("description", "")
    flags = story.get("flags", [])
    category = story.get("category", "general")
    source = story.get("source", "")

    notes = []

    # Opener
    cat_openers = {
        "football": "Right let's talk football —",
        "hiphop": "Hip-hop Twitter is going crazy about this —",
        "ai_tech": "AI news just dropped and this one's actually wild —",
        "trending_general": "This is trending everywhere right now —",
        "instagram_drama": "Instagram drama alert —",
    }
    opener = cat_openers.get(category, "So this is trending —")
    notes.append(f"{opener} {title[:80]}")

    # Key fact
    if description:
        notes.append(f"Here's what we know: {description[:150]}")
    elif "has_stats" in flags:
        notes.append("There's a key stat attached to this one — look at these numbers.")

    # Take angle
    if "debatable" in flags:
        notes.append("And this is where it gets interesting — people are actually split on this.")
    elif "emotional" in flags:
        notes.append("The reaction to this has been completely unhinged and I'm here for it.")
    elif "core_topic" in flags:
        notes.append("Chelsea fans especially are gonna have thoughts on this one.")

    # Tangent hook
    if "cross_pollination" in flags:
        notes.append("What's interesting is how this connects to the bigger picture — this isn't just about football/music.")
    else:
        notes.append(f"Source on this is {source} — worth reading the full thing after.")

    # Audience question
    notes.append("Let me know in the comments — am I wrong? Because I could be wrong.")

    return notes[:5]


def write_story(story: dict, tier: int, is_clickbait: bool = False) -> list[str]:
    """
    Main entry point. Routes to appropriate writer based on tier.
    Returns list of speaker note strings.
    """
    print(f"  [AI Writer] Writing Tier {tier} notes for: {story.get('title', '')[:50]}")

    if tier == 1:
        return generate_tier1_notes(story)
    elif tier == 2:
        return generate_tier2_notes(story)
    elif tier == 3 or is_clickbait:
        return generate_wildcard_notes(story)
    else:
        return _rule_based_notes(story, tier=2)
