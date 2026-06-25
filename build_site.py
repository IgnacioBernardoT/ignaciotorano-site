#!/usr/bin/env python3
"""
build_site.py
-------------
One script that keeps ignaciotorano.com in sync after you publish posts:

  1. Scans the local ./blog/ folder for post sub-folders.
  2. Reads each post's index.html for its real title, excerpt, category, image.
  3. Writes a complete sitemap.xml (all posts + static pages).
  4. Injects static HTML cards for every folder-post into blog.html,
     sorted newest-first, between two markers.

Run it from your repo folder (where blog.html and the blog/ folder live):

    python build_site.py

Then commit + push in GitHub Desktop. No GitHub API calls, no network needed —
it reads the files already on your computer, so it's fast and never rate-limited.

Markers it writes between in blog.html:
    <!--AUTO_POSTS_START--> ... <!--AUTO_POSTS_END-->
The first run replaces the old <!--NEW_POST_INSERT_HERE--> marker with these.
"""

import os
import re
import html
from datetime import date, datetime

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DOMAIN = "https://ignaciotorano.com"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR = os.path.join(REPO_DIR, "blog")
BLOG_HTML = os.path.join(REPO_DIR, "blog.html")
SITEMAP = os.path.join(REPO_DIR, "sitemap.xml")

START_MARKER = "<!--AUTO_POSTS_START-->"
END_MARKER = "<!--AUTO_POSTS_END-->"
LEGACY_MARKER = "<!--NEW_POST_INSERT_HERE-->"

STATIC_PAGES = [
    ("/",            "1.0", "weekly"),
    ("/videos.html", "0.8", "weekly"),
    ("/blog.html",   "0.9", "weekly"),
]

# Posts that carry a <video:video> block in the sitemap, keyed by slug.
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

SKIP_SLUGS = set()


# ---------------------------------------------------------------------------
# READ POSTS
# ---------------------------------------------------------------------------
def read_meta(tag_html, slug):
    """Pull title, description, category, image, date from a post's index.html."""
    # Title: text before the first "|", else cleaned slug
    m = re.search(r"<title>(.*?)</title>", tag_html, re.S | re.I)
    if m:
        title = m.group(1).split("|")[0].strip()
        title = html.unescape(title)
    else:
        title = slug.replace("-", " ").title()

    # Excerpt: meta description. Match the opening quote char and read until the
    # SAME quote char, so apostrophes inside a double-quoted value are kept.
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=(["\'])(.*?)\1',
                  tag_html, re.S | re.I)
    excerpt = html.unescape(m.group(2).strip()) if m else "Read the full article."

    # Category: text in the hero eyebrow div, before any "·"
    m = re.search(r'class=["\']eyebrow["\'][^>]*>(.*?)</div>', tag_html, re.S | re.I)
    if m:
        category = re.sub(r"<[^>]+>", "", m.group(1)).split("·")[0].strip()
        category = html.unescape(category)
    else:
        category = "South Tampa"

    return title, excerpt, category


def post_date(folder):
    """Most recent mtime of files in the post folder (newest-first sort key)."""
    latest = 0
    for root, _, files in os.walk(folder):
        for f in files:
            try:
                latest = max(latest, os.path.getmtime(os.path.join(root, f)))
            except OSError:
                pass
    return latest or os.path.getmtime(folder)


def collect_posts():
    posts = []
    for name in sorted(os.listdir(BLOG_DIR)):
        folder = os.path.join(BLOG_DIR, name)
        index = os.path.join(folder, "index.html")
        if not os.path.isdir(folder) or name in SKIP_SLUGS:
            continue
        if not os.path.isfile(index):
            continue
        with open(index, "r", encoding="utf-8", errors="replace") as fh:
            tag_html = fh.read()
        title, excerpt, category = read_meta(tag_html, name)
        # feature image: {slug}-feature.png if present, else fallback banner
        feat = f"{name}-feature.png"
        img = f"blog/{name}/{feat}" if os.path.isfile(os.path.join(folder, feat)) \
            else "tampa_banner.png"
        mtime = post_date(folder)
        posts.append({
            "slug": name, "title": title, "excerpt": excerpt,
            "category": category, "img": img,
            "mtime": mtime,
            "date_label": datetime.fromtimestamp(mtime).strftime("%B %Y"),
            "lastmod": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d"),
        })
    posts.sort(key=lambda p: p["mtime"], reverse=True)  # newest first
    return posts


# ---------------------------------------------------------------------------
# BUILD BLOG CARDS
# ---------------------------------------------------------------------------
def card_html(p):
    t = html.escape(p["title"])
    e = html.escape(p["excerpt"])
    c = html.escape(p["category"])
    return f'''      <a class="blog-card" href="blog/{p['slug']}/" style="text-decoration:none;color:inherit">
        <div class="blog-thumb">
          <img src="{p['img']}" alt="{t}" loading="lazy" onerror="this.onerror=null;this.src='tampa_banner.png'">
          <span class="blog-category">{c}</span>
        </div>
        <div class="blog-body">
          <p class="blog-date">{p['date_label']}</p>
          <h3 class="blog-card-title">{t}</h3>
          <p class="blog-excerpt">{e}</p>
          <span class="blog-read-more">Read Article &#8594;</span>
        </div>
      </a>'''


def inject_cards(posts):
    with open(BLOG_HTML, "r", encoding="utf-8") as fh:
        doc = fh.read()

    cards = "\n".join(card_html(p) for p in posts)
    block = f"{START_MARKER}\n{cards}\n      {END_MARKER}"

    if START_MARKER in doc and END_MARKER in doc:
        doc = re.sub(
            re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
            block, doc, flags=re.S)
    elif LEGACY_MARKER in doc:
        doc = doc.replace(LEGACY_MARKER, block, 1)
    else:
        raise SystemExit(
            "Couldn't find insertion markers in blog.html. Add "
            f"{LEGACY_MARKER} where cards should go, then re-run.")

    with open(BLOG_HTML, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return len(posts)


# ---------------------------------------------------------------------------
# BUILD SITEMAP
# ---------------------------------------------------------------------------
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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


def build_sitemap(posts):
    today = date.today().isoformat()
    blocks = [url_block(f"{DOMAIN}{p}", today, pr, cf) for p, pr, cf in STATIC_PAGES]
    for p in posts:
        loc = f"{DOMAIN}/blog/{p['slug']}/"
        blocks.append(url_block(loc, p["lastmod"], "0.9", "monthly",
                                video=VIDEO_POSTS.get(p["slug"])))
    header = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
              '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"\n'
              '        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">')
    with open(SITEMAP, "w", encoding="utf-8") as fh:
        fh.write(header + "\n" + "\n".join(blocks) + "\n</urlset>\n")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not os.path.isdir(BLOG_DIR):
        raise SystemExit(f"No blog/ folder found at {BLOG_DIR}. "
                         "Run this from your repo folder.")
    posts = collect_posts()
    print(f"Found {len(posts)} posts.\n")
    for p in posts:
        print(f"  {p['lastmod']}  {p['slug']}")
    n = inject_cards(posts)
    build_sitemap(posts)
    print(f"\nInjected {n} static cards into blog.html")
    print(f"Wrote sitemap.xml with {len(posts) + len(STATIC_PAGES)} URLs")
    print("\nNext: commit + push in GitHub Desktop.")
