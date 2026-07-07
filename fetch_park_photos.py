# fetch_park_photos.py
# Fetches real Google Places photos for every park in parks_data.js
# and writes park_photos.js for the parks page to use as photo fallback.
#
# HOW TO RUN (Windows):
#   1. Put this file in the same folder as parks_data.js
#   2. Open Command Prompt in that folder
#   3. Set your key:   set GOOGLE_API_KEY=YOUR_PLACES_API_KEY
#   4. Run:            python fetch_park_photos.py
#   5. Commit the generated park_photos.js to your site repo
#
# Cost estimate (one-time): ~189 Text Search calls (~$6). Photo serving
# happens at page-view time via Google's photo endpoint.
# IMPORTANT: restrict the API key to your domain (HTTP referrer
# ignaciotorano.com/*) in Google Cloud Console before deploying, since
# the key appears in the generated photo URLs.

import json, os, re, time, urllib.request, urllib.parse

API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip()
if not API_KEY:
    raise SystemExit("Set GOOGLE_API_KEY first:  set GOOGLE_API_KEY=your_key")
# Optional second key embedded in the public photo URLs. Use a key that is
# referrer-restricted to ignaciotorano.com/* so nobody can steal it.
# If not set, the main key is used.
PHOTO_KEY = os.environ.get("PHOTO_KEY", API_KEY).strip()

MAX_PHOTOS_PER_PARK = 3
PHOTO_WIDTH = 800

# ---- load parks_data.js ----
with open("parks_data.js", "r", encoding="utf-8") as f:
    raw = f.read()
raw = re.sub(r"^\s*const\s+PARKS_DATA\s*=\s*", "", raw).rstrip().rstrip(";")
parks = json.loads(raw)
print(f"Loaded {len(parks)} parks")

def search_place(park):
    """Text Search (New) -> first place with photos."""
    body = json.dumps({
        "textQuery": f"{park['NAME']}, {park.get('FULLADDR','')}, Tampa FL",
        "locationBias": {"circle": {
            "center": {"latitude": park.get("_lat", 27.95),
                        "longitude": park.get("_lng", -82.46)},
            "radius": 2000.0}},
        "pageSize": 1,
    }).encode()
    req = urllib.request.Request(
        "https://places.googleapis.com/v1/places:searchText",
        data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.id,places.displayName,places.photos",
        })
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    return (data.get("places") or [None])[0]

result = {}
missing = []
for i, p in enumerate(parks, 1):
    oid = str(p["OBJECTID"])
    try:
        place = search_place(p)
        photos = (place or {}).get("photos") or []
        urls = []
        for ph in photos[:MAX_PHOTOS_PER_PARK]:
            name = ph.get("name")
            if name:
                urls.append(
                    f"https://places.googleapis.com/v1/{name}/media"
                    f"?maxWidthPx={PHOTO_WIDTH}&key={PHOTO_KEY}")
        if urls:
            result[oid] = urls
            print(f"[{i}/{len(parks)}] {p['NAME']}: {len(urls)} photo(s)")
        else:
            missing.append(p["NAME"])
            print(f"[{i}/{len(parks)}] {p['NAME']}: no photos found")
    except Exception as e:
        missing.append(p["NAME"])
        print(f"[{i}/{len(parks)}] {p['NAME']}: ERROR {e}")
    time.sleep(0.15)  # gentle rate limit

with open("park_photos.js", "w", encoding="utf-8") as f:
    f.write("const PARK_PHOTOS = ")
    json.dump(result, f)
    f.write(";\n")

print(f"\nDone. {len(result)} parks with photos -> park_photos.js")
if missing:
    print(f"{len(missing)} parks had no Google photos (illustrated "
          f"placeholders will show for these):")
    for n in missing:
        print("  -", n)
