# fetch_park_photos.py
# Refreshes Google Places photos for every park in parks_data.js
# and writes park_photos.js. Google photo IDs expire, so rerun periodically.
#
# HOW TO RUN (Windows):
#   1. Put this file in your ignaciotorano-site folder
#   2. Open Command Prompt in that folder
#   3. set GOOGLE_API_KEY=your_places_api_key
#      set PHOTO_KEY=your_referrer_restricted_public_key
#      python fetch_park_photos.py
#   4. Commit ONLY the generated park_photos.js to your repo — NOT this file.

import json, os, re, time, urllib.request

API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip()
if not API_KEY:
    raise SystemExit("Set GOOGLE_API_KEY first:  set GOOGLE_API_KEY=your_key")
PHOTO_KEY = os.environ.get("PHOTO_KEY", API_KEY).strip()

MAX_PHOTOS_PER_PARK = 3
PHOTO_WIDTH = 800

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
        data = json.loads(r.read().decode())
    return (data.get("places") or [None])[0]

result = {}
result_by_name = {}
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
            result_by_name[p["NAME"].lower().strip()] = urls
            print(f"[{i}/{len(parks)}] {p['NAME']}: {len(urls)} photo(s)")
        else:
            missing.append(p["NAME"])
            print(f"[{i}/{len(parks)}] {p['NAME']}: no photos found")
    except Exception as e:
        missing.append(p["NAME"])
        print(f"[{i}/{len(parks)}] {p['NAME']}: ERROR {e}")
    time.sleep(0.15)

with open("park_photos.js", "w", encoding="utf-8") as f:
    f.write("const PARK_PHOTOS = ")
    json.dump(result, f)
    f.write(";\n")
    f.write("const PARK_PHOTOS_BY_NAME = ")
    json.dump(result_by_name, f)
    f.write(";\n")

print(f"\nDone. {len(result)} parks with photos -> park_photos.js")
if missing:
    print(f"{len(missing)} parks had no Google photos (illustrated placeholders will show):")
    for n in missing:
        print("  -", n)
