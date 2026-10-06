# fetch_park_photos.py — v2 with rate limit handling
# Refreshes Google Places photos for every park in parks_data.js.
# Includes automatic retry on 429 Too Many Requests errors.

import json, os, re, time, urllib.request, urllib.error

API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip()
if not API_KEY:
    raise SystemExit("Set GOOGLE_API_KEY first")
PHOTO_KEY = os.environ.get("PHOTO_KEY", API_KEY).strip()

MAX_PHOTOS_PER_PARK = 3
PHOTO_WIDTH = 800
BASE_DELAY = 0.6   # 600ms between requests (was 150ms) — stays under quota
RETRY_DELAYS = [2, 5, 15, 30, 60]  # back-off waits when hit with 429

with open("parks_data.js", "r", encoding="utf-8") as f:
    raw = f.read()
raw = re.sub(r"^\s*const\s+PARKS_DATA\s*=\s*", "", raw).rstrip().rstrip(";")
parks = json.loads(raw)
print(f"Loaded {len(parks)} parks")

def search_place(park):
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
        return json.loads(r.read().decode())

def search_with_retry(park):
    """Search with automatic retry on 429."""
    for attempt, delay in enumerate([0] + RETRY_DELAYS):
        if delay > 0:
            print(f"    rate limited — waiting {delay}s before retry {attempt}...")
            time.sleep(delay)
        try:
            data = search_place(park)
            places = data.get("places") or [None]
            return places[0]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < len(RETRY_DELAYS):
                continue  # retry with longer delay
            raise

result = {}
result_by_name = {}
missing = []
for i, p in enumerate(parks, 1):
    oid = str(p["OBJECTID"])
    try:
        place = search_with_retry(p)
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
            result_by_name[p["NAME"].lower().strip()] = urls
            print(f"[{i}/{len(parks)}] {p['NAME']}: {len(urls)} photo(s)")
        else:
            missing.append(p["NAME"])
            print(f"[{i}/{len(parks)}] {p['NAME']}: no photos")
    except Exception as e:
        missing.append(p["NAME"])
        print(f"[{i}/{len(parks)}] {p['NAME']}: ERROR {e}")
    # Save progress every 20 parks so a crash doesn't lose everything
    if i % 20 == 0:
        with open("park_photos.js", "w", encoding="utf-8") as f:
            f.write("const PARK_PHOTOS = ")
            json.dump(result, f)
            f.write(";\n")
            f.write("const PARK_PHOTOS_BY_NAME = ")
            json.dump(result_by_name, f)
            f.write(";\n")
    time.sleep(BASE_DELAY)

with open("park_photos.js", "w", encoding="utf-8") as f:
    f.write("const PARK_PHOTOS = ")
    json.dump(result, f)
    f.write(";\n")
    f.write("const PARK_PHOTOS_BY_NAME = ")
    json.dump(result_by_name, f)
    f.write(";\n")

print(f"\nDone. {len(result)}/{len(parks)} parks with photos.")
if missing:
    print(f"{len(missing)} missing (will show illustrated placeholders):")
    for n in missing: print("  -", n)
