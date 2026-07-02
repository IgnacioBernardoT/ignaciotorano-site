// netlify/functions/google-reviews.js
// Pulls live Google reviews via the Places API (New).
//
// Required environment variables (Netlify → Site configuration →
// Environment variables):
//   GOOGLE_PLACES_API_KEY  – Google Cloud API key with "Places API (New)" enabled
//   GOOGLE_PLACE_ID        – the Place ID for the business listing
//
// Response shape matches what index.html expects:
//   { reviews: [{ author, rating, text, relativeTime }], rating, total }

let cache = { data: null, fetchedAt: 0 };
const CACHE_TTL_MS = 6 * 60 * 60 * 1000; // 6 hours

exports.handler = async function () {
  const apiKey = process.env.GOOGLE_PLACES_API_KEY;
  const placeId = process.env.GOOGLE_PLACE_ID;

  if (!apiKey || !placeId) {
    return json(500, { error: "Missing GOOGLE_PLACES_API_KEY or GOOGLE_PLACE_ID env var" });
  }

  // Serve from cache if fresh
  if (cache.data && Date.now() - cache.fetchedAt < CACHE_TTL_MS) {
    return json(200, cache.data, true);
  }

  try {
    const url = `https://places.googleapis.com/v1/places/${encodeURIComponent(placeId)}`;
    const res = await fetch(url, {
      headers: {
        "X-Goog-Api-Key": apiKey,
        "X-Goog-FieldMask": "rating,userRatingCount,reviews",
      },
    });
    const data = await res.json();

    if (!res.ok) {
      return json(502, {
        error: "Google Places API (New) error",
        status: res.status,
        message: (data.error && data.error.message) || "",
      });
    }

    const payload = {
      rating: data.rating || null,
      total: data.userRatingCount || 0,
      reviews: (data.reviews || [])
        .filter((r) => (r.rating || 0) >= 4 && r.text && (r.text.text || "").trim().length > 0)
        .slice(0, 6)
        .map((r) => ({
          author: (r.authorAttribution && r.authorAttribution.displayName) || "Google User",
          rating: r.rating || 5,
          text: r.text.text.trim(),
          relativeTime: r.relativePublishTimeDescription || "",
        })),
    };

    cache = { data: payload, fetchedAt: Date.now() };
    return json(200, payload);
  } catch (err) {
    if (cache.data) return json(200, cache.data, true);
    return json(500, { error: "Failed to fetch reviews", message: err.message });
  }
};

function json(statusCode, body, fromCache = false) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": statusCode === 200 ? "public, max-age=21600" : "no-store",
      "X-Cache": fromCache ? "HIT" : "MISS",
    },
    body: JSON.stringify(body),
  };
}
