"""Human review UI — prefers curated queue, writes human_feedback.jsonl.

``fastapi`` is an optional ``[dashboard]`` extra and is imported lazily inside
:func:`create_app`, so importing this module (e.g. for API-doc generation)
never requires it. Only actually starting the server does.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from lebanese_franco_factory.core.paths import output_dir, repo_root


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


def _latest_decisions() -> dict[str, dict]:
    """Most recent feedback row per id (last write wins)."""
    path = feedback_path()
    if not path.exists():
        return {}
    latest: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = row.get("id")
        if rid:
            latest[rid] = row
    return latest


def reviewed_counts() -> dict[str, int]:
    """How many items reviewed, broken down by final decision."""
    counts = {"total": 0, "correct": 0, "edit": 0, "reject": 0}
    for row in _latest_decisions().values():
        counts["total"] += 1
        d = row.get("decision", "")
        if d in counts:
            counts[d] += 1
    return counts


def recent_decisions(n: int = 10) -> list[dict]:
    """Last ``n`` feedback rows, newest first (for the activity list)."""
    path = feedback_path()
    if not path.exists():
        return []
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows: list[dict] = []
    for line in lines[-n:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.reverse()
    return rows


def queue_progress() -> dict[str, int]:
    """Total / reviewed / remaining across the curated review queue files."""
    done = reviewed_ids()
    ids: set[str] = set()
    for queue_file in (
        repo_root() / "data" / "review" / "needs_human_v0.2.jsonl",
        repo_root() / "data" / "review" / "queue_v0.2.jsonl",
    ):
        if not queue_file.exists():
            continue
        for line in queue_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rid = json.loads(line).get("id")
            except json.JSONDecodeError:
                continue
            if rid:
                ids.add(rid)
    reviewed_in_queue = len(ids & done)
    return {
        "total": len(ids),
        "reviewed": reviewed_in_queue,
        "remaining": len(ids) - reviewed_in_queue,
    }


def dataset_total() -> int:
    """Total clean examples generated across all runs (from output manifests)."""
    total = 0
    out = output_dir()
    if out.exists():
        for manifest in out.rglob("manifest.json"):
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            total += int(data.get("size_clean", data.get("size", 0)) or 0)
    return total


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
            if row.get("id") in done_any:
                continue
            if row.get("family") == "conversion":
                rows.append(row)
            if len(rows) >= limit:
                return rows
    return rows


_STYLE = """
body{font-family:system-ui,sans-serif;max-width:760px;margin:1.5rem auto;padding:0 1rem;color:#1c1c1c}
h1{margin:.2rem 0}
.stats{display:flex;flex-wrap:wrap;gap:.6rem;margin:1rem 0}
.stat{flex:1;min-width:120px;background:#f7f3ea;border:1px solid #e2dccb;border-radius:8px;padding:.6rem .8rem}
.stat .n{font-size:1.5rem;font-weight:700;line-height:1.1}
.stat .l{color:#666;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em}
.bar{height:8px;background:#e6e1d5;border-radius:5px;overflow:hidden;margin:.4rem 0 1rem}
.bar>span{display:block;height:100%;background:#0b3d2e}
.banner{padding:.6rem .9rem;border-radius:8px;margin:1rem 0;font-weight:600}
.banner.ok{background:#e6f4ea;border:1px solid #b7e0c4;color:#0b6b2e}
.box{border:1px solid #ccc;padding:1rem;margin:.8rem 0;border-radius:8px}
.box b{color:#666;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em}
.box .v{font-size:1.15rem;margin-top:.3rem;direction:auto}
button{margin-right:.4rem;padding:.5rem 1rem;cursor:pointer;border:0;border-radius:6px;color:#fff;font-weight:600}
.b-correct{background:#0b6b2e}.b-edit{background:#0b4f8a}.b-reject{background:#8a1c1c}
input[name=corrected]{width:100%;padding:.5rem;font-size:1.05rem;margin-top:.3rem;box-sizing:border-box}
table{width:100%;border-collapse:collapse;margin-top:.5rem;font-size:.85rem}
td,th{padding:.3rem .5rem;border-bottom:1px solid #eee;text-align:left}
.pill{padding:.05rem .5rem;border-radius:10px;font-size:.75rem;font-weight:600}
.p-correct{background:#e6f4ea;color:#0b6b2e}.p-edit{background:#e4eefb;color:#0b4f8a}.p-reject{background:#fbe4e4;color:#8a1c1c}
.muted{color:#888;font-size:.85rem}
"""


def _stats_bar_html() -> str:
    c = reviewed_counts()
    q = queue_progress()
    total_ds = dataset_total()
    pct = int(100 * q["reviewed"] / q["total"]) if q["total"] else 0
    return f"""
<div class='stats'>
  <div class='stat'><div class='n'>{c['total']}</div><div class='l'>Reviewed</div></div>
  <div class='stat'><div class='n'>{q['remaining']}</div><div class='l'>Curated left</div></div>
  <div class='stat'><div class='n'>{q['total']}</div><div class='l'>Curated total</div></div>
  <div class='stat'><div class='n'>{total_ds:,}</div><div class='l'>Dataset examples</div></div>
</div>
<div class='bar'><span style='width:{pct}%'></span></div>
<p class='muted'>Queue {q['reviewed']}/{q['total']} done ({pct}%) ·
 <span class='pill p-correct'>correct {c['correct']}</span>
 <span class='pill p-edit'>edited {c['edit']}</span>
 <span class='pill p-reject'>rejected {c['reject']}</span></p>
"""


def _recent_list_html() -> str:
    rows = recent_decisions(10)
    if not rows:
        return "<p class='muted'>No decisions yet.</p>"
    trs = []
    for r in rows:
        d = html.escape(str(r.get("decision", "")))
        rid = html.escape(str(r.get("id", "")))
        corrected = html.escape(str(r.get("corrected", ""))[:60])
        ts = html.escape(str(r.get("timestamp", ""))[11:19])
        trs.append(
            f"<tr><td>{ts}</td><td><span class='pill p-{d}'>{d}</span></td>"
            f"<td class='muted'>{rid}</td><td>{corrected}</td></tr>"
        )
    return (
        "<table><tr><th>time</th><th>decision</th><th>id</th><th>result</th></tr>"
        + "".join(trs)
        + "</table>"
    )


def _review_home_html(msg: str = "") -> str:
    banner = f"<div class='banner ok'>✓ {html.escape(msg)}</div>" if msg else ""
    stats = _stats_bar_html()
    recent = _recent_list_html()
    queue = load_queue()
    if not queue:
        return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Review</title><style>{_STYLE}</style></head><body>
<h1>Human Review</h1>{banner}{stats}
<div class='box'><b>Queue empty</b><div class='v'>All curated items reviewed 🎉 — or generate more data.</div></div>
<h3>Recent decisions</h3>{recent}
<p><a href='/review'>Refresh</a></p>
</body></html>"""
    item = queue[0]
    src = html.escape(str(item.get("source", "")))
    tgt = html.escape(str(item.get("target", "")))
    iid = html.escape(str(item.get("id", "")))
    fam = html.escape(str(item.get("family", "")))
    extra = (
        " · <b>bonus generated sample</b> (curated queue cleared)"
        if queue_progress()["remaining"] == 0
        else ""
    )
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Review</title><style>{_STYLE}</style></head><body>
<h1>Human Review</h1>{banner}{stats}
<p class='muted'>Now reviewing · id <b>{iid}</b>{f' · {fam}' if fam else ''}{extra}</p>
<div class='box'><b>Original</b><div class='v'>{src}</div></div>
<div class='box'><b>Generated</b><div class='v'>{tgt}</div></div>
<form method='post' action='/review/submit'>
<input type='hidden' name='id' value='{iid}'>
<input type='hidden' name='original' value='{src}'>
<input type='hidden' name='generated' value='{tgt}'>
<label class='muted'>Correction (used only if you click Edit)
<input name='corrected' value='{tgt}'></label>
<p>
<button class='b-correct' name='decision' value='correct'>✓ Correct</button>
<button class='b-edit' name='decision' value='edit'>✎ Save edit</button>
<button class='b-reject' name='decision' value='reject'>✕ Reject</button>
</p>
</form>
<h3>Recent decisions</h3>{recent}
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
        "dataset_version": "v0.2",
    }
    with feedback_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def create_app():
    """Build the FastAPI human-review app (imports fastapi lazily)."""
    from urllib.parse import quote

    from fastapi import FastAPI, Form
    from fastapi.responses import HTMLResponse, RedirectResponse

    app = FastAPI(title="Lebanese Franco Human Review")

    @app.get("/", response_class=HTMLResponse)
    @app.get("/review", response_class=HTMLResponse)
    def review_home(msg: str = "") -> str:
        return _review_home_html(msg)

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
        verb = {"correct": "Marked correct", "edit": "Saved edit", "reject": "Rejected"}.get(
            decision, "Saved"
        )
        msg = f"{verb} · {id}"
        return RedirectResponse(url=f"/review?msg={quote(msg)}", status_code=303)

    return app


def main() -> None:
    import os

    import uvicorn

    # Override with LFF_REVIEW_PORT / LFF_HOST if the default is taken.
    port = int(os.environ.get("LFF_REVIEW_PORT", "8081"))
    host = os.environ.get("LFF_HOST", "127.0.0.1")
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
