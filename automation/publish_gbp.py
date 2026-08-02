#!/usr/bin/env python3
"""
publish_gbp.py
--------------
Runs inside GitHub Actions when a merge to main lands a file in
automation/pending/. For each pending post it:

  1. Waits (briefly) for Netlify to deploy so the feature image URL is live.
  2. Exchanges the stored refresh token for a Google access token.
  3. Publishes the post to Google Business Profile (with the image if it
     resolves, text-only if not).
  4. Moves the JSON from pending/ to posted/ and marks the topic row Y.

Required env vars (GitHub repo secrets):
  GBP_CLIENT_ID, GBP_CLIENT_SECRET, GBP_REFRESH_TOKEN,
  GBP_ACCOUNT_ID, GBP_LOCATION_ID
"""

import csv
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(REPO, "automation", "pending")
POSTED = os.path.join(REPO, "automation", "posted")
TOPICS_CSV = os.path.join(REPO, "automation", "topics.csv")


def get_access_token() -> str:
    data = urllib.parse.urlencode({
        "client_id": os.environ["GBP_CLIENT_ID"],
        "client_secret": os.environ["GBP_CLIENT_SECRET"],
        "refresh_token": os.environ["GBP_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["access_token"]


def url_is_live(url: str, attempts: int = 10, wait: int = 30) -> bool:
    """Retry until the deployed image URL returns 200 (Netlify deploy lag)."""
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        if i < attempts - 1:
            time.sleep(wait)
    return False


def publish(post: dict, token: str):
    body = {
        "languageCode": "en-US",
        "topicType": "STANDARD",
        "summary": post["gbp_post"],
    }
    if url_is_live(post["image_url"]):
        body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": post["image_url"]}]
        print(f"  image attached: {post['image_url']}")
    else:
        print("  no live image found — publishing text-only")

    url = (f"https://mybusiness.googleapis.com/v4/accounts/"
           f"{os.environ['GBP_ACCOUNT_ID']}/locations/"
           f"{os.environ['GBP_LOCATION_ID']}/localPosts")
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
            print(f"  published: {resp.get('name', 'ok')}")
    except urllib.error.HTTPError as e:
        print(f"  GBP API error {e.code}: {e.read().decode()[:500]}")
        raise


def sync_true_date(slug: str):
    """Set the post's visible date to today — the real publish (merge) date."""
    import re
    from datetime import date as _date
    path = os.path.join(REPO, "blog", slug, "index.html")
    if not os.path.exists(path):
        return
    html = open(path, encoding="utf-8").read()
    today = _date.today().strftime("%B %-d, %Y")
    new = re.sub(r"<!--POSTDATE-->.*?<!--/POSTDATE-->",
                 f"<!--POSTDATE-->{today}<!--/POSTDATE-->", html, flags=re.S)
    if new != html:
        open(path, "w", encoding="utf-8").write(new)
        print(f"  date set to {today}")


def mark_posted(day: str):
    with open(TOPICS_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if r["Day"] == day:
            r["Posted"] = "Y"
    with open(TOPICS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Day", "Topic", "Tone", "Posted"])
        w.writeheader()
        w.writerows(rows)


def main():
    if not os.path.isdir(PENDING):
        print("Nothing pending.")
        return 0
    files = [f for f in sorted(os.listdir(PENDING)) if f.endswith(".json")]
    if not files:
        print("Nothing pending.")
        return 0

    token = get_access_token()
    os.makedirs(POSTED, exist_ok=True)
    failures = 0
    for name in files:
        path = os.path.join(PENDING, name)
        post = json.load(open(path, encoding="utf-8"))
        print(f"Publishing {post['slug']} ...")
        try:
            sync_true_date(post["slug"])
            publish(post, token)
            mark_posted(post["day"])
            shutil.move(path, os.path.join(POSTED, name))
        except Exception as e:
            failures += 1
            print(f"  FAILED, will retry on next run: {e}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
