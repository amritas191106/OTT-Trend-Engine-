"""
TMDB API wrapper.
Docs: https://developer.themoviedb.org/reference/intro/getting-started

Get a free API key (v3 auth) at: https://www.themoviedb.org/settings/api
"""

import os
import time
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2  # doubles each retry: 2s, 4s, 8s


def _get(endpoint: str, params: dict | None = None) -> dict:
    """
    Internal helper to call the TMDB API with retries.
    Retries on connection errors/timeouts, which are common on flaky
    networks — each retry waits longer than the last.
    """
    if not TMDB_API_KEY:
        raise RuntimeError(
            "TMDB_API_KEY is not set. Add it to your .env file. "
            "Get a free key at https://www.themoviedb.org/settings/api"
        )
    params = params or {}
    params["api_key"] = TMDB_API_KEY

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                print(f"[TMDB] Connection issue on {endpoint} (attempt {attempt}/{MAX_RETRIES}), "
                      f"retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"[TMDB] Giving up on {endpoint} after {MAX_RETRIES} attempts.")

    raise last_error


def get_trending(media_type: str = "all", window: str = "week", limit: int = 6) -> list[dict]:
    """
    Fetch trending movies/TV shows.
    media_type: 'all' | 'movie' | 'tv'
    window: 'day' | 'week'
    Returns a simplified list of dicts: id, title, media_type, overview, popularity, vote_average
    """
    data = _get(f"/trending/{media_type}/{window}")
    results = data.get("results", [])[:limit]

    simplified = []
    for r in results:
        simplified.append({
            "id": r.get("id"),
            "title": r.get("title") or r.get("name"),
            "media_type": r.get("media_type"),
            "overview": r.get("overview", ""),
            "popularity": r.get("popularity"),
            "vote_average": r.get("vote_average"),
            "vote_count": r.get("vote_count"),
        })
    return simplified


def get_reviews(media_id: int, media_type: str, limit: int = 5) -> list[str]:
    """
    Fetch review text for a given title.
    media_type must be 'movie' or 'tv' (not 'all').
    Returns a list of review content strings. Returns an empty list on any
    failure (missing reviews, network issue after retries, etc.) rather
    than raising — a single title's review fetch failing shouldn't take
    down the whole pipeline; the Analyst agent just falls back to
    overview-only analysis for that title.
    """
    if media_type not in ("movie", "tv"):
        return []
    try:
        data = _get(f"/{media_type}/{media_id}/reviews")
    except (requests.exceptions.RequestException, RuntimeError) as e:
        print(f"[TMDB] Could not fetch reviews for {media_type}/{media_id}: {e}")
        return []
    results = data.get("results", [])[:limit]
    return [r.get("content", "").strip() for r in results if r.get("content")]


def get_recommendations(media_id: int, media_type: str, limit: int = 4) -> list[str]:
    """
    Fetch titles TMDB recommends based on a given title (real data, not
    LLM-guessed). Used so the final report can suggest "watch this next"
    titles grounded in actual similarity data rather than hallucination.
    media_type must be 'movie' or 'tv'.
    Returns a list of title name strings.
    """
    if media_type not in ("movie", "tv"):
        return []
    try:
        data = _get(f"/{media_type}/{media_id}/recommendations")
    except (requests.exceptions.RequestException, RuntimeError) as e:
        print(f"[TMDB] Could not fetch recommendations for {media_type}/{media_id}: {e}")
        return []
    results = data.get("results", [])[:limit]
    names = [r.get("title") or r.get("name") for r in results]
    return [n for n in names if n]
