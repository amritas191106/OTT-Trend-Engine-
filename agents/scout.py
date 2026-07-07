"""
Scout Agent
Responsibility: discover what's currently trending. Pure data-fetching,
no LLM reasoning needed here , this agent's "skill" is tool use (API access).
"""

from state import PipelineState
from tools.tmdb import get_trending


def scout_agent(state: PipelineState) -> PipelineState:
    print("[Scout Agent] Fetching trending titles...")

    media_type = state.get("media_type", "all")
    window = state.get("window", "week")
    limit = state.get("limit", 6)

    trending = get_trending(media_type=media_type, window=window, limit=limit)

    print(f"[Scout Agent] Found {len(trending)} trending titles: "
          f"{[t['title'] for t in trending]}")

    return {"trending": trending}
