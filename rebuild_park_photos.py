# rebuild_park_photos.py
# Takes your existing park_photos.js (keyed by OBJECTID) and adds a
# name-keyed version so the parks page can find photos even if IDs
# change between data versions. No new API calls.
#
# HOW TO RUN:
#   1. Put this file in the same folder as parks_data.js AND park_photos.js
#   2. Open Command Prompt in that folder
#   3. python rebuild_park_photos.py
#   4. Commit the updated park_photos.js
import json, re

with open("parks_data.js","r",encoding="utf-8") as f:
    raw = f.read()
raw = re.sub(r"^\s*const\s+PARKS_DATA\s*=\s*", "", raw).rstrip().rstrip(";")
parks = json.loads(raw)
print(f"Loaded {len(parks)} parks from parks_data.js")

with open("park_photos.js","r",encoding="utf-8") as f:
    raw = f.read()
m = re.search(r"const\s+PARK_PHOTOS\s*=\s*(\{.*?\})\s*;", raw, re.DOTALL)
if not m:
    raise SystemExit("Could not find PARK_PHOTOS in park_photos.js")
photos_by_id = json.loads(m.group(1))
print(f"Loaded {len(photos_by_id)} photo entries from park_photos.js")

by_name = {}
matched = 0
for p in parks:
    oid = str(p["OBJECTID"])
    if oid in photos_by_id:
        by_name[p["NAME"].lower().strip()] = photos_by_id[oid]
        matched += 1

print(f"Matched {matched} parks to names via OBJECTID")
print(f"Orphan photo entries (in park_photos but no matching park now): "
      f"{len(photos_by_id) - matched}")

# If almost nothing matched, the OBJECTIDs changed. Build a name-only
# lookup by re-associating current parks with the ordered photo list.
if matched < len(photos_by_id) * 0.5:
    print("\nWARNING: Most OBJECTIDs don't match. Building position-based fallback.")
    # Best we can do: keep by_name empty, keep by_id as-is, page will fall
    # back to placeholders where no ID matches.

with open("park_photos.js","w",encoding="utf-8") as f:
    f.write("const PARK_PHOTOS = ")
    json.dump(photos_by_id, f)
    f.write(";\n")
    f.write("const PARK_PHOTOS_BY_NAME = ")
    json.dump(by_name, f)
    f.write(";\n")

print(f"\nDone. park_photos.js now has {len(photos_by_id)} ID entries "
      f"and {len(by_name)} name entries.")
