#!/usr/bin/env python3
"""
attach_image.py
---------------
Runs when Ignacio drops an image into a comment on a draft PR.
Downloads the image, converts it to PNG, sizes it sensibly, and saves it
as blog/<slug>/<slug>-feature.png on the PR branch.

Env vars provided by the workflow:
  IMAGE_URL   first image URL found in the comment
  SLUG        post slug (from the branch name post/<slug>)
  GITHUB_TOKEN  used for authenticated download of the attachment
"""

import io
import os
import sys
import urllib.request

from PIL import Image

MAX_SIDE = 1600


def main():
    url = os.environ["IMAGE_URL"]
    slug = os.environ["SLUG"]
    token = os.environ.get("GITHUB_TOKEN", "")

    req = urllib.request.Request(url)
    if token and ("github" in url):
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "gbp-automation")
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()

    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)

    out_dir = os.path.join("blog", slug)
    if not os.path.isdir(out_dir):
        print(f"ERROR: blog/{slug}/ not found on this branch")
        return 1
    out_path = os.path.join(out_dir, f"{slug}-feature.png")
    img.save(out_path, "PNG")
    print(f"saved {out_path} ({img.size[0]}x{img.size[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
