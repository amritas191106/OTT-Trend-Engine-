"""
Orchestration: Pipeline pattern.

Scout -> Analyst -> Strategist, strictly sequential. Each agent reads
what the previous one wrote to shared state and adds its own piece.
This is the correct pattern here because each step depends entirely
on the previous step's output, with no branching or parallel work needed.
"""

from langgraph.graph import StateGraph, END

from state import PipelineState
from agents.scout import scout_agent
from agents.analyst import analyst_agent
from agents.strategist import strategist_agent


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("scout", scout_agent)
    graph.add_node("analyst", analyst_agent)
    graph.add_node("strategist", strategist_agent)

    graph.set_entry_point("scout")
    graph.add_edge("scout", "analyst")
    graph.add_edge("analyst", "strategist")
    graph.add_edge("strategist", END)

    return graph.compile()
