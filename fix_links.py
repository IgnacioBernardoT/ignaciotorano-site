"""
fix_links.py — run from the root of the ignaciotorano-site folder:
    python fix_links.py
Rewrites known-broken internal links in every .html file.
"""
import pathlib, re

REPLACEMENTS = [
    ('href="/tampa-parks-guide.html"', 'href="/parks"'),
    ('href="tampa-parks-guide.html"', 'href="/parks"'),
    ('href="/blog-port-tampa.html"', 'href="/blog/port-tampa-living/"'),
    ('href="/blog/davis-islands-worth-it-2026/"', 'href="/neighborhoods/communities/davis-islands"'),
    ('href="/neighborhoods"', 'href="/neighborhoods/"'),
    ('href="/resources/purchasing-power-quiz"', 'href="/resources/quiz"'),
]
# Relative links that only make sense from the root; make them absolute everywhere
RELATIVE = [
    (re.compile(r'href="videos\.html"'), 'href="/videos"'),
    (re.compile(r'href="blog\.html"'), 'href="/blog"'),
    (re.compile(r'href="index\.html"'), 'href="/"'),
    (re.compile(r'href="parks\.html"'), 'href="/parks"'),
    (re.compile(r'href="/videos\.html"'), 'href="/videos"'),
    (re.compile(r'href="/blog\.html"'), 'href="/blog"'),
    (re.compile(r'href="/parks\.html"'), 'href="/parks"'),
]

SKIP_DIRS = {".git", ".github", "node_modules", "netlify", "emails", "automation", "gbp-automation"}
changed = 0; total = 0
for p in pathlib.Path(".").rglob("*.html"):
    if any(part in SKIP_DIRS for part in p.parts[:-1]): continue
    s = orig = p.read_text(encoding="utf-8", errors="ignore")
    for a, b in REPLACEMENTS:
        s = s.replace(a, b)
    for pat, b in RELATIVE:
        s = pat.sub(b, s)
    if s != orig:
        p.write_text(s, encoding="utf-8"); changed += 1
        total += sum(orig.count(a) for a, _ in REPLACEMENTS)
print(f"Files updated: {changed}")
