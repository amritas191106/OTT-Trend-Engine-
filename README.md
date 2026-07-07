
# OTT Streaming Trend Engine

A multi-agent system that identifies currently trending movies/TV shows,
analyzes why they're trending using audience reviews, and produces an
actionable content strategy report, the kind a streaming platform's
content team could actually use.

## Problem Statement

Streaming platforms need to understand not just what is trending, but
why, in order to make content acquisition and promotion decisions and 
viewers want concrete suggestions for what to watch next based on
those trends, not just a list of popular titles. This requires several
genuinely distinct skills: data retrieval, evidence-grounded analysis,
and strategic synthesis - which maps naturally onto three specialized
agents rather than one agent doing everything.

## Architecture: Pipeline Orchestration Pattern

```
┌─────────────┐      ┌───────────────┐      ┌──────────────────┐
│ Scout Agent │ ───▶ │ Analyst Agent │ ───▶ │ Strategist Agent │
└─────────────┘      └───────────────┘      └──────────────────┘
   fetches              explains why          synthesizes into
   trending titles    each is trending          final report
   (TMDB API)         (reviews + LLM)              (LLM)
```

This is a **Pipeline** pattern (as opposed to Supervisor,
Parallel+Aggregator, or Hierarchical): each agent's output is a strict
precondition for the next agent's input, with no branching decisions or
independent parallel work required. A Supervisor pattern would add
unnecessary routing complexity here since there's no dynamic decision
about which agent to call next and the order is always the same.

Implemented in **LangGraph** as a `StateGraph` with three nodes and linear
edges (see `graph.py`). Shared state (`state.py`) is passed between nodes
and accumulated as it flows through the pipeline.

### Agent Responsibilities

| Agent | Responsibility | Tools/Skills Used |
|---|---|---|
| **Scout** | Discover what's currently trending | TMDB Trending API |
| **Analyst** | Explain *why* each title is trending, grounded in real review text; also fetch real similar-title data | TMDB Reviews + Recommendations APIs + LLM reasoning |
| **Strategist** | Synthesize all analyses into a final report with strategic recommendations *and* concrete "what to watch next" suggestions | LLM reasoning over aggregated state |

Each agent has a distinct input/output contract and a distinct skill —
this isn't the same prompt run three times with different personas.

## Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get API keys:**
   - TMDB (free): https://www.themoviedb.org/settings/api
   - Google Gemini (free): https://aistudio.google.com/apikey

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # then edit .env and paste in your keys
   ```

4. **Run:**
   ```bash
   python main.py
   ```

The final report is printed to console and saved to `output/trend_report_<timestamp>.md`.

## Configuration

Edit the `initial_state` dict in `main.py` to change:
- `media_type`: `"all"`, `"movie"`, or `"tv"`
- `window`: `"day"` or `"week"`
- `limit`: number of trending titles to analyze (keep low to control API/LLM cost)

## Project Structure

```
ott-trend-engine/
├── agents/
│   ├── scout.py         # Scout agent
│   ├── analyst.py       # Analyst agent
│   └── strategist.py    # Strategist agent
├── tools/
│   └── tmdb.py          # TMDB API wrapper
├── state.py             # Shared pipeline state schema
├── llm.py               # Centralized LLM client
├── graph.py             # LangGraph pipeline definition
├── main.py              # Entry point
├── requirements.txt
└── .env.example
```

## Design Decisions & Limitations

- **No vector DB/RAG pipeline**: review text is short enough to pass
  directly as LLM context rather than requiring retrieval infrastructure.
  This keeps the system simpler without sacrificing the "grounded in real
  evidence" requirement.
- **Analyst step runs in parallel**: the Analyst agent analyzes all
  trending titles concurrently (`ThreadPoolExecutor`) rather than one at a
  time, then aggregates results back into original trending order. This is
  a **Parallel + Aggregator** sub-pattern nested inside the outer Pipeline —
  the overall Scout → Analyst → Strategist flow is still sequential, but
  work within the Analyst step fans out and back in.
- **Sentiment as structured signal**: the Analyst agent now extracts an
  explicit sentiment label (positive/mixed/negative/unknown) alongside its
  prose analysis, which the Strategist agent factors into its
  recommendations. e.g. flagging titles trending on controversy rather
  than genuine praise.
- **Future extensions**: a Benchmark agent comparing trends week-over-week,
  or wrapping the TMDB tool as an MCP server for reuse across projects.

## Example Output

See `output/` after running for a generated sample report.

# OTT-Trend-Engine-
Multi-agent OTT streaming trend analysis engine -  Agentic AI capstone
a5e93c8250f03409dbfb134f7ab49378a73452bb
