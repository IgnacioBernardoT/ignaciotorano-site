"""
fix_titles.py — run from the root of the ignaciotorano-site folder:
    python fix_titles.py
Shortens <title> tags in blog posts and news pages:
  1. removes " | South Tampa Realtor"
  2. if still longer than 60 characters, also removes " | Ignacio Toraño"
Prints every title it changed and its new length.
"""
import pathlib, re, html

MAX = 60
files = list(pathlib.Path("blog").glob("*/index.html")) + list(pathlib.Path("news").glob("*.html"))
changed = 0
for p in files:
    s = orig = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    if not m:
        continue
    t = html.unescape(m.group(1)).strip()
    new = t.replace(" | South Tampa Realtor", "")
    if len(new) > MAX:
        new = new.replace(" | Ignacio Toraño", "")
    if new != t:
        s = s.replace(m.group(0), f"<title>{html.escape(new, quote=False)}</title>", 1)
        p.write_text(s, encoding="utf-8")
        changed += 1
        flag = "" if len(new) <= MAX else "  (still long — shorten by hand)"
        print(f"{len(new):3d}  {new}{flag}")
print(f"\nTitles updated: {changed}")
