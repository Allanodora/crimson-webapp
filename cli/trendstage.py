#!/usr/bin/env python3
"""
TrendStage CLI - Generate assets for web app
Usage: python trendstage.py --topic "Chelsea VAR"
"""

import argparse
import json
import math
import random
import time
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class TrendStageCLI:
    def __init__(self, topic: str, output_dir: str):
        self.topic = topic
        self.output_dir = Path(__file__).parent.parent / output_dir
        self.width = 1920
        self.height = 1080
        self.fps = 30

        self.colors = {
            "bg": (10, 10, 15),
            "surface": (22, 22, 31),
            "border": (42, 42, 58),
            "primary": (99, 102, 241),
            "primary_rgb": (99, 102, 241),
            "success": (34, 197, 94),
            "warning": (245, 158, 11),
            "danger": (239, 68, 68),
            "text": (241, 245, 249),
            "text_dim": (148, 163, 184),
        }

        self.data = None

    def run(self):
        print(f"\nTrendStage Generator: {self.topic}\n")
        print("-" * 40)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.collect_data()
        self.generate_stats()
        self.generate_comments()
        self.generate_graph_states()
        self.generate_clip_preview()
        self.write_config()

        print("-" * 40)
        print(f"\nGenerated in: {self.output_dir}")
        print("Open webapp/index.html to start\n")

    def collect_data(self):
        print("[1/5] Collecting data...")

        self.data = {
            "topic": self.topic,
            "event": self._generate_event(),
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "views": random.randint(500000, 8000000),
                "engagement": random.randint(15, 85),
                "velocity": random.randint(50, 300),
                "reach": random.randint(1000000, 15000000),
            },
            "sentiment": self._calculate_sentiment(),
            "trending_score": random.randint(70, 99),
        }

        print(f"  Event: {self.data['event']}")
        print(f"  Views: {self.data['stats']['views']:,}")
        print(f"  Velocity: +{self.data['stats']['velocity']}%")

    def _generate_event(self):
        actions = [
            "surge",
            "breaking",
            "viral moment",
            "exclusive",
            "analysis",
            "reaction",
        ]
        templates = [
            f"{self.topic} {random.choice(actions)}",
            f"Breaking: {self.topic}",
            f"Inside {self.topic}",
            f"{self.topic} explained",
        ]
        return random.choice(templates)

    def _calculate_sentiment(self):
        weights = [0.6, 0.25, 0.15]
        return random.choices(["positive", "neutral", "negative"], weights=weights)[0]

    def generate_stats(self):
        print("[2/5] Generating stats.json...")

        stats = {
            "views": {
                "value": self.data["stats"]["views"],
                "formatted": self._format_number(self.data["stats"]["views"]),
                "trend": "up",
            },
            "engagement": {
                "value": self.data["stats"]["engagement"],
                "formatted": f"{self.data['stats']['engagement']}%",
                "trend": "up",
            },
            "velocity": {
                "value": self.data["stats"]["velocity"],
                "formatted": f"+{self.data['stats']['velocity']}%",
                "trend": "up",
            },
            "sentiment": self.data["sentiment"],
            "trending_score": self.data["trending_score"],
        }

        with open(self.output_dir / "stats.json", "w") as f:
            json.dump(stats, f, indent=2)

    def generate_comments(self):
        print("[3/5] Generating comments.json...")

        comments = [
            {
                "author": "football_fan_92",
                "text": "This changes everything. Game changer.",
                "sentiment": "positive",
                "likes": 4521,
            },
            {
                "author": "tactics_guru",
                "text": "The data supports this completely.",
                "sentiment": "positive",
                "likes": 2847,
            },
            {
                "author": "neutral_viewer",
                "text": "Interesting perspective, needs more context.",
                "sentiment": "neutral",
                "likes": 1203,
            },
            {
                "author": "pundit_daily",
                "text": "Finally someone said it.",
                "sentiment": "positive",
                "likes": 3892,
            },
            {
                "author": "stats_ninja",
                "text": "Numbers don't lie.",
                "sentiment": "positive",
                "likes": 2156,
            },
            {
                "author": "debate_king",
                "text": "Hot take but not entirely wrong.",
                "sentiment": "neutral",
                "likes": 987,
            },
            {
                "author": "fanboy_mike",
                "text": "Best analysis I've seen today!",
                "sentiment": "positive",
                "likes": 1834,
            },
            {
                "author": "critic_sam",
                "text": "Overhyped as usual.",
                "sentiment": "negative",
                "likes": 445,
            },
        ]

        random.shuffle(comments)

        with open(self.output_dir / "comments.json", "w") as f:
            json.dump({"comments": comments[:8], "total": len(comments)}, f, indent=2)

    def generate_graph_states(self):
        print("[4/5] Generating graph states...")

        if not PIL_AVAILABLE:
            print("  Warning: PIL not available, skipping graph generation")
            return

        states = ["full", "highlight", "zoom", "compare"]

        for i, state in enumerate(states):
            img = self._render_graph_state(state, i)
            img.save(self.output_dir / f"graph_{i}.png")
            print(f"  - graph_{i}.png ({state})")

    def _render_graph_state(self, state, index):
        img = Image.new("RGB", (self.width, self.height), self.colors["bg"])
        draw = ImageDraw.Draw(img)

        font_bold = self._get_font(48, bold=True)
        font_regular = self._get_font(24)
        font_small = self._get_font(18)

        if state == "full":
            self._draw_full_graph(draw, font_bold, font_regular, font_small)
        elif state == "highlight":
            self._draw_highlight_graph(draw, font_bold, font_regular, font_small, index)
        elif state == "zoom":
            self._draw_zoom_graph(draw, font_bold, font_regular, font_small)
        elif state == "compare":
            self._draw_compare_graph(draw, font_bold, font_regular, font_small)

        return img

    def _get_font(self, size, bold=False):
        try:
            return ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", size)
        except:
            return ImageFont.load_default()

    def _draw_full_graph(self, draw, font_bold, font_regular, font_small):
        draw.rectangle([60, 80, 900, 700], fill=self.colors["surface"])
        draw.rectangle([60, 80, 900, 700], outline=self.colors["border"], width=2)

        draw.text(
            (80, 100), self.data["topic"], fill=self.colors["text"], font=font_bold
        )

        points = [
            (100, 600),
            (200, 450),
            (300, 520),
            (400, 300),
            (500, 380),
            (600, 200),
            (700, 280),
            (800, 150),
        ]

        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=self.colors["primary"], width=3)

        for x, y in points:
            draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=self.colors["success"])

        draw.text(
            (100, 720),
            f"Peak: {self._format_number(self.data['stats']['views'])} views",
            fill=self.colors["text_dim"],
            font=font_regular,
        )

        draw.rectangle([60, 80, 65, 700], fill=self.colors["primary"])

    def _draw_highlight_graph(self, draw, font_bold, font_regular, font_small, frame):
        draw.rectangle([60, 80, 900, 700], fill=self.colors["surface"])
        draw.rectangle([60, 80, 900, 700], outline=self.colors["primary"], width=3)

        draw.text(
            (80, 100), self.data["topic"], fill=self.colors["text"], font=font_bold
        )

        highlight_y = 300 + math.sin(frame * 0.5) * 50
        draw.ellipse(
            [550, highlight_y - 30, 750, highlight_y + 30], fill=self.colors["primary"]
        )

        points = [
            (100, 600),
            (200, 450),
            (300, 520),
            (400, 300),
            (500, 380),
            (600, 200),
            (700, 280),
            (800, 150),
        ]

        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=self.colors["border"], width=2)

        draw.line([points[5], points[6]], fill=self.colors["primary"], width=4)

        draw.text(
            (550, highlight_y + 50),
            f"+{self.data['stats']['velocity']}%",
            fill=self.colors["success"],
            font=font_bold,
        )

        draw.rectangle([60, 80, 65, 700], fill=self.colors["primary"])

    def _draw_zoom_graph(self, draw, font_bold, font_regular, font_small):
        draw.rectangle([60, 80, 900, 700], fill=self.colors["surface"])
        draw.rectangle([60, 80, 900, 700], outline=self.colors["success"], width=3)

        draw.text(
            (80, 100),
            f"ZOOM: {self.data['topic']}",
            fill=self.colors["text"],
            font=font_bold,
        )

        points = [
            (100, 550),
            (200, 480),
            (300, 420),
            (400, 350),
            (500, 280),
            (600, 200),
            (700, 280),
            (800, 150),
        ]

        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=self.colors["success"], width=4)

        for x, y in points:
            draw.ellipse([x - 6, y - 6, x + 6, y + 6], fill=self.colors["success"])

        draw.text(
            (100, 720),
            "Peak Performance Zone",
            fill=self.colors["success"],
            font=font_regular,
        )

        draw.rectangle([60, 80, 65, 700], fill=self.colors["success"])

    def _draw_compare_graph(self, draw, font_bold, font_regular, font_small):
        draw.rectangle([60, 80, 900, 700], fill=self.colors["surface"])
        draw.rectangle([60, 80, 900, 700], outline=self.colors["warning"], width=3)

        draw.text(
            (80, 100),
            f"COMPARE: {self.data['topic']}",
            fill=self.colors["text"],
            font=font_bold,
        )

        draw.text((120, 150), "Current", fill=self.colors["primary"], font=font_regular)
        draw.rectangle([120, 180, 400, 200], fill=self.colors["primary"])

        draw.text(
            (120, 220), "Previous", fill=self.colors["text_dim"], font=font_regular
        )
        draw.rectangle([120, 250, 280, 270], fill=self.colors["text_dim"])

        comparison = self.data["stats"]["velocity"]
        draw.text(
            (120, 300),
            f"+{comparison}% vs last period",
            fill=self.colors["success"],
            font=font_bold,
        )

        draw.rectangle([60, 80, 65, 700], fill=self.colors["warning"])

    def generate_clip_preview(self):
        print("[5/5] Generating clip preview...")

        if not PIL_AVAILABLE:
            print("  Warning: PIL not available, skipping clip generation")
            return

        img = Image.new("RGB", (self.width, self.height), self.colors["bg"])
        draw = ImageDraw.Draw(img)

        font_bold = self._get_font(64, bold=True)
        font_regular = self._get_font(32)

        draw.rectangle([980, 80, 1860, 700], fill=self.colors["surface"])
        draw.rectangle([980, 80, 1860, 700], outline=self.colors["border"], width=2)

        draw.text(
            (1100, 300), self.data["event"], fill=self.colors["text"], font=font_bold
        )
        draw.text(
            (1100, 400),
            f"Sentiment: {self.data['sentiment']}",
            fill=self.colors["text_dim"],
            font=font_regular,
        )

        sentiment_color = {
            "positive": self.colors["success"],
            "neutral": self.colors["warning"],
            "negative": self.colors["danger"],
        }.get(self.data["sentiment"], self.colors["text_dim"])

        draw.ellipse([1050, 330, 1090, 370], fill=sentiment_color)

        img.save(self.output_dir / "clip_preview.png")
        print("  - clip_preview.png")

    def write_config(self):
        print("\n[Config] Writing config.json...")

        config = {
            "topic": self.data["topic"],
            "event": self.data["event"],
            "timestamp": self.data["timestamp"],
            "elements": {
                "graph": {
                    "states": [
                        "graph_0.png",
                        "graph_1.png",
                        "graph_2.png",
                        "graph_3.png",
                    ],
                    "zone": "left",
                    "default_state": 0,
                },
                "clip": {"src": "clip_preview.png", "zone": "right"},
                "comments": {"data": "comments.json", "zone": "bottom"},
                "stats": {"data": "stats.json", "zone": "top"},
            },
            "layout": {
                "graph": {"x": 60, "y": 80, "width": 840, "height": 620},
                "clip": {"x": 980, "y": 80, "width": 880, "height": 620},
                "comments": {"x": 60, "y": 750, "width": 1800, "height": 200},
                "stats": {"x": 60, "y": 15, "width": 1800, "height": 50},
            },
        }

        with open(self.output_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)

        print("  - config.json")

    def _format_number(self, num):
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)


def main():
    parser = argparse.ArgumentParser(
        description="TrendStage: Generate assets for web app"
    )
    parser.add_argument(
        "--topic", "-t", required=True, help="Topic to generate assets for"
    )
    parser.add_argument(
        "--output", "-o", default="webapp/assets", help="Output directory"
    )

    args = parser.parse_args()

    cli = TrendStageCLI(topic=args.topic, output_dir=args.output)
    cli.run()


if __name__ == "__main__":
    main()
