"""
Strategist Agent
Responsibility: synthesize Scout + Analyst outputs into a final,
decision usable report , both a content strategy view (for a platform)
and a "what to watch next" recommendation view (for a viewer), grounded
in TMDB's real similar title data rather than the LLM inventing titles.
This is the only agent whose output the end user actually reads.
"""

from state import PipelineState
from llm import llm

STRATEGIST_PROMPT = """You are a content strategy consultant for a streaming platform. \
Below is a set of currently trending titles, analysis of why each is trending, and \
real similar-title data pulled from TMDB for each one.

{analyses_block}

Write a report with these sections:

## Trend Summary
A short overview of the overall trend landscape right now (2-3 sentences).

## Title-by-Title Breakdown
For each title, a brief bullet with the key driver of its popularity and its sentiment.

## What to Watch Next
For each trending title, recommend 2-3 titles from its "similar titles" list that \
best match why people are enjoying it (e.g. if a title is trending for its twisty plot, \
prioritize similar titles rather than just listing all of them). If a title has no \
similar-title data, say so briefly and skip it.

## Strategic Recommendations
3-4 concrete, actionable recommendations for a streaming platform based on these \
trends (e.g. genres to invest in, content to promote, risks to watch for like \
hype driven by controversy rather than quality).

Keep the tone professional and concise but complete — do not cut sections short. \
This report will be read by a content team and by curious viewers."""


def strategist_agent(state: PipelineState) -> PipelineState:
    print("[Strategist Agent] Synthesizing final report...")

    analyses = state.get("analyses", [])

    analyses_block = "\n\n".join(
        f"### {a['title']} (avg rating: {a['vote_average']}/10, "
        f"sentiment: {a['sentiment']}, {a['review_count_used']} reviews analyzed)\n"
        f"Why trending: {a['analysis']}\n"
        f"Similar titles (from TMDB): "
        f"{', '.join(a['recommended_similar']) if a['recommended_similar'] else '(none found)'}"
        for a in analyses
    )

    prompt = STRATEGIST_PROMPT.format(analyses_block=analyses_block)
    response = llm.invoke(prompt)
    report = response.content

    print("[Strategist Agent] Report complete.")

    return {"report": report}
