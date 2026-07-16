"""Human review UI — prefers curated queue, writes human_feedback.jsonl."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from lebanese_franco_factory.core.paths import output_dir, repo_root

app = FastAPI(title="Lebanese Franco Human Review")


def feedback_path() -> Path:
    path = repo_root() / "feedback"
    path.mkdir(exist_ok=True)
    return path / "human_feedback.jsonl"


def reviewed_ids(*, require_human: bool = False) -> set[str]:
    """IDs already reviewed. If require_human, ignore ai_first_pass-only rows."""
    path = feedback_path()
    if not path.exists():
        return set()
    latest: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rid = row.get("id", "")
        if rid:
            latest[rid] = row
    if not require_human:
        return set(latest)
    human = {"native", "human", "juliano", "anonymous"}
    return {
        rid
        for rid, row in latest.items()
        if row.get("reviewer") in human or row.get("batch", "").endswith("_native")
    }


def load_queue(limit: int = 50) -> list[dict]:
    """Prefer curated review queue, then fall back to generated conversion rows."""
    done_any = reviewed_ids()
    done_human = reviewed_ids(require_human=True)
    rows: list[dict] = []

    # Priority: needs_human (native pass) → curated queue → generated output
    for queue_file in (
        repo_root() / "data" / "review" / "needs_human_v0.2.jsonl",
        repo_root() / "data" / "review" / "queue_v0.2.jsonl",
    ):
        if not queue_file.exists():
            continue
        # needs_human must get a native pass even if AI already reviewed
        skip_ids = done_human if "needs_human" in queue_file.name else done_any
        for line in queue_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("id") in skip_ids:
                continue
            if row.get("family") == "conversion" or "source" in row:
                rows.append(row)
            elif row.get("family") == "chat_sft":
                msgs = row.get("messages") or []
                if len(msgs) >= 2:
                    rows.append(
                        {
                            "id": row["id"],
                            "family": "chat_sft",
                            "source": msgs[0].get("content", ""),
                            "target": msgs[1].get("content", ""),
                        }
                    )
            if len(rows) >= limit:
                return rows
        if rows:
            return rows

    for clean in sorted(output_dir().rglob("clean.jsonl")):
        for line in clean.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("id") in done:
                continue
            if row.get("family") == "conversion":
                rows.append(row)
            if len(rows) >= limit:
                return rows
    return rows


@app.get("/", response_class=HTMLResponse)
@app.get("/review", response_class=HTMLResponse)
def review_home() -> str:
    queue = load_queue()
    remaining = len(queue)
    if not queue:
        return (
            "<html><body><h1>Review queue empty</h1>"
            "<p>All curated items reviewed, or generate more data.</p>"
            "<p><a href='/'>Refresh</a></p></body></html>"
        )
    item = queue[0]
    src = html.escape(str(item.get("source", "")))
    tgt = html.escape(str(item.get("target", "")))
    iid = html.escape(str(item.get("id", "")))
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Review</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem}}
.box{{border:1px solid #ccc;padding:1rem;margin:1rem 0;border-radius:8px}}
button{{margin-right:.5rem;padding:.5rem .9rem;cursor:pointer}}
.meta{{color:#666;font-size:.9rem}}
</style></head><body>
<h1>Human Review</h1>
<p class='meta'>Remaining in queue: {remaining} · id: {iid}</p>
<div class='box'><b>Original</b><div>{src}</div></div>
<div class='box'><b>Generated</b><div>{tgt}</div></div>
<form method='post' action='/review/submit'>
<input type='hidden' name='id' value='{iid}'>
<input type='hidden' name='original' value='{src}'>
<input type='hidden' name='generated' value='{tgt}'>
<label>Edit <input name='corrected' value='{tgt}' style='width:100%'></label>
<p>
<button name='decision' value='correct'>Correct</button>
<button name='decision' value='edit'>Edit</button>
<button name='decision' value='reject'>Reject</button>
</p>
</form>
</body></html>"""


@app.post("/review/submit")
def submit(
    id: str = Form(...),
    original: str = Form(...),
    generated: str = Form(...),
    corrected: str = Form(""),
    decision: str = Form(...),
):
    record = {
        "id": id,
        "decision": decision,
        "original": original,
        "generated": generated,
        "corrected": corrected if decision == "edit" else generated,
        "reviewer": "anonymous",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_version": "v0.2",
    }
    with feedback_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return RedirectResponse(url="/review", status_code=303)
