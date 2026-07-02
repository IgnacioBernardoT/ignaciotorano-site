// netlify/functions/google-reviews.js
// Pulls live Google reviews for Ignacio's Google Business Profile
// via the Google Places API (Place Details endpoint).
//
// Required environment variables (set in Netlify → Site settings →
// Environment variables):
//   GOOGLE_PLACES_API_KEY  – a Google Cloud API key with "Places API" enabled
//   GOOGLE_PLACE_ID        – the Place ID for the business listing
//
// Response shape matches what index.html already expects:
//   { reviews: [{ author, rating, text, relativeTime }], rating, total }

let cache = { data: null, fetchedAt: 0 };
const CACHE_TTL_MS = 6 * 60 * 60 * 1000; // 6 hours

exports.handler = async function () {
  const apiKey = process.env.GOOGLE_PLACES_API_KEY;
  const placeId = process.env.GOOGLE_PLACE_ID;

  if (!apiKey || !placeId) {
    return json(500, { error: "Missing GOOGLE_PLACES_API_KEY or GOOGLE_PLACE_ID env var" });
  }

  // Serve from cache if fresh (keeps API usage tiny)
  if (cache.data && Date.now() - cache.fetchedAt < CACHE_TTL_MS) {
    return json(200, cache.data, true);
  }

  try {
    const url =
      "https://maps.googleapis.com/maps/api/place/details/json" +
      `?place_id=${encodeURIComponent(placeId)}` +
      "&fields=reviews,rating,user_ratings_total" +
      "&reviews_sort=newest" +
      `&key=${apiKey}`;

    const res = await fetch(url);
    const data = await res.json();

    if (data.status !== "OK") {
      return json(502, { error: "Google Places API error", status: data.status, message: data.error_message || "" });
    }

    const result = data.result || {};
    const payload = {
      rating: result.rating || null,
      total: result.user_ratings_total || 0,
      reviews: (result.reviews || [])
        .filter((r) => r.rating >= 4 && (r.text || "").trim().length > 0)
        .slice(0, 6)
        .map((r) => ({
          author: r.author_name || "Google User",
          rating: r.rating || 5,
          text: (r.text || "").trim(),
          relativeTime: r.relative_time_description || "",
        })),
    };

    cache = { data: payload, fetchedAt: Date.now() };
    return json(200, payload);
  } catch (err) {
    // If Google is unreachable but we have stale cache, serve it
    if (cache.data) return json(200, cache.data, true);
    return json(500, { error: "Failed to fetch reviews", message: err.message });
  }
};

function json(statusCode, body, fromCache = false) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json",
      // Let Netlify's CDN cache successful responses for 6h too
      "Cache-Control": statusCode === 200 ? "public, max-age=21600" : "no-store",
      "X-Cache": fromCache ? "HIT" : "MISS",
    },
    body: JSON.stringify(body),
  };
}
