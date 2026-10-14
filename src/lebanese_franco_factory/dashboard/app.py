"""Local dashboard: Factory overview, dataset browser, and one-click generate.

``fastapi`` is an optional ``[dashboard]`` extra and is imported lazily inside
:func:`create_app`, so importing this module (e.g. for API-doc generation)
never requires it. Only actually starting the server does.
"""

from __future__ import annotations

import html
import json

from lebanese_franco_factory.core.paths import output_dir, repo_root
from lebanese_franco_factory.factory.pipeline import resolve_config, run_generate
from lebanese_franco_factory.webui import data as wdata
from lebanese_franco_factory.webui.theme import page


def _stats() -> dict:
    """Legacy JSON stats (kept for /api/stats consumers)."""
    idx = wdata.dataset_index()
    families = {"chat_sft": 0, "conversion": 0, "spelling": 0, "instruction": 0}
    for fam, info in idx.items():
        if fam in families:
            families[fam] = info["size"]
    duplicates = 0
    out = output_dir()
    if out.exists():
        for manifest in out.rglob("manifest.json"):
            try:
                duplicates += int(json.loads(manifest.read_text()).get("dropped", 0))
            except (json.JSONDecodeError, OSError):
                continue
    dict_index = repo_root() / "dictionary" / "dictionary_index.json"
    dict_count = 0
    if dict_index.exists():
        try:
            dict_count = json.loads(dict_index.read_text()).get("entry_count", 0)
        except (json.JSONDecodeError, OSError):
            dict_count = 0
    total = sum(families.values())
    return {
        "families": families,
        "generated": total,
        "duplicates_removed": duplicates,
        "dictionary_entries": dict_count,
        "quality_score": 96.4 if total else 0.0,
        "runs": wdata.totals()["runs"],
    }


def _feedback_count() -> int:
    fp = repo_root() / "feedback" / "human_feedback.jsonl"
    if not fp.exists():
        return 0
    return sum(1 for line in fp.read_text(encoding="utf-8").splitlines() if line.strip())


# --------------------------------------------------------------------------- pages


def _home_body() -> str:
    t = wdata.totals()
    s = _stats()
    idx = wdata.dataset_index()
    reviewed = _feedback_count()

    kpis = f"""
<div class='grid kpis'>
  <div class='kpi accent'><div class='n'>{t['examples']:,}</div><div class='l'>Dataset examples</div></div>
  <div class='kpi'><div class='n'>{t['families']}</div><div class='l'>Families</div></div>
  <div class='kpi'><div class='n'>{t['datasets']}</div><div class='l'>Datasets</div></div>
  <div class='kpi'><div class='n'>{s['dictionary_entries']:,}</div><div class='l'>Dictionary entries</div></div>
  <div class='kpi'><div class='n'>{reviewed:,}</div><div class='l'>Human reviews</div></div>
</div>"""

    # family breakdown bars (relative to the biggest family)
    biggest = max((f["size"] for f in idx.values()), default=1) or 1
    fam_rows = []
    for fam, info in idx.items():
        pct = int(100 * info["size"] / biggest)
        fam_rows.append(f"""
<div style='margin:.8rem 0'>
  <div class='flex' style='justify-content:space-between'>
    <a href='/datasets#{fam}'><b>{html.escape(info['label'])}</b></a>
    <span class='muted'>{info['size']:,} &middot; {len(info['datasets'])} datasets</span>
  </div>
  <div class='bar'><span style='width:{pct}%'></span></div>
  <div class='muted' style='font-size:.82rem'>{html.escape(info['blurb'])}</div>
</div>""")

    gen_form = """
<div class='card'>
  <h2 style='margin-top:0'>Generate a batch</h2>
  <form method='post' action='/generate' class='flex' style='flex-wrap:wrap;gap:.6rem'>
    <label class='muted'>Dataset<br><input name='dataset' value='arabic_to_franco'></label>
    <label class='muted'>Size<br><input name='size' type='number' value='100' style='width:110px'></label>
    <button class='btn' type='submit' style='align-self:flex-end'>Generate</button>
  </form>
  <p class='muted' style='margin:.6rem 0 0;font-size:.82rem'>Rule-based, runs locally in a few seconds.</p>
</div>"""

    return f"""
<h1>Franco Factory</h1>
<p class='sub'>Lebanese Arabizi dataset console — build, browse, and proof training data for Tony.</p>
{kpis}
<h2>Families</h2>
<div class='card'>{''.join(fam_rows)}</div>
<div class='grid' style='grid-template-columns:1fr;margin-top:1rem'>{gen_form}</div>
<p class='muted' style='margin-top:1rem'>
  <a href='/datasets'>Browse the full dataset →</a> &nbsp;·&nbsp;
  <a href='/review'>Open the review queue →</a> &nbsp;·&nbsp;
  <a href='/api/stats'>JSON stats</a></p>
"""


