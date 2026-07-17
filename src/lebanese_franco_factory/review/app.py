"""Human review UI — Correct / Edit / Reject → feedback/human_feedback.jsonl.

``fastapi`` is an optional ``[dashboard]`` extra and is imported lazily inside
:func:`create_app`, so importing this module (e.g. for API-doc generation)
never requires it. Only actually starting the server does.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lebanese_franco_factory.core.paths import output_dir, repo_root


def feedback_path() -> Path:
    path = repo_root() / "feedback"
    path.mkdir(exist_ok=True)
    return path / "human_feedback.jsonl"


def load_queue(limit: int = 50) -> list[dict]:
    rows: list[dict] = []
    for clean in sorted(output_dir().rglob("clean.jsonl")):
        for line in clean.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("family") == "conversion":
                rows.append(row)
            if len(rows) >= limit:
                return rows
    return rows


def _review_home_html() -> str:
    queue = load_queue()
    if not queue:
        return "<html><body><h1>No conversion samples yet. Generate data first.</h1></body></html>"
    item = queue[0]
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Review</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem}}
.box{{border:1px solid #ccc;padding:1rem;margin:1rem 0;border-radius:8px}}
button{{margin-right:.5rem;padding:.5rem .9rem}}
</style></head><body>
<h1>Human Review</h1>
<div class='box'><b>Original</b><div>{item.get('source','')}</div></div>
<div class='box'><b>Generated</b><div>{item.get('target','')}</div></div>
<form method='post' action='/review/submit'>
<input type='hidden' name='id' value='{item.get('id','')}'>
<input type='hidden' name='original' value='{item.get('source','')}'>
<input type='hidden' name='generated' value='{item.get('target','')}'>
<label>Edit <input name='corrected' value='{item.get('target','')}' style='width:100%'></label>
<p>
<button name='decision' value='correct'>Correct</button>
<button name='decision' value='edit'>Edit</button>
<button name='decision' value='reject'>Reject</button>
</p>
</form>
<p><a href='/'>Dashboard</a></p>
</body></html>"""


def record_feedback(
    *, id: str, original: str, generated: str, corrected: str, decision: str
) -> dict:
    """Append one review decision to ``feedback/human_feedback.jsonl``."""
    record = {
        "id": id,
        "decision": decision,
        "original": original,
        "generated": generated,
        "corrected": corrected if decision == "edit" else generated,
        "reviewer": "anonymous",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_version": "v0.1",
    }
    with feedback_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def create_app():
    """Build the FastAPI human-review app (imports fastapi lazily)."""
    from fastapi import FastAPI, Form
    from fastapi.responses import HTMLResponse, RedirectResponse

    app = FastAPI(title="Lebanese Franco Human Review")

    @app.get("/", response_class=HTMLResponse)
    @app.get("/review", response_class=HTMLResponse)
    def review_home() -> str:
        return _review_home_html()

    @app.post("/review/submit")
    def submit(
        id: str = Form(...),
        original: str = Form(...),
        generated: str = Form(...),
        corrected: str = Form(""),
        decision: str = Form(...),
    ):
        record_feedback(
            id=id,
            original=original,
            generated=generated,
            corrected=corrected,
            decision=decision,
        )
        return RedirectResponse(url="/review", status_code=303)

    return app


def main() -> None:
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8081)


if __name__ == "__main__":
    main()
