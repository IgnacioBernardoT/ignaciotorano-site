#!/usr/bin/env python3
"""
generate_sitemap.py
-------------------
Builds a complete sitemap.xml for ignaciotorano.com by pulling every
blog post folder from the GitHub repo. Run this whenever you publish
new posts and commit the result — your sitemap stays in sync automatically.

Usage:
    python generate_sitemap.py

Output:
    sitemap.xml in the current folder.

No dependencies beyond the Python standard library.
"""

import json
import urllib.request
import urllib.error
from datetime import date

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
OWNER = "IgnacioBernardoT"
REPO = "ignaciotorano-site"
DOMAIN = "https://ignaciotorano.com"
BLOG_PATH = "blog"  # folder in the repo that holds post sub-folders

# Static (non-blog) pages to always include, with their priority.
STATIC_PAGES = [
    ("/",            "1.0", "weekly"),
    ("/videos.html", "0.8", "weekly"),
    ("/blog.html",   "0.9", "weekly"),
]

# The dog-rescue post carries a <video:video> block. Add any video posts here
# keyed by their folder slug so the video metadata is preserved.
VIDEO_POSTS = {
    "tampa-dog-rescue": {
        "thumbnail": "https://img.youtube.com/vi/k4D4dwwW-gs/maxresdefault.jpg",
        "title": "Dog Rescue at Davis Islands Dog Park - Tampa, FL",
        "description": ("Dramatic video of a dog being revived after near-drowning at "
                        "Davis Islands Dog Park in Tampa, Florida. Filmed by Ignacio "
                        "Torano, Tampa real estate professional."),
        "player": "https://www.youtube.com/embed/k4D4dwwW-gs",
        "duration": "120",
        "publication_date": "2026-05-22",
    },
}

# Slugs to skip (junk folders, drafts, etc.) if any ever appear.
SKIP_SLUGS = set()


# ---------------------------------------------------------------------------
# FETCH BLOG FOLDERS FROM GITHUB
# ---------------------------------------------------------------------------
def get_blog_slugs():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{BLOG_PATH}"
    req = urllib.request.Request(url, headers={"User-Agent": "sitemap-generator"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            items = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"GitHub API error {e.code}: {e.reason}. "
                         f"Check OWNER/REPO and that the repo is public.")
    slugs = [
        it["name"] for it in items
        if it.get("type") == "dir" and it["name"] not in SKIP_SLUGS
    ]
    return sorted(slugs)


def get_last_commit_date(slug):
    """Return YYYY-MM-DD of the most recent commit touching this post folder."""
    url = (f"https://api.github.com/repos/{OWNER}/{REPO}/commits"
           f"?path={BLOG_PATH}/{slug}&per_page=1")
    req = urllib.request.Request(url, headers={"User-Agent": "sitemap-generator"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            commits = json.loads(resp.read().decode())
        if commits:
            return commits[0]["commit"]["committer"]["date"][:10]
    except Exception:
        pass
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# BUILD XML
# ---------------------------------------------------------------------------
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def url_block(loc, lastmod, priority, changefreq, video=None):
    lines = [
        "  <url>",
        f"    <loc>{loc}</loc>",
        f"    <lastmod>{lastmod}</lastmod>",
        f"    <changefreq>{changefreq}</changefreq>",
        f"    <priority>{priority}</priority>",
    ]
    if video:
        lines += [
            "    <video:video>",
            f"      <video:thumbnail_loc>{video['thumbnail']}</video:thumbnail_loc>",
            f"      <video:title>{esc(video['title'])}</video:title>",
            f"      <video:description>{esc(video['description'])}</video:description>",
            f"      <video:player_loc>{video['player']}</video:player_loc>",
            f"      <video:duration>{video['duration']}</video:duration>",
            f"      <video:publication_date>{video['publication_date']}</video:publication_date>",
            "    </video:video>",
        ]
    lines.append("  </url>")
    return "\n".join(lines)


def build_sitemap():
    today = date.today().isoformat()
    blocks = []

    # Static pages first
    for path, priority, changefreq in STATIC_PAGES:
        blocks.append(url_block(f"{DOMAIN}{path}", today, priority, changefreq))

    # Blog posts
    slugs = get_blog_slugs()
    print(f"Found {len(slugs)} blog post folders.")
    for slug in slugs:
        loc = f"{DOMAIN}/{BLOG_PATH}/{slug}/"
        lastmod = get_last_commit_date(slug)
        video = VIDEO_POSTS.get(slug)
        blocks.append(url_block(loc, lastmod, "0.9", "monthly", video=video))
        print(f"  + {slug}  ({lastmod})")

    header = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
              '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"\n'
              '        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">')
    return header + "\n" + "\n".join(blocks) + "\n</urlset>\n"


if __name__ == "__main__":
    xml = build_sitemap()
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml)
    print("\nWrote sitemap.xml")
