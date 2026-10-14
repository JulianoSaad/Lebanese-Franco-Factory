"""Shared visual theme + page shell for the dashboard and review apps.

A single design system so both local apps look like one product: a deep
cedar-green / parchment palette, cards, a top nav bar, and a footer. Keeping
it here means the two FastAPI apps stay tiny and never drift in style.
"""

from __future__ import annotations

BASE_CSS = """
:root{
  --green:#159c6f; --green-2:#1fb07f; --green-3:#31c795;
  --gold:#e0bd6b; --gold-soft:#f0dfb0;
  --bg:#0d120f; --bg-2:#0a0e0c; --card:#151b17; --card-2:#1b2320;
  --ink:#e9ece7; --muted:#8b968d;
  --border:#26302a; --border-2:#1e2622;
  --ok:#3fd08a; --ok-bg:#12281d; --ok-bd:#1f5138;
  --edit:#5aa9f0; --edit-bg:#12212f; --edit-bd:#254967;
  --rej:#f0736f; --rej-bg:#2c1717; --rej-bd:#5a2a28;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.35);
  --radius:12px;
}
*{box-sizing:border-box}
body{
  margin:0;background:var(--bg);color:var(--ink);
  font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  line-height:1.5;-webkit-font-smoothing:antialiased;
}
a{color:var(--green-2);text-decoration:none}
a:hover{text-decoration:underline;color:var(--green-3)}
.wrap{max-width:1080px;margin:0 auto;padding:1.5rem 1.25rem 4rem}

/* ---- top nav ---- */
.nav{background:linear-gradient(180deg,#101913,#0a0f0c);color:#fff;
  box-shadow:var(--shadow);position:sticky;top:0;z-index:10;
  border-bottom:1px solid #1c2620}
.nav .inner{max-width:1080px;margin:0 auto;display:flex;align-items:center;
  gap:.4rem;padding:.7rem 1.25rem;flex-wrap:wrap}
.brand{font-weight:700;font-size:1.05rem;letter-spacing:.2px;display:flex;
  align-items:center;gap:.5rem;margin-right:1rem;color:#f3f5f1}
.brand .cedar{color:var(--gold)}
.nav a.link{color:#9fb3a7;padding:.35rem .7rem;border-radius:8px;font-size:.92rem;
  font-weight:500}
.nav a.link:hover{background:rgba(255,255,255,.06);text-decoration:none;color:#fff}
.nav a.link.active{background:rgba(49,199,149,.16);color:var(--green-3)}
.nav .spacer{flex:1}
.nav .tag{font-size:.72rem;color:var(--gold-soft);border:1px solid rgba(224,189,107,.4);
  padding:.15rem .5rem;border-radius:20px;letter-spacing:.04em}

/* ---- headings ---- */
h1{font-size:1.6rem;margin:.2rem 0 .1rem;letter-spacing:-.01em}
h2{font-size:1.15rem;margin:1.8rem 0 .6rem;letter-spacing:-.01em}
.sub{color:var(--muted);margin:.1rem 0 1.2rem;font-size:.95rem}

/* ---- cards & grid ---- */
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.1rem 1.2rem;box-shadow:var(--shadow)}
.grid{display:grid;gap:.9rem}
.kpis{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:.9rem 1rem;box-shadow:var(--shadow)}
.kpi .n{font-size:1.7rem;font-weight:800;line-height:1.05;color:var(--green-3)}
.kpi .l{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;
  margin-top:.15rem;font-weight:600}
.kpi.accent{background:linear-gradient(145deg,#12563e,#0c3728);border-color:#1c6b4c}
.kpi.accent .n{color:#eafff4}.kpi.accent .l{color:var(--gold-soft)}

/* ---- progress bar ---- */
.bar{height:9px;background:var(--border);border-radius:6px;overflow:hidden;margin:.5rem 0}
.bar>span{display:block;height:100%;
  background:linear-gradient(90deg,var(--green-2),var(--green-3))}

/* ---- pills ---- */
.pill{padding:.1rem .55rem;border-radius:20px;font-size:.72rem;font-weight:700;
  display:inline-block;letter-spacing:.02em}
.p-correct{background:var(--ok-bg);color:var(--ok);border:1px solid var(--ok-bd)}
.p-edit{background:var(--edit-bg);color:var(--edit);border:1px solid var(--edit-bd)}
.p-reject{background:var(--rej-bg);color:var(--rej);border:1px solid var(--rej-bd)}
.p-neutral{background:#2a2416;color:var(--gold);border:1px solid #4a3e1f}

/* ---- tables ---- */
.tbl{width:100%;border-collapse:collapse;font-size:.9rem}
.tbl th{text-align:left;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;
  color:var(--muted);padding:.55rem .6rem;border-bottom:2px solid var(--border)}
.tbl td{padding:.55rem .6rem;border-bottom:1px solid var(--border-2);vertical-align:middle}
.tbl tr:hover td{background:var(--card-2)}
.ar{font-size:1.15rem;direction:rtl;font-weight:600;color:#f2f4ef}
.fr{font-size:1rem}
.muted{color:var(--muted)}
.mono{font-family:ui-monospace,'SF Mono',Menlo,monospace;font-size:.78rem;color:var(--muted)}
.num{text-align:right;font-variant-numeric:tabular-nums}

/* ---- buttons ---- */
.btn{border:0;padding:.5rem .95rem;border-radius:8px;cursor:pointer;font-weight:600;
  font-size:.9rem;color:#04140d;background:var(--green-2);transition:filter .12s}
.btn:hover{filter:brightness(1.1)}
.btn.ghost{background:var(--card-2);color:var(--green-3);border:1px solid var(--border)}
.btn.sm{padding:.3rem .55rem;font-size:.82rem}
.b-correct{background:var(--ok)}.b-edit{background:var(--edit)}.b-reject{background:var(--rej)}
.iconbtn{border:1px solid var(--border);background:var(--card-2);color:var(--ink);
  border-radius:7px;cursor:pointer;padding:.28rem .5rem;font-size:.95rem;line-height:1;
  transition:.12s}
.iconbtn:hover{filter:brightness(1.15)}
.iconbtn.c:hover{background:var(--ok-bg);border-color:var(--ok-bd);color:var(--ok)}
.iconbtn.e:hover{background:var(--edit-bg);border-color:var(--edit-bd);color:var(--edit)}
.iconbtn.r:hover{background:var(--rej-bg);border-color:var(--rej-bd);color:var(--rej)}

input,select{font:inherit;padding:.42rem .55rem;border:1px solid var(--border);
  border-radius:8px;background:var(--bg-2);color:var(--ink)}
input::placeholder{color:var(--muted)}
input:focus,select:focus{outline:2px solid var(--green-3);outline-offset:-1px;
  background:var(--card-2)}
.field{width:100%}

/* ---- banners ---- */
.banner{padding:.65rem .95rem;border-radius:10px;margin:0 0 1rem;font-weight:600}
.banner.ok{background:var(--ok-bg);border:1px solid var(--ok-bd);color:var(--ok)}

/* ---- toolbar ---- */
.toolbar{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;margin:.4rem 0 1rem}
.toolbar .grow{flex:1;min-width:180px}
.chip{padding:.3rem .7rem;border-radius:20px;border:1px solid var(--border);
  background:var(--card-2);cursor:pointer;font-size:.85rem;font-weight:600;color:var(--muted)}
.chip.on{background:var(--green-2);color:#04140d;border-color:var(--green-2)}

.footer{color:var(--muted);font-size:.82rem;margin-top:2.5rem;text-align:center}
.row-done td{opacity:.45}
.flex{display:flex;gap:.4rem;align-items:center}
.wrap-actions{white-space:nowrap}
"""


def _nav(active: str) -> str:
    links = [
        ("dashboard", "/", "Dashboard"),
        ("datasets", "/datasets", "Datasets"),
        ("review", "/review", "Review"),
    ]
    items = "".join(
        f"<a class='link{' active' if key == active else ''}' href='{href}'>{label}</a>"
        for key, href, label in links
    )
    return f"""
<nav class='nav'><div class='inner'>
  <span class='brand'><span class='cedar'>&#127794;</span> Lebanese Franco Factory</span>
  {items}
  <span class='spacer'></span>
  <span class='tag'>Language Lab</span>
</div></nav>
"""


def page(title: str, body: str, active: str = "", extra_head: str = "") -> str:
    """Wrap page ``body`` in the shared shell (nav + styling + footer)."""
    return f"""<!doctype html>
<html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{title} &middot; Franco Factory</title>
<style>{BASE_CSS}</style>{extra_head}
</head><body>
{_nav(active)}
<div class='wrap'>
{body}
<div class='footer'>Lebanese Language Lab &middot; Franco Factory &mdash; local console</div>
</div>
</body></html>"""
