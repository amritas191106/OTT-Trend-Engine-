"""
Analyst Agent
Responsibility: for each trending title, gather review text (RAG-lite —
retrieval of grounding context) and use the LLM to explain why it's
trending: genre appeal, standout elements, sentiment, recurring themes.
Also pulls TMDB's real "similar title" recommendations so the final
report can suggest concrete titles to watch next, grounded in actual
similarity data rather than the LLM guessing.

Runs concurrently across titles (Parallel + Aggregator sub-pattern nested
inside the outer Pipeline) since each title's analysis is independent of
the others — no need to wait for title 1 before starting title 2.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from state import PipelineState
from tools.tmdb import get_reviews, get_recommendations
from llm import llm

ANALYST_PROMPT = """You are a media trend analyst. Based on the title info and \
audience reviews below, explain concisely why this title is trending right now.

Title: {title}
Overview: {overview}
Average rating: {vote_average}/10 ({vote_count} votes)

Audience reviews:
{reviews}

Respond in exactly this format (Analysis can span multiple sentences/lines):

Sentiment: <one word — positive, mixed, or negative>
Analysis: <3-4 sentences covering (1) what seems to be driving its popularity —
genre, cast, story hook, controversy, etc. (2) why audience sentiment leans the
way it does (3) one notable recurring theme across reviews, if reviews are
available>

If no reviews are available, base your answer on the overview and rating alone,
set Sentiment to "unknown", and say so explicitly in the analysis."""


def _parse_response(raw_text: str) -> tuple[str, str]:
    """
    Split the model's response into (sentiment, analysis).
    Handles multi-line analysis text correctly — everything after the
    'Analysis:' marker is captured, not just the first line.
    """
    sentiment = "unknown"
    analysis_lines = []
    in_analysis = False

    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("sentiment:"):
            sentiment = stripped.split(":", 1)[1].strip().lower()
            in_analysis = False
            continue
        if stripped.lower().startswith("analysis:"):
            analysis_lines.append(stripped.split(":", 1)[1].strip())
            in_analysis = True
            continue
        if in_analysis and stripped:
            analysis_lines.append(stripped)

    analysis_text = " ".join(analysis_lines).strip() or raw_text.strip()
    return sentiment, analysis_text


def _analyze_one(item: dict) -> dict:
    """Analyze a single trending title. Runs in its own thread."""
    media_type = item.get("media_type")
    reviews = get_reviews(item["id"], media_type) if media_type in ("movie", "tv") else []
    reviews_text = "\n---\n".join(reviews) if reviews else "(No reviews available)"

    prompt = ANALYST_PROMPT.format(
        title=item["title"],
        overview=item.get("overview") or "(No overview available)",
        vote_average=item.get("vote_average"),
        vote_count=item.get("vote_count"),
        reviews=reviews_text[:4000],  # keep prompt size sane
    )

    response = llm.invoke(prompt)
    sentiment, analysis_text = _parse_response(response.content)

    recommended = get_recommendations(item["id"], media_type) if media_type in ("movie", "tv") else []

    print(f"[Analyst Agent] Done: {item['title']} (sentiment: {sentiment}, "
          f"{len(recommended)} similar titles found)")

    return {
        "title": item["title"],
        "media_type": media_type,
        "vote_average": item.get("vote_average"),
        "review_count_used": len(reviews),
        "sentiment": sentiment,
        "analysis": analysis_text,
        "recommended_similar": recommended,
    }


def analyst_agent(state: PipelineState) -> PipelineState:
    print("[Analyst Agent] Analyzing why each title is trending (in parallel)...")

    trending = state.get("trending", [])
    analyses = []

    # Parallel + Aggregator: fan out one worker per title, then gather
    # results back into a single list before handing off to Strategist.
    with ThreadPoolExecutor(max_workers=min(3, max(1, len(trending)))) as executor:
        future_to_item = {executor.submit(_analyze_one, item): item for item in trending}
        for future in as_completed(future_to_item):
            analyses.append(future.result())

    # as_completed() returns results out of order — restore original
    # trending order so the report reads sensibly.
    title_order = [item["title"] for item in trending]
    analyses.sort(key=lambda a: title_order.index(a["title"]))

    return {"analyses": analyses}
