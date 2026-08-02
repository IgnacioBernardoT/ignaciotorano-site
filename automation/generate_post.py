#!/usr/bin/env python3
"""
generate_post.py
----------------
Runs inside GitHub Actions on a schedule (or manually).

  1. Picks the next unposted topic from automation/topics.csv.
     If every topic is used, asks Claude to invent a brand-new one
     and appends it to the CSV — the system never runs dry.
  2. Calls the Claude API once and gets back structured JSON:
     GBP post + full blog article + title/slug/category/SEO meta.
  3. Writes blog/<slug>/index.html from automation/blog_template.html.
  4. Writes automation/pending/<slug>.json (the GBP post waiting
     for approval — published only after the PR is merged).
  5. Marks the CSV row as P (pending).

Requires env var: ANTHROPIC_API_KEY
"""

import csv
import json
import os
import re
import sys
import urllib.request
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_CSV = os.path.join(REPO, "automation", "topics.csv")
TEMPLATE = os.path.join(REPO, "automation", "blog_template.html")
PENDING_DIR = os.path.join(REPO, "automation", "pending")
BLOG_DIR = os.path.join(REPO, "blog")

MODEL = "claude-sonnet-4-6"
CATEGORIES = ["Buyers Guide", "Sellers Guide", "Market Insight", "Neighborhood Guide", "Local Living"]

VOICE_RULES = (
    "Voice rules (non-negotiable): Structure is Hook (reframe something the reader "
    "thinks they know, or a surprising fact), then Reward (the real insight they will "
    "remember), then Potential Issue (what goes wrong if they don't know this), then "
    "Solution (the answer delivered naturally, never as advice to contact anyone). "
    "First person singular, minimal use of I. Where relevant, reference specific South "
    "Tampa streets, neighborhoods, or local businesses by name (Bayshore Boulevard, "
    "Hyde Park, Davis Islands, Palma Ceia, South Howard, Westshore, Port Tampa, etc.). "
    "Reader-first, never agent-centric or promotional."
)


def call_claude(prompt: str) -> dict:
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    text = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def load_topics():
    with open(TOPICS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f)), ["Day", "Topic", "Tone", "Posted"]


def save_topics(rows, fields):
    with open(TOPICS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def existing_slugs():
    if not os.path.isdir(BLOG_DIR):
        return set()
    return {d for d in os.listdir(BLOG_DIR) if os.path.isdir(os.path.join(BLOG_DIR, d))}


def pick_topic(rows, fields):
    for row in rows:
        if row["Posted"].strip().upper() == "N":
            return row
    # List exhausted — have Claude invent a new topic.
    used = "; ".join(r["Topic"] for r in rows[-40:])
    new = call_claude(
        "You write content topics for a South Tampa, Florida real estate blog and "
        "Google Business Profile. Invent ONE new topic that is NOT in this list: "
        + used +
        ". Respond ONLY with JSON, no markdown fences: "
        '{"topic": "...", "tone": "Friendly & Local"}'
    )
    row = {
        "Day": str(len(rows) + 1),
        "Topic": new["topic"],
        "Tone": new.get("tone", "Friendly & Local"),
        "Posted": "N",
    }
    rows.append(row)
    return row


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:70].rstrip("-")


def title_html(title: str) -> str:
    words = title.split()
    if len(words) < 2:
        return title
    return " ".join(words[:-1]) + " <em>" + words[-1] + "</em>"


