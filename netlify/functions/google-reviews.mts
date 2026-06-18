import type { Context } from "@netlify/functions";

const PLACE_ID = "ChIJ6U8r1jjFwogRAcC8b_IhfUc";
const CACHE_TTL_MS = 60 * 60 * 1000;

let cachedData: { reviews: Review[]; rating: number; totalReviews: number; fetchedAt: number } | null = null;

interface Review {
  author: string;
  rating: number;
  text: string;
  relativeTime: string;
}

const JSON_HEADERS = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
};

async function fetchReviewsNew(apiKey: string, placeId: string) {
  const url = `https://places.googleapis.com/v1/places/${placeId}`;
  const res = await fetch(url, {
    headers: {
      "X-Goog-Api-Key": apiKey,
      "X-Goog-FieldMask": "reviews,rating,userRatingCount",
    },
  });

  const data = await res.json();

  if (data.error) {
    throw new Error(`Places API (New): ${data.error.message || data.error.status || JSON.stringify(data.error)}`);
  }

  if (!data.reviews || data.reviews.length === 0) {
    throw new Error("Places API (New): No reviews returned");
  }

  const reviews: Review[] = data.reviews.map((r: any) => ({
    author: r.authorAttribution?.displayName || "Anonymous",
    rating: r.rating || 5,
    text: r.text?.text || r.originalText?.text || "",
    relativeTime: r.relativePublishTimeDescription || "",
  }));

  return {
    reviews,
    rating: data.rating || 0,
    totalReviews: data.userRatingCount || 0,
  };
}

async function fetchReviewsLegacy(apiKey: string, placeId: string) {
  const url = new URL("https://maps.googleapis.com/maps/api/place/details/json");
  url.searchParams.set("place_id", placeId);
  url.searchParams.set("fields", "reviews,rating,user_ratings_total");
  url.searchParams.set("key", apiKey);

  const res = await fetch(url.toString());
  const data = await res.json();

  if (data.status && data.status !== "OK") {
    throw new Error(`Places API (Legacy): ${data.status} - ${data.error_message || "Unknown error"}`);
  }

  if (!data.result || !data.result.reviews || data.result.reviews.length === 0) {
    throw new Error("Places API (Legacy): No reviews returned");
  }

  const reviews: Review[] = data.result.reviews.map((r: any) => ({
    author: r.author_name,
    rating: r.rating,
    text: r.text,
    relativeTime: r.relative_time_description,
  }));

  return {
    reviews,
    rating: data.result.rating || 0,
    totalReviews: data.result.user_ratings_total || 0,
  };
}

export default async function handler(req: Request, _context: Context) {
  const apiKey = Netlify.env.get("GOOGLE_PLACES_API_KEY");
  if (!apiKey) {
    return new Response(
      JSON.stringify({ error: "GOOGLE_PLACES_API_KEY environment variable is not set" }),
      { status: 503, headers: JSON_HEADERS },
    );
  }

  if (cachedData && Date.now() - cachedData.fetchedAt < CACHE_TTL_MS) {
    return new Response(JSON.stringify(cachedData), { headers: JSON_HEADERS });
  }

  const errors: string[] = [];

  try {
    const result = await fetchReviewsNew(apiKey, PLACE_ID);
    cachedData = { ...result, fetchedAt: Date.now() };
    return new Response(JSON.stringify(result), { headers: JSON_HEADERS });
  } catch (err: any) {
    errors.push(err.message);
  }

  try {
    const result = await fetchReviewsLegacy(apiKey, PLACE_ID);
    cachedData = { ...result, fetchedAt: Date.now() };
    return new Response(JSON.stringify(result), { headers: JSON_HEADERS });
  } catch (err: any) {
    errors.push(err.message);
  }

  return new Response(
    JSON.stringify({ error: "Both Google Places APIs failed", details: errors }),
    { status: 502, headers: JSON_HEADERS },
  );
}

export const config = {
  path: "/api/google-reviews",
};
