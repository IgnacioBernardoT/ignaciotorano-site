# fetch_custom_park_photos.py
# Refreshes Google Places photos for every park in custom_parks.js
# and writes custom_park_photos.js.

import json, os, re, time, urllib.request

API_KEY = os.environ.get("GOOGLE_API_KEY","").strip()
PHOTO_KEY = os.environ.get("PHOTO_KEY", API_KEY).strip()
if not API_KEY:
    raise SystemExit("Set GOOGLE_API_KEY first")

MAX_PHOTOS = 3
PHOTO_WIDTH = 800

with open("custom_parks.js","r",encoding="utf-8") as f:
    raw = f.read()
raw = re.sub(r"^\s*const\s+CUSTOM_PARKS\s*=\s*","",raw).rstrip().rstrip(";")
parks = json.loads(raw)
print(f"Loaded {len(parks)} parks from custom_parks.js")

def search(name, addr, lat, lng):
    body = json.dumps({
        "textQuery": f"{name}, {addr}",
        "locationBias": {"circle": {
            "center": {"latitude": lat, "longitude": lng},
            "radius": 2000.0}},
        "pageSize": 1,
    }).encode()
    req = urllib.request.Request(
        "https://places.googleapis.com/v1/places:searchText",
        data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "places.photos",
        })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

photos_by_id, photos_by_name = {}, {}
missing = []
for i, p in enumerate(parks, 1):
    oid = str(p["OBJECTID"])
    try:
        data = search(p["NAME"], p["FULLADDR"], p["_lat"], p["_lng"])
        place = (data.get("places") or [None])[0]
        photos = (place or {}).get("photos") or []
        urls = []
        for ph in photos[:MAX_PHOTOS]:
            n = ph.get("name")
            if n:
                urls.append(
                    f"https://places.googleapis.com/v1/{n}/media"
                    f"?maxWidthPx={PHOTO_WIDTH}&key={PHOTO_KEY}")
        if urls:
            photos_by_id[oid] = urls
            photos_by_name[p["NAME"].lower().strip()] = urls
            print(f"[{i}/{len(parks)}] {p['NAME']}: {len(urls)} photo(s)")
        else:
            missing.append(p["NAME"])
            print(f"[{i}/{len(parks)}] {p['NAME']}: no photos found")
    except Exception as e:
        missing.append(p["NAME"])
        print(f"[{i}/{len(parks)}] {p['NAME']}: ERROR {e}")
    time.sleep(0.15)

with open("custom_park_photos.js","w",encoding="utf-8") as f:
    f.write("const CUSTOM_PARK_PHOTOS = ")
    json.dump(photos_by_id, f)
    f.write(";\n")
    f.write("const CUSTOM_PARK_PHOTOS_BY_NAME = ")
    json.dump(photos_by_name, f)
    f.write(";\n")

print(f"\nDone. {len(photos_by_id)} parks with photos -> custom_park_photos.js")
if missing:
    print(f"{len(missing)} parks without Google photos (illustrated placeholders):")
    for n in missing: print("  -", n)