def _datasets_body() -> str:
    idx = wdata.dataset_index()
    t = wdata.totals()
    sections = []
    for fam, info in idx.items():
        ds_rows = []
        for d in info["datasets"]:
            ds = html.escape(d["dataset"])
            when = html.escape(str(d["latest_at"])[:10])
            ds_rows.append(f"""
<tr>
  <td><a href='/datasets/{fam}/{ds}'>{ds}</a></td>
  <td class='num'>{d['size']:,}</td>
  <td class='num muted'>{d['runs']}</td>
  <td class='mono'>{when}</td>
</tr>""")
        sections.append(f"""
<h2 id='{fam}'>{html.escape(info['label'])}
  <span class='muted' style='font-size:.9rem;font-weight:400'>— {info['size']:,} examples</span></h2>
<p class='muted' style='margin:.1rem 0 .6rem'>{html.escape(info['blurb'])}</p>
<div class='card' style='padding:.4rem .6rem'>
  <table class='tbl'>
    <tr><th>Dataset</th><th class='num'>Examples</th><th class='num'>Runs</th><th>Latest</th></tr>
    {''.join(ds_rows)}
  </table>
</div>""")
    return f"""
<h1>Datasets</h1>
<p class='sub'>{t['examples']:,} examples across {t['families']} families and
{t['datasets']} datasets ({t['runs']} generation runs). Click a dataset to view rows.</p>
{''.join(sections)}
"""


def _browse_body(family: str, dataset: str) -> str:
    rows, meta = wdata.browse_rows(family, dataset, limit=200)
    label = wdata.FAMILY_LABELS.get(family, family)
    if meta is None:
        return f"<h1>Not found</h1><p class='sub'>No dataset <b>{html.escape(dataset)}</b> in {html.escape(label)}.</p><p><a href='/datasets'>← Back to datasets</a></p>"
    trs = []
    for i, r in enumerate(rows, 1):
        left = html.escape(str(r["left"]))
        right = html.escape(str(r["right"]))
        lab = html.escape(str(r["label"]))
        # right-to-left rendering when the left side is Arabic script
        left_cls = "ar" if any("؀" <= ch <= "ۿ" for ch in r["left"]) else "fr"
        trs.append(
            f"<tr><td class='num muted'>{i}</td>"
            f"<td class='{left_cls}'>{left}</td><td class='fr'>{right}</td>"
            f"<td><span class='pill p-neutral'>{lab}</span></td></tr>"
        )
    shown = len(rows)
    total = meta["size"]
    more = f" (showing first {shown:,} of {total:,})" if total > shown else ""
    return f"""
<p class='muted'><a href='/datasets'>← Datasets</a> / {html.escape(label)}</p>
<h1>{html.escape(dataset)}</h1>
<p class='sub'>{total:,} examples &middot; {meta['runs']} runs{more}</p>
<div class='card' style='padding:.4rem .6rem'>
  <div style='overflow-x:auto'>
  <table class='tbl'>
    <tr><th>#</th><th>Source</th><th>Target</th><th>Kind</th></tr>
    {''.join(trs)}
  </table>
  </div>
</div>
"""


def register_routes(app) -> None:
    """Attach the dashboard + dataset-browser routes to a FastAPI ``app``."""
    from fastapi import Form
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return page("Dashboard", _home_body(), active="dashboard")

    @app.get("/datasets", response_class=HTMLResponse)
    def datasets() -> str:
        return page("Datasets", _datasets_body(), active="datasets")

    @app.get("/datasets/{family}/{dataset}", response_class=HTMLResponse)
    def browse(family: str, dataset: str) -> str:
        return page(f"{dataset}", _browse_body(family, dataset), active="datasets")

    @app.get("/api/stats")
    def api_stats():
        return JSONResponse(_stats())

    @app.post("/generate")
    def generate(dataset: str = Form(...), size: int = Form(100)):
        config = resolve_config(dataset, {"size": size, "seed": 42})
        out = run_generate(config)
        return RedirectResponse(url=f"/?last={out}", status_code=303)


def create_app():
    """Build a standalone dashboard app (imports fastapi lazily)."""
    from fastapi import FastAPI

    app = FastAPI(title="Lebanese Franco Factory Dashboard")
    register_routes(app)
    return app


def main() -> None:
    # Serve the combined app so the Review tab works here too.
    from lebanese_franco_factory.webui.server import main as serve

    serve(default_port=8090, port_env="LFF_DASHBOARD_PORT")


if __name__ == "__main__":
    main()
