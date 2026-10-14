"""Human review UI — full-list proofing, writes human_feedback.jsonl.

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
from lebanese_franco_factory.webui import data as wdata
from lebanese_franco_factory.webui import excel as wexcel
from lebanese_franco_factory.webui.theme import page


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
    """Total distinct dataset examples (canonical size per dataset)."""
    return wdata.totals()["examples"]


def load_queue(limit: int = 500, *, include_done: bool = False) -> list[dict]:
    """Prefer curated review queue, then fall back to generated conversion rows.

    With ``include_done`` the already-reviewed rows are kept (and tagged
    ``_done``/``_decision``) so the list view can show full history.
    """
    latest = _latest_decisions()
    done_any = set(latest)
    done_human = reviewed_ids(require_human=True)
    rows: list[dict] = []

    def _decorate(row: dict) -> dict:
        rid = row.get("id")
        dec = latest.get(rid, {})
        row["_done"] = rid in done_any
        row["_decision"] = dec.get("decision", "")
        return row

    # Priority: needs_human (native pass) → curated queue → generated output
    for queue_file in (
        repo_root() / "data" / "review" / "needs_human_v0.2.jsonl",
        repo_root() / "data" / "review" / "queue_v0.2.jsonl",
    ):
        if not queue_file.exists():
            continue
        skip_ids = done_human if "needs_human" in queue_file.name else done_any
        for line in queue_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            done = row.get("id") in skip_ids
            if done and not include_done:
                continue
            item: dict | None = None
            if row.get("family") == "conversion" or "source" in row:
                item = row
            elif row.get("family") == "chat_sft":
                msgs = row.get("messages") or []
                if len(msgs) >= 2:
                    item = {
                        "id": row["id"],
                        "family": "chat_sft",
                        "source": msgs[0].get("content", ""),
                        "target": msgs[1].get("content", ""),
                        "reason": row.get("reason", ""),
                    }
            if item is not None:
                rows.append(_decorate(item))
            if len(rows) >= limit:
                return rows
        if rows:
            return rows

    for clean in sorted(output_dir().rglob("clean.jsonl")):
        for line in clean.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("id") in done_any and not include_done:
                continue
            if row.get("family") == "conversion":
                rows.append(_decorate(row))
            if len(rows) >= limit:
                return rows
    return rows


# --------------------------------------------------------------------------- UI


def _stats_bar_html() -> str:
    c = reviewed_counts()
    q = queue_progress()
    total_ds = dataset_total()
    pct = int(100 * q["reviewed"] / q["total"]) if q["total"] else 0
    return f"""
<div class='grid kpis' style='margin:1rem 0'>
  <div class='kpi'><div class='n' id='k-reviewed'>{c['total']}</div><div class='l'>Reviewed</div></div>
  <div class='kpi accent'><div class='n' id='k-remaining'>{q['remaining']}</div><div class='l'>Left to proof</div></div>
  <div class='kpi'><div class='n'>{q['total']}</div><div class='l'>Curated queue</div></div>
  <div class='kpi'><div class='n'>{total_ds:,}</div><div class='l'>Dataset examples</div></div>
</div>
<div class='bar'><span id='k-bar' style='width:{pct}%'></span></div>
<p class='muted' style='margin:.2rem 0 0'>Queue <b id='k-frac'>{q['reviewed']}/{q['total']}</b> proofed
 &middot; <span class='pill p-correct'>correct {c['correct']}</span>
 <span class='pill p-edit'>edited {c['edit']}</span>
 <span class='pill p-reject'>rejected {c['reject']}</span></p>
