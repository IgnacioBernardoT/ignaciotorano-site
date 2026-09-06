"""
fix_images.py — run from the root of the ignaciotorano-site folder:
    python fix_images.py
For each blog post, if the feature image it references doesn't exist on disk,
remove the <div class="feature-img">...</div> block. Also makes root-relative
the two logo/headshot images in port-tampa-living.
"""
import pathlib, re

removed = 0
for post in pathlib.Path("blog").glob("*/index.html"):
    s = orig = post.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<div class="feature-img">\s*<img src="([^"]+)"[^>]*>\s*</div>\s*', s)
    if m:
        img = m.group(1)
        img_path = post.parent / img if not img.startswith("/") else pathlib.Path(img.lstrip("/"))
        if not img_path.exists():
            s = s.replace(m.group(0), "", 1)
            removed += 1
    s = s.replace('src="iggy_logo_v2.webp"', 'src="/iggy_logo_v2.webp"')
    s = s.replace('src="iggy_headshot_v2.webp"', 'src="/iggy_headshot_v2.webp"')
    if s != orig:
        post.write_text(s, encoding="utf-8")
print(f"Feature-image tags removed (missing files): {removed}")
