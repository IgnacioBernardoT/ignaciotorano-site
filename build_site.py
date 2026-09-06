"""
build_sitemap.py — run from the root of the ignaciotorano-site folder:
    python build_sitemap.py

Scans every .html file and writes sitemap.xml with the correct public URL:
  index.html                -> https://ignaciotorano.com/
  blog.html                 -> https://ignaciotorano.com/blog        (extensionless)
  neighborhoods/index.html  -> https://ignaciotorano.com/neighborhoods/
  blog/<slug>/index.html    -> https://ignaciotorano.com/blog/<slug>/
  resources/quiz.html       -> https://ignaciotorano.com/resources/quiz
Uses each file's last-modified date for <lastmod>.
"""
import pathlib, datetime

SITE = "https://ignaciotorano.com"

# Folders that never contain public pages
SKIP_DIRS = {".git", ".github", "node_modules", "netlify", "emails", "automation",
             "gbp-automation", "templates", "template", "scripts", "python"}
# Individual files that should not be indexed
SKIP_FILES = {"404.html", "quiz.html_root_placeholder"}
# Root-level files that are duplicates/redirects (add here if any remain)
SKIP_PATHS = {"quiz.html", "resources/purchasing-power-quiz.html"}

# Priorities by section (optional hint for Google)
def priority(url):
    if url == SITE + "/": return "1.0"
    if "/nbhd_" in url or "/neighborhoods/" == url[-15:] or url.endswith("/parks"): return "0.9"
    if "/blog/" in url or "/resources/" in url: return "0.7"
    if "/neighborhoods/communities/" in url or "/news/" in url: return "0.6"
    return "0.8"

root = pathlib.Path(".")
entries = []

for p in sorted(root.rglob("*.html")):
    parts = p.parts
    if any(part in SKIP_DIRS for part in parts[:-1]): continue
    if p.name in SKIP_FILES or p.as_posix() in SKIP_PATHS: continue

    rel = p.as_posix()
    if p.name == "index.html":
        url = SITE + "/" + rel[:-len("index.html")]          # dir/ or /
    else:
        url = SITE + "/" + rel[:-len(".html")]               # extensionless
    url = url.replace("//", "/").replace("https:/", "https://")

    mod = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
    entries.append((url, mod, priority(url)))

xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for url, mod, pri in entries:
    xml.append(f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{mod}</lastmod>\n    <priority>{pri}</priority>\n  </url>")
xml.append("</urlset>\n")

pathlib.Path("sitemap.xml").write_text("\n".join(xml), encoding="utf-8")
print(f"sitemap.xml written with {len(entries)} URLs")
for url, _, _ in entries[:200]:
    print(" ", url)
