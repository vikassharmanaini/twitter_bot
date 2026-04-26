"""
report_generator.py

Static HTML report from knowledge_store.
Key dependencies: knowledge_store, datetime
"""

from __future__ import annotations

import html
from pathlib import Path

from src.knowledge_store import KnowledgeStore


def write_report(store: KnowledgeStore, out_path: str | Path = "report.html") -> Path:
    p = Path(out_path)
    data = store.export_weekly_summary_json()
    items = data.get("items") or []
    rows = []
    for it in items[:100]:
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(str(it.get("tweet_id", ""))),
                html.escape(str(it.get("account", ""))),
                html.escape(str(it.get("reply_text", ""))[:200]),
            )
        )
    body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Bot report</title></head>
<body>
<h1>Weekly replies</h1>
<p>Count: {data.get("count", 0)}</p>
<table border="1"><thead><tr><th>Tweet</th><th>Account</th><th>Reply</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
</body></html>"""
    p.write_text(body, encoding="utf-8")
    return p