"""


def _recent_list_html() -> str:
    rows = recent_decisions(12)
    if not rows:
        return "<p class='muted'>No decisions yet.</p>"
    trs = []
    for r in rows:
        d = html.escape(str(r.get("decision", "")))
        rid = html.escape(str(r.get("id", "")))
        corrected = html.escape(str(r.get("corrected", ""))[:70])
        ts = html.escape(str(r.get("timestamp", ""))[11:19])
        trs.append(
            f"<tr><td class='mono'>{ts}</td><td><span class='pill p-{d}'>{d}</span></td>"
            f"<td class='mono'>{rid}</td><td class='fr'>{corrected}</td></tr>"
        )
    return (
        "<table class='tbl'><tr><th>time</th><th>decision</th><th>id</th><th>result</th></tr>"
        + "".join(trs)
        + "</table>"
    )


def _row_html(i: int, item: dict) -> str:
    iid = html.escape(str(item.get("id", "")))
    src = html.escape(str(item.get("source", "")))
    tgt = html.escape(str(item.get("target", "")))
    reason = html.escape(str(item.get("reason", "")))
    done = item.get("_done")
    dec = html.escape(str(item.get("_decision", "")))
    cls = " row-done" if done else ""
    status = f"<span class='pill p-{dec}'>{dec}</span>" if done else "<span class='pill p-neutral'>pending</span>"
    reason_html = f"<div class='muted' style='font-size:.75rem'>{reason}</div>" if reason else ""
    return f"""
<tr class='r{cls}' data-id='{iid}' data-search='{src.lower()} {tgt.lower()} {iid.lower()}'
    data-state='{'done' if done else 'pending'}'>
  <td class='num muted'>{i}</td>
  <td><div class='ar'>{src}</div><div class='mono'>{iid}</div>{reason_html}</td>
  <td><input class='field fr' value='{tgt}' data-orig='{tgt}'></td>
  <td class='wrap-actions'>
    <span class='status'>{status}</span>
    <span class='flex' style='margin-top:.35rem'>
      <button class='iconbtn c' title='Correct' data-act='correct'>&#10003;</button>
      <button class='iconbtn e' title='Save edit' data-act='edit'>&#9998;</button>
      <button class='iconbtn r' title='Reject' data-act='reject'>&#10007;</button>
    </span>
  </td>
</tr>"""


_LIST_JS = """
<script>
async function decide(tr, act){
  const id=tr.dataset.id, inp=tr.querySelector('input.field');
  const body=new URLSearchParams({id, original:tr.querySelector('.ar').textContent,
    generated:inp.dataset.orig, corrected:inp.value, decision:act});
  const st=tr.querySelector('.status');
  st.innerHTML="<span class='pill p-neutral'>saving…</span>";
  try{
    const r=await fetch('/review/api/submit',{method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded'},body});
    const j=await r.json();
    st.innerHTML="<span class='pill p-"+j.decision+"'>"+j.decision+"</span>";
    tr.classList.add('row-done'); tr.dataset.state='done';
    if(j.stats) applyStats(j.stats);
  }catch(e){ st.innerHTML="<span class='pill p-reject'>error</span>"; }
}
function applyStats(s){
  const set=(id,v)=>{const el=document.getElementById(id); if(el)el.textContent=v;};
  set('k-reviewed',s.reviewed); set('k-remaining',s.remaining);
  set('k-frac',s.q_reviewed+'/'+s.q_total);
  const bar=document.getElementById('k-bar');
  if(bar)bar.style.width=(s.q_total? Math.round(100*s.q_reviewed/s.q_total):0)+'%';
}
document.addEventListener('click',e=>{
  const b=e.target.closest('button[data-act]'); if(!b)return;
  decide(b.closest('tr'), b.dataset.act);
});
function applyFilter(){
  const q=(document.getElementById('search').value||'').toLowerCase();
  const mode=document.querySelector('.chip.on').dataset.f;
  let shown=0;
  document.querySelectorAll('tr.r').forEach(tr=>{
    const okText=!q||tr.dataset.search.includes(q);
    const okState=mode==='all'||tr.dataset.state===mode;
    const vis=okText&&okState; tr.style.display=vis?'':'none'; if(vis)shown++;
  });
  document.getElementById('shown').textContent=shown;
}
document.getElementById('search').addEventListener('input',applyFilter);
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{
  document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));
  c.classList.add('on'); applyFilter();
}));
applyFilter();
</script>
"""


def _review_body(msg: str = "") -> str:
    banner = f"<div class='banner ok'>&#10003; {html.escape(msg)}</div>" if msg else ""
    stats = _stats_bar_html()
    items = load_queue(limit=1000, include_done=True)
    pending = sum(1 for it in items if not it.get("_done"))
    if not items:
        return f"""{banner}<h1>Human Review</h1>
