"""
Shared pipeline state passed between agents in the LangGraph.
"""

from typing import TypedDict, List, Dict, Any


class PipelineState(TypedDict, total=False):
    # Input
    media_type: str      # 'all' | 'movie' | 'tv'
    window: str           # 'day' | 'week'
    limit: int             # how many trending titles to pull

    # Filled in by Scout Agent
    trending: List[Dict[str, Any]]

    # Filled in by Analyst Agent
    analyses: List[Dict[str, Any]]

    # Filled in by Strategist Agent
    report: str