def main():
    rows, fields = load_topics()
    row = pick_topic(rows, fields)
    topic, tone = row["Topic"], row["Tone"]
    taken = existing_slugs()

    prompt = (
        "You write for Ignacio Toraño, a South Tampa, Florida real estate agent. "
        "Generate BOTH a Google Business Profile post and a full blog article on the "
        "topic below. " + VOICE_RULES + "\n\n"
        f"Topic: {topic}\nTone: {tone}\n\n"
        "GBP post: 1000 characters max, plain text only, no hashtags, no emojis, no "
        "markdown, no # symbols, no agent name, no CTA, no ask. End with a single "
        "short first-person observational sentence that grounds it in real market "
        "experience — no ask.\n\n"
        "Blog article: 500-800 words in the same voice. A lead sentence (one strong "
        "italic-worthy line), then 4-6 paragraphs. In the paragraphs you may weave in "
        "one or two natural internal links using these exact hrefs where they fit: "
        "https://ignaciotorano.com/blog (anchor about writing on these details) and "
        "https://ignaciotorano.com/#contact (a single soft, natural mention at most). "
        "Paragraphs are plain HTML <p class=\"reveal\">...</p> strings without the "
        "lead.\n\n"
        f"Slug must NOT be any of: {', '.join(sorted(taken)) or 'none'}.\n\n"
        "Respond ONLY with JSON, no markdown fences, exactly this shape:\n"
        "{\n"
        '  "title": "Short Title Case Headline",\n'
        '  "slug": "lowercase-hyphenated-slug",\n'
        f'  "category": "one of: {", ".join(CATEGORIES)}",\n'
        '  "meta_description": "150 chars max SEO description",\n'
        '  "keywords": "comma, separated, seo, keywords",\n'
        '  "gbp_post": "the full GBP post text",\n'
        '  "lead": "the single lead sentence for the blog article",\n'
        '  "paragraphs": ["<p class=\\"reveal\\">...</p>", "..."]\n'
        "}"
    )

    out = call_claude(prompt)

    slug = slugify(out.get("slug") or out["title"])
    if slug in taken:
        slug = f"{slug}-{date.today().strftime('%Y%m%d')}"
    category = out.get("category") if out.get("category") in CATEGORIES else "Market Insight"

    # Render blog post
    tpl = open(TEMPLATE, encoding="utf-8").read()
    body = f'<p class="lead">{out["lead"]}</p>\n' + "\n".join(out["paragraphs"])
    html = (tpl
            .replace("{{TITLE_HTML}}", title_html(out["title"]))
            .replace("{{TITLE}}", out["title"])
            .replace("{{META_DESCRIPTION}}", out["meta_description"].replace('"', "'"))
            .replace("{{KEYWORDS}}", out.get("keywords", "South Tampa real estate"))
            .replace("{{SLUG}}", slug)
            .replace("{{CATEGORY}}", category)
            .replace("{{MONTH_YEAR}}", "<!--POSTDATE-->" + date.today().strftime("%B %-d, %Y") + "<!--/POSTDATE-->")
            .replace("{{ARTICLE_BODY}}", body))

    post_dir = os.path.join(BLOG_DIR, slug)
    os.makedirs(post_dir, exist_ok=True)
    with open(os.path.join(post_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # Queue the GBP post for publishing after merge
    os.makedirs(PENDING_DIR, exist_ok=True)
    gbp = out["gbp_post"].strip()[:1450]  # GBP hard limit is 1500
    with open(os.path.join(PENDING_DIR, f"{slug}.json"), "w", encoding="utf-8") as f:
        json.dump({
            "slug": slug,
            "title": out["title"],
            "topic": topic,
            "tone": tone,
            "day": row["Day"],
            "date": date.today().isoformat(),
            "gbp_post": gbp,
            "image_url": f"https://ignaciotorano.com/blog/{slug}/{slug}-feature.png",
        }, f, indent=2)

    # Mark topic pending
    row["Posted"] = "P"
    save_topics(rows, fields)

    # Outputs for the workflow / PR body
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"slug={slug}\n")
            f.write(f"title={out['title']}\n")
    # PR body written to a file so the workflow can use it
    with open(os.path.join(REPO, "automation", "pr_body.md"), "w", encoding="utf-8") as f:
        f.write(
            f"## {out['title']}\n\n"
            f"**Topic {row['Day']}:** {topic}  \n**Tone:** {tone}  \n**Category:** {category}\n\n"
            "### Google Business Profile post (publishes on merge)\n\n"
            f"> {gbp}\n\n"
            "### Blog article (goes live on merge)\n\n"
            f"Preview file: `blog/{slug}/index.html`\n\n"
            f"*{out['lead']}*\n\n"
            "### Your image\n\n"
            "**Drag your image into a comment on this PR and post it.** It attaches "
            "itself as the feature image automatically (a \u2705 reply confirms it). "
            "Works from your phone too. Any format is fine \u2014 it converts to PNG. "
            "No image, no problem: the blog hides it and the GBP post goes text-only.\n\n"
            "**Merge this PR to publish both. Close it to discard.**\n"
        )
    print(f"Generated: {slug}")


if __name__ == "__main__":
    sys.exit(main())