<p class='sub'>Native-speaker proofing of generated Lebanese-Franco phrases.</p>{stats}
<div class='card'><b>Queue clear</b><div class='fr' style='margin-top:.4rem'>
All curated items proofed &#127881; — generate more data from the Dashboard.</div></div>
<h2>Recent decisions</h2>{_recent_list_html()}"""
    rows = "".join(_row_html(i + 1, it) for i, it in enumerate(items))
    return f"""{banner}
<h1>Human Review <span class='muted' style='font-size:1rem'>&middot; {pending} left to proof</span></h1>
<p class='sub'>Edit the Franco spelling inline, then approve, save your edit, or reject —
each click saves instantly.</p>
{stats}
<div class='card' style='margin-bottom:1rem'>
  <div class='flex' style='flex-wrap:wrap;justify-content:space-between;gap:.8rem'>
    <div>
      <b>Offline editing</b>
      <div class='muted' style='font-size:.85rem'>Export to Excel, fix spelling in the
        Franco column, then upload the file to record every decision at once.</div>
    </div>
    <div class='flex' style='flex-wrap:wrap'>
      <a class='btn ghost' href='/review/export.xlsx'>&#8681; Export to Excel</a>
      <form method='post' action='/review/import' enctype='multipart/form-data' class='flex'>
        <input type='file' name='file' accept='.xlsx' required>
        <button class='btn' type='submit'>&#8679; Import</button>
      </form>
    </div>
  </div>
</div>
<div class='card'>
  <div class='toolbar'>
    <input id='search' class='grow' placeholder='Search Arabic, Franco, or id…'>
    <span class='chip on' data-f='pending'>Pending</span>
    <span class='chip' data-f='done'>Done</span>
    <span class='chip' data-f='all'>All</span>
    <span class='muted'>showing <b id='shown'>{pending}</b></span>
  </div>
  <div style='overflow-x:auto'>
  <table class='tbl'>
    <tr><th>#</th><th>Arabic (source)</th><th>Franco (edit if needed)</th><th>Decision</th></tr>
    {rows}
  </table>
  </div>
