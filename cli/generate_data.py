#!/usr/bin/env python3
import json
import random
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class MultiTrendGenerator:
    def __init__(self, base_dir="webapp/assets"):
        self.base_dir = Path(__file__).parent.parent / base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.colors = {
            "bg": (10, 10, 15),
            "surface": (22, 22, 31),
            "primary": (59, 130, 246),
            "success": (34, 197, 94),
            "text": (241, 245, 249),
            "text_dim": (100, 116, 139),
        }

    def generate_topic_data(self, topic_name):
        print(f"Generating assets for: {topic_name}")
        folder = self.base_dir / topic_name.lower().replace(" ", "_")
        folder.mkdir(parents=True, exist_ok=True)

        # 1. Stats
        views = random.randint(100000, 5000000)
        stats = {
            "views": {"value": views, "formatted": self._format_num(views)},
            "velocity": {"value": random.randint(20, 200)},
            "engagement": {
                "value": random.randint(5, 45),
                "formatted": f"{random.randint(5, 45)}%",
            },
        }
        with open(folder / "stats.json", "w") as f:
            json.dump(stats, f)

        # 2. Comments
        comments = {
            "comments": [
                {
                    "author": f"user_{i}",
                    "text": f"This is incredible news about {topic_name}!",
                    "likes": random.randint(10, 1000),
                }
                for i in range(5)
            ]
        }
        with open(folder / "comments.json", "w") as f:
            json.dump(comments, f)

        # 3. Graphs (3 states)
        for i in range(3):
            img = Image.new("RGB", (1200, 800), self.colors["bg"])
            draw = ImageDraw.Draw(img)
            # Simple line graph
            points = [(50 + x * 200, 700 - random.randint(100, 600)) for x in range(6)]
            draw.line(points, fill=self.colors["primary"], width=5)
            for p in points:
                draw.ellipse(
                    [p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8],
                    fill=self.colors["success"],
                )

            draw.text((50, 50), f"{topic_name} - State {i}", fill=self.colors["text"])
            img.save(folder / f"graph_{i}.png")

        # 4. Media (dummy image)
        media = Image.new("RGB", (1280, 720), (30, 30, 40))
        draw = ImageDraw.Draw(media)
        draw.text((500, 350), f"MEDIA FOR {topic_name}", fill=(255, 255, 255))
        media.save(folder / "media.png")

        return {
            "name": topic_name,
            "path": topic_name.lower().replace(" ", "_"),
            "views_fmt": stats["views"]["formatted"],
        }

    def _format_num(self, n):
        if n > 1000000:
            return f"{n / 1000000:.1f}M"
        if n > 1000:
            return f"{n / 1000:.1f}K"
        return str(n)


def main():
    topics = [
        "Chelsea VAR",
        "AI Breakthrough",
        "Bitcoin Spike",
        "Mars Landing",
        "New iPhone",
    ]
    generator = MultiTrendGenerator()
    manifest = []

    for t in topics:
        data = generator.generate_topic_data(t)
        manifest.append(
            {
                "name": data["name"],
                "id": data["path"],
                "assets": {
                    "graph": [
                        f"assets/{data['path']}/graph_0.png",
                        f"assets/{data['path']}/graph_1.png",
                        f"assets/{data['path']}/graph_2.png",
                    ],
                    "media": f"assets/{data['path']}/media.png",
                    "stats": f"assets/{data['path']}/stats.json",
                    "comments": f"assets/{data['path']}/comments.json",
                    "source_url": f"https://news.google.com/search?q={data['path']}",
                },
                "meta": {"views": data["views_fmt"]},
            }
        )

    with open(Path(__file__).parent.parent / "webapp/config.json", "w") as f:
        json.dump({"topics": manifest}, f, indent=2)
    print("\nDone! Manifest written to webapp/config.json")


if __name__ == "__main__":
    main()
