"""
OTT Streaming Trend Engine
Entry point: runs the Scout -> Analyst -> Strategist pipeline and
saves the final report to disk.
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from graph import build_graph  # noqa: E402  (import after load_dotenv)


def main():
    app = build_graph()

    initial_state = {
        "media_type": "all",   # 'all' | 'movie' | 'tv'
        "window": "week",       # 'day' | 'week'
        "limit": 6,              # number of trending titles to analyze
    }

    print("=" * 60)
    print("OTT STREAMING TREND ENGINE")
    print("=" * 60)

    final_state = app.invoke(initial_state)

    report = final_state.get("report", "(No report generated)")

    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"output/trend_report_{timestamp}.md"

    with open(out_path, "w") as f:
        f.write(report)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