</div>
<h2>Recent decisions</h2>{_recent_list_html()}
{_LIST_JS}"""


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
        "reviewer": "native",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_version": "v0.2",
    }
    with feedback_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def _queue_lookup() -> dict[str, dict]:
    """Map id -> {source, target} across all queued items (for Excel import)."""
    lookup: dict[str, dict] = {}
    for it in load_queue(limit=10000, include_done=True):
        rid = it.get("id")
        if rid:
            lookup[rid] = {"source": it.get("source", ""), "target": it.get("target", "")}
    return lookup


def apply_imported_rows(parsed: list[dict[str, str]]) -> dict[str, int]:
    """Record feedback for each imported row; return a summary count.

    Decision rules: an explicit ``reject``/``edit`` wins; ``correct`` becomes an
    edit if the Franco text was changed; a blank decision with a changed Franco
    is treated as an edit; otherwise the row is skipped.
    """
    lookup = _queue_lookup()
    summary = {"correct": 0, "edit": 0, "reject": 0, "skipped": 0, "unknown": 0}
    for row in parsed:
        rid = row.get("id", "")
        if not rid:
            summary["unknown"] += 1
            continue
        franco = (row.get("franco") or "").strip()
        decision = (row.get("decision") or "").strip().lower()
        orig = lookup.get(rid, {})
        source = orig.get("source", "")
        original_target = orig.get("target", franco)
        changed = bool(franco) and franco != original_target

        if decision == "reject":
            final, corrected = "reject", franco or original_target
        elif decision == "edit" or (decision in ("", "correct") and changed):
            final, corrected = "edit", franco or original_target
        elif decision == "correct":
            final, corrected = "correct", original_target
        else:
            summary["skipped"] += 1
            continue

        record_feedback(
            id=rid, original=source, generated=original_target,
            corrected=corrected, decision=final,
        )
        summary[final] += 1
    return summary


def _live_stats() -> dict:
    c = reviewed_counts()
    q = queue_progress()
    return {
        "reviewed": c["total"],
        "remaining": q["remaining"],
        "q_reviewed": q["reviewed"],
        "q_total": q["total"],
    }


def register_routes(app, *, mount_root: bool = False) -> None:
    """Attach the human-review routes to a FastAPI ``app``.

    ``mount_root`` also serves the review page at ``/`` (used when review runs
    standalone; in the combined app the dashboard owns ``/``).
    """
    from urllib.parse import quote

    from fastapi import File, Form, UploadFile
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

    if mount_root:
        @app.get("/", response_class=HTMLResponse)
        def _review_root(msg: str = "") -> str:
            return page("Review", _review_body(msg), active="review")

    @app.get("/review", response_class=HTMLResponse)
    def review_home(msg: str = "") -> str:
        return page("Review", _review_body(msg), active="review")

    @app.post("/review/api/submit")
    def api_submit(
        id: str = Form(...),
        original: str = Form(""),
        generated: str = Form(""),
        corrected: str = Form(""),
        decision: str = Form(...),
    ):
        record_feedback(
            id=id, original=original, generated=generated,
            corrected=corrected, decision=decision,
        )
        return JSONResponse({"ok": True, "id": id, "decision": decision, "stats": _live_stats()})

    @app.get("/review/export.xlsx")
    def export_xlsx():
        rows = load_queue(limit=5000, include_done=False)
        data = wexcel.build_workbook(rows)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="franco_review.xlsx"'},
        )

    @app.post("/review/import")
    def import_xlsx(file: UploadFile = File(...)):
        try:
            parsed = wexcel.parse_workbook(file.file.read())
            s = apply_imported_rows(parsed)
            msg = (
                f"Imported {file.filename}: {s['correct']} correct, {s['edit']} edited, "
                f"{s['reject']} rejected, {s['skipped']} skipped."
            )
        except Exception as exc:  # noqa: BLE001 - surface any parse error to the user
            msg = f"Import failed: {exc}"
        return RedirectResponse(url=f"/review?msg={quote(msg)}", status_code=303)

    @app.post("/review/submit")
    def submit(
        id: str = Form(...),
        original: str = Form(...),
        generated: str = Form(...),
        corrected: str = Form(""),
        decision: str = Form(...),
    ):
        record_feedback(
            id=id, original=original, generated=generated,
            corrected=corrected, decision=decision,
        )
        verb = {"correct": "Marked correct", "edit": "Saved edit", "reject": "Rejected"}.get(
            decision, "Saved"
        )
        return RedirectResponse(url=f"/review?msg={quote(verb + ' · ' + id)}", status_code=303)


def create_app():
    """Build a standalone review app (imports fastapi lazily)."""
    from fastapi import FastAPI

    app = FastAPI(title="Lebanese Franco Human Review")
    register_routes(app, mount_root=True)
    return app


def main() -> None:
    # The review UI is now part of the combined app so every tab works.
    from lebanese_franco_factory.webui.server import main as serve

    serve(default_port=8081, port_env="LFF_REVIEW_PORT")


if __name__ == "__main__":
    main()
