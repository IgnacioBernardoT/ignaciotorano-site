"""
remove_videos.py  -  ignaciotorano.com
Removes the Videos page from the whole site. Run from the repo root:

    python remove_videos.py

What it does:
  1. Removes every "Videos" nav/footer link from all .html files
     (<li><a href=".../videos">Videos</a></li> and bare <a ...>Videos</a> lines).
  2. Deletes videos.html.
  3. netlify.toml: adds 301s for /videos, /videos/, /videos.html -> homepage,
     and repoints the two old redirects that targeted /videos (no redirect chains).
  4. Removes the videos URL from sitemap.xml and the Videos line from llms.txt.
  5. Removes Videos from automation/blog_template.html (future auto posts).

Safe to run more than once. Line endings and encoding are preserved.
"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {".git", "node_modules", ".netlify"}

# A full line that is only a Videos nav/footer link (li-wrapped or bare <a>).
LINK_LINE = re.compile(
    r'^[ \t]*(?:<li>)?<a href="(?:https://ignaciotorano\.com)?/videos(?:\.html)?/?"'
    r'(?: class="active")?>Videos</a>(?:</li>)?[ \t]*\r?\n',
    re.M,
)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


changed, links_removed = [], 0

# 1. HTML links
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in filenames:
        if not name.endswith(".html"):
            continue
        path = os.path.join(dirpath, name)
        if rel(path) == "videos.html":
            continue
        text = read(path)
        new, n = LINK_LINE.subn("", text)
        if n:
            write(path, new)
            changed.append(rel(path))
            links_removed += n

# 2. Delete videos.html
vp = os.path.join(ROOT, "videos.html")
deleted = os.path.exists(vp)
if deleted:
    os.remove(vp)

# 3. netlify.toml
tp = os.path.join(ROOT, "netlify.toml")
toml_note = "not found"
if os.path.exists(tp):
    t = read(tp)
    nl = "\r\n" if "\r\n" in t else "\n"
    orig = t
    # repoint old redirects that sent people to /videos
    t = re.sub(r'(to = ")/videos(")', r'\1/\2', t)
    block, added = "", 0
    for src in ("/videos", "/videos/", "/videos.html"):
        if re.search(r'from = "%s"' % re.escape(src), t):
            continue
        block += f'[[redirects]]{nl}from = "{src}"{nl}to = "/"{nl}status = 301{nl}'
        added += 1
    if block:
        # merge into the existing redirects list: insert right after the last
        # [[redirects]] entry, before the next section (e.g. [context])
        last = t.rfind("[[redirects]]")
        if last == -1:
            t = t + ("" if t.endswith(nl) else nl) + block
        else:
            m = re.compile(r'\r?\n(?=\s*\[(?!\[redirects\]\]))').search(t, last)
            pos = m.end() if m else len(t)
            if not m and not t.endswith(nl):
                t += nl
                pos = len(t)
            t = t[:pos] + block + t[pos:]
    if t != orig:
        write(tp, t)
        changed.append("netlify.toml")
    toml_note = f"{added} redirect(s) added, old /videos targets repointed to /"

# 4. sitemap.xml + llms.txt
sp = os.path.join(ROOT, "sitemap.xml")
if os.path.exists(sp):
    s = read(sp)
    new = re.sub(
        r'[ \t]*<url>\s*<loc>https://ignaciotorano\.com/videos(?:\.html)?/?</loc>.*?</url>[ \t]*\r?\n',
        "", s, flags=re.S)
    if new != s:
        write(sp, new)
        changed.append("sitemap.xml")

lp = os.path.join(ROOT, "llms.txt")
if os.path.exists(lp):
    s = read(lp)
    new = re.sub(r'^.*https://ignaciotorano\.com/videos(?:\.html)?/?\).*\r?\n', "", s, flags=re.M)
    if new != s:
        write(lp, new)
        changed.append("llms.txt")

# 5. automation/blog_template.html is .html, already handled in step 1

print(f"Videos links removed: {links_removed} in {len([c for c in changed if c.endswith('.html')])} HTML files")
print(f"videos.html deleted: {'yes' if deleted else 'already gone'}")
print(f"netlify.toml: {toml_note}")
print(f"Files changed: {len(changed) + (1 if deleted else 0)}")

# Final check: anything left?
left = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in filenames:
        if name.endswith(".html"):
            p = os.path.join(dirpath, name)
            if re.search(r'href="(?:https://ignaciotorano\.com)?/videos(?:\.html)?/?"', read(p)):
                left.append(rel(p))
print("Remaining /videos links: " + (", ".join(left) if left else "none"))
