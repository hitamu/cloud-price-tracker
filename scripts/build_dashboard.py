#!/usr/bin/env python3
"""
Build the HTML dashboard from data/prices.json (and data/prices_baseline.json if present).
Outputs: index.html
"""

import json
from pathlib import Path

DATA_FILE     = Path("data/prices.json")
BASELINE_FILE = Path("data/prices_baseline.json")
OUT_FILE      = Path("index.html")


def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)


def load_baseline():
    if BASELINE_FILE.exists():
        with open(BASELINE_FILE) as f:
            return json.load(f)
    return None


def build_baseline_index(baseline):
    """Build a flat lookup: 'provider|instance_name' -> hourly_price"""
    if not baseline:
        return {}
    index = {}
    for pkey, pdata in baseline.get("providers", {}).items():
        for inst in pdata.get("instances", []):
            price = inst.get("hourly_usd") or inst.get("hourly_eur") or 0
            index[f"{pkey}|{inst['name']}"] = price
    return index


def build_html(data, baseline):
    updated_at       = data["updated_at"]
    baseline_set_at  = (baseline or {}).get("baseline_set_at")
    json_payload     = json.dumps(data, separators=(",", ":"))
    baseline_payload = json.dumps(build_baseline_index(baseline), separators=(",", ":")) if baseline else "null"
    baseline_date_js = json.dumps(baseline_set_at)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Cloud VM Price Tracker – Paris Region</title>
  <meta name="description" content="Daily updated VM pricing for Scaleway, AWS EC2 and OVHcloud – Paris region. Compare prices and track changes over time."/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
  <style>
    :root{{
      --bg:#0a0e1a;--surface:#111827;--surface2:#1a2235;--border:#1f2d45;
      --accent:#4f8ef7;--accent2:#7c5cfc;--gold:#f5c842;
      --text:#e2e8f0;--text-dim:#64748b;--text-muted:#94a3b8;
      --green:#22c55e;--red:#ef4444;--yellow:#eab308;
      --scw:#6b4fbb;--aws:#ff9900;--ovh:#0099da;
      --radius:12px;--shadow:0 4px 24px rgba(0,0,0,.4);
    }}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.6}}
    /* ── Header ── */
    header{{
      background:linear-gradient(135deg,#0d1b33 0%,#0a0e1a 100%);
      border-bottom:1px solid var(--border);padding:24px 32px;
      display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
      position:sticky;top:0;z-index:100;backdrop-filter:blur(10px);
    }}
    .header-left h1{{
      font-size:1.5rem;font-weight:700;
      background:linear-gradient(90deg,var(--accent),var(--accent2));
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    }}
    .header-left p{{font-size:.8rem;color:var(--text-dim);margin-top:2px}}
    .header-right{{display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
    .badge{{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:.75rem;font-weight:500;border:1px solid}}
    .badge-scw{{background:rgba(107,79,187,.15);color:#a78bfa;border-color:rgba(107,79,187,.3)}}
    .badge-aws{{background:rgba(255,153,0,.1);color:var(--aws);border-color:rgba(255,153,0,.25)}}
    .badge-ovh{{background:rgba(0,153,218,.1);color:#38bdf8;border-color:rgba(0,153,218,.25)}}
    .updated{{font-size:.75rem;color:var(--text-dim);display:flex;align-items:center;gap:6px}}
    .dot{{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
    /* ── Baseline bar ── */
    .baseline-bar{{
      background:rgba(79,142,247,.06);border-bottom:1px solid var(--border);
      padding:9px 32px;font-size:.78rem;color:var(--text-muted);
      display:flex;gap:20px;align-items:center;flex-wrap:wrap;
    }}
    .baseline-bar strong{{color:var(--accent)}}
    .chg-up{{color:var(--red);font-weight:600}}
    .chg-down{{color:var(--green);font-weight:600}}
    .chg-new{{color:var(--yellow);font-weight:600}}
    /* ── Stats bar ── */
    .stats-bar{{
      display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
      gap:12px;padding:20px 32px;background:var(--surface);border-bottom:1px solid var(--border);
    }}
    .stat-card{{
      background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);
      padding:14px 18px;transition:transform .2s,box-shadow .2s;
    }}
    .stat-card:hover{{transform:translateY(-2px);box-shadow:var(--shadow)}}
    .stat-label{{font-size:.7rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:.08em}}
    .stat-value{{font-size:1.5rem;font-weight:700;margin-top:4px}}
    .stat-sub{{font-size:.75rem;color:var(--text-muted);margin-top:2px}}
    /* ── Controls ── */
    .controls{{
      padding:16px 32px;background:var(--surface);border-bottom:1px solid var(--border);
      display:flex;gap:12px;flex-wrap:wrap;align-items:center;
    }}
    .search-wrap{{position:relative;flex:1;min-width:200px;max-width:340px}}
    .search-icon{{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--text-dim);font-size:.9rem;pointer-events:none}}
    input[type=text],select{{
      width:100%;background:var(--surface2);border:1px solid var(--border);color:var(--text);
      border-radius:8px;padding:8px 12px;font-size:.85rem;font-family:inherit;
      outline:none;transition:border-color .2s;
    }}
    input[type=text]{{padding-left:36px}}
    input[type=text]:focus,select:focus{{border-color:var(--accent)}}
    select{{cursor:pointer;min-width:130px}}
    .filter-group{{display:flex;gap:6px;flex-wrap:wrap}}
    .filter-btn{{
      padding:6px 14px;border-radius:20px;border:1px solid var(--border);
      background:var(--surface2);color:var(--text-muted);font-size:.8rem;
      font-family:inherit;cursor:pointer;transition:all .2s;
    }}
    .filter-btn:hover{{border-color:var(--accent);color:var(--accent)}}
    .filter-btn.active{{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}}
    .filter-btn.active.chg-up  {{background:var(--red);border-color:var(--red)}}
    .filter-btn.active.chg-down{{background:#16a34a;border-color:#16a34a}}
    .filter-btn.active.chg-new {{background:#a16207;border-color:#a16207}}
    /* ── Tabs ── */
    .main{{padding:24px 32px;max-width:1600px;margin:0 auto}}
    .tabs{{display:flex;gap:4px;border-bottom:1px solid var(--border);margin-bottom:24px;overflow-x:auto}}
    .tab{{
      padding:10px 20px;border-radius:8px 8px 0 0;border:1px solid transparent;
      background:transparent;color:var(--text-dim);font-size:.875rem;font-weight:500;
      cursor:pointer;font-family:inherit;white-space:nowrap;transition:all .2s;
      border-bottom:none;position:relative;bottom:-1px;
    }}
    .tab:hover{{color:var(--text);background:var(--surface2)}}
    .tab.active{{background:var(--surface);border-color:var(--border);color:var(--text);border-bottom-color:var(--surface)}}
    .tab-scw.active{{color:#a78bfa}}
    .tab-aws.active{{color:var(--aws)}}
    .tab-ovh.active{{color:#38bdf8}}
    .tab-all.active{{color:var(--accent)}}
    .section{{display:none}}
    .section.visible{{display:block}}
    /* ── Table ── */
    .table-wrap{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}}
    .table-header{{display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid var(--border);background:var(--surface2)}}
    .table-title{{font-size:.9rem;font-weight:600;display:flex;align-items:center;gap:8px}}
    .count-badge{{background:var(--surface);border:1px solid var(--border);color:var(--text-muted);font-size:.72rem;padding:2px 8px;border-radius:12px}}
    .provider-dot{{width:10px;height:10px;border-radius:50%;display:inline-block}}
    .provider-dot-scw{{background:var(--scw);box-shadow:0 0 6px var(--scw)}}
    .provider-dot-aws{{background:var(--aws);box-shadow:0 0 6px var(--aws)}}
    .provider-dot-ovh{{background:var(--ovh);box-shadow:0 0 6px var(--ovh)}}
    .provider-dot-all{{background:var(--accent);box-shadow:0 0 6px var(--accent)}}
    table{{width:100%;border-collapse:collapse;font-size:.83rem}}
    thead th{{
      background:var(--surface2);color:var(--text-dim);font-size:.72rem;font-weight:600;
      text-transform:uppercase;letter-spacing:.06em;padding:10px 16px;text-align:left;
      border-bottom:1px solid var(--border);cursor:pointer;user-select:none;
      white-space:nowrap;transition:color .2s;
    }}
    thead th:hover{{color:var(--accent)}}
    thead th .si{{margin-left:4px;opacity:.4}}
    thead th.sorted{{color:var(--accent)}}
    thead th.sorted .si{{opacity:1}}
    tbody tr{{border-bottom:1px solid rgba(31,45,69,.6);transition:background .15s}}
    tbody tr:last-child{{border-bottom:none}}
    tbody tr:hover{{background:var(--surface2)}}
    td{{padding:11px 16px;vertical-align:middle}}
    .iname{{font-weight:600;font-size:.85rem;color:var(--text);font-family:'Courier New',monospace}}
    .chip{{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:12px;font-size:.7rem;font-weight:500}}
    .chip-gpu{{background:rgba(245,200,66,.12);color:var(--gold);border:1px solid rgba(245,200,66,.25)}}
    .chip-arm{{background:rgba(34,197,94,.1);color:var(--green);border:1px solid rgba(34,197,94,.2)}}
    .chip-eos{{background:rgba(239,68,68,.1);color:var(--red);border:1px solid rgba(239,68,68,.2)}}
    .chip-prov{{font-size:.68rem;padding:2px 7px}}
    .chip-prov-scw{{background:rgba(107,79,187,.15);color:#a78bfa;border:1px solid rgba(107,79,187,.25)}}
    .chip-prov-aws{{background:rgba(255,153,0,.1);color:var(--aws);border:1px solid rgba(255,153,0,.2)}}
    .chip-prov-ovh{{background:rgba(0,153,218,.1);color:#38bdf8;border:1px solid rgba(0,153,218,.2)}}
    .price{{font-weight:600;font-size:.9rem}}
    .price-sub{{font-size:.75rem;color:var(--text-muted)}}
    /* Delta */
    .delta{{font-size:.8rem;font-weight:600;white-space:nowrap}}
    .delta-up  {{color:var(--red)}}
    .delta-down{{color:var(--green)}}
    .delta-same{{color:var(--text-dim)}}
    .delta-new {{color:var(--yellow)}}
    .delta-none{{color:var(--text-dim);opacity:.35}}
    /* Bar */
    .bar-wrap{{display:flex;align-items:center;gap:8px;min-width:80px}}
    .bar{{height:5px;border-radius:3px;opacity:.7;transition:width .4s;min-width:2px}}
    .bar-aws{{background:var(--aws)}}
    .bar-scw{{background:var(--scw)}}
    .bar-ovh{{background:var(--ovh)}}
    .bar-all{{background:var(--accent)}}
    .no-results{{padding:60px 20px;text-align:center;color:var(--text-dim)}}
    .no-results .icon{{font-size:2.5rem;margin-bottom:12px}}
    footer{{text-align:center;padding:24px 32px;color:var(--text-dim);font-size:.78rem;border-top:1px solid var(--border);margin-top:40px}}
    footer a{{color:var(--accent);text-decoration:none}}
    footer a:hover{{text-decoration:underline}}
    @media(max-width:768px){{
      header,.stats-bar,.controls,.main,.baseline-bar{{padding-left:16px;padding-right:16px}}
      .stats-bar{{grid-template-columns:repeat(2,1fr)}}
      table{{font-size:.78rem}}
      td,thead th{{padding:8px 10px}}
      .bar-wrap{{min-width:50px}}
    }}
  </style>
</head>
<body>

<header>
  <div class="header-left">
    <h1>☁️ Cloud VM Price Tracker</h1>
    <p>Paris Region · Daily updated · On-demand pricing</p>
  </div>
  <div class="header-right">
    <span class="badge badge-scw">🟣 Scaleway <span id="scw-count">—</span></span>
    <span class="badge badge-aws">🟠 AWS EC2 <span id="aws-count">—</span></span>
    <span class="badge badge-ovh">🔵 OVHcloud <span id="ovh-count">—</span></span>
    <span class="updated"><span class="dot"></span>Updated: <span id="updated-at">—</span></span>
  </div>
</header>

<div id="baseline-bar" class="baseline-bar" style="display:none">
  📌 Baseline snapshot: <strong id="baseline-date">—</strong>
  &nbsp;·&nbsp;
  <span class="chg-up"   id="chg-up">—</span>
  <span class="chg-down" id="chg-down">— </span>
  <span class="chg-new"  id="chg-new">—</span>
  &nbsp;·&nbsp;<span style="opacity:.6">vs. reference prices</span>
</div>

<div class="stats-bar">
  <div class="stat-card">
    <div class="stat-label">Total Instances</div>
    <div class="stat-value" id="stat-total" style="color:var(--accent)">—</div>
    <div class="stat-sub">across 3 providers</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Cheapest VM</div>
    <div class="stat-value" id="stat-cheapest" style="color:var(--green);font-size:1.1rem">—</div>
    <div class="stat-sub" id="stat-cheapest-name">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Scaleway Min</div>
    <div class="stat-value" id="stat-scw" style="color:#a78bfa;font-size:1.1rem">—</div>
    <div class="stat-sub" id="stat-scw-name">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">AWS EC2 Min</div>
    <div class="stat-value" id="stat-aws" style="color:var(--aws);font-size:1.1rem">—</div>
    <div class="stat-sub" id="stat-aws-name">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">OVHcloud Min</div>
    <div class="stat-value" id="stat-ovh" style="color:#38bdf8;font-size:1.1rem">—</div>
    <div class="stat-sub" id="stat-ovh-name">—</div>
  </div>
</div>

<div class="controls">
  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input type="text" id="search" placeholder="Search instance (e.g. t3.medium, GP1-S…)"/>
  </div>
  <select id="sort-by">
    <option value="price_asc">Price: Low → High</option>
    <option value="price_desc">Price: High → Low</option>
    <option value="vcpu_asc">vCPU: Low → High</option>
    <option value="vcpu_desc">vCPU: High → Low</option>
    <option value="ram_asc">RAM: Low → High</option>
    <option value="ram_desc">RAM: High → Low</option>
    <option value="name_asc">Name: A → Z</option>
    <option value="delta_desc">Biggest Change First</option>
  </select>
  <div class="filter-group" id="arch-group">
    <button class="filter-btn active" onclick="setArch('all',this)">All CPU</button>
    <button class="filter-btn" onclick="setArch('x86_64',this)">x86</button>
    <button class="filter-btn" onclick="setArch('arm64',this)">ARM</button>
    <button class="filter-btn" onclick="setArch('gpu',this)">GPU</button>
  </div>
  <div class="filter-group" id="delta-group">
    <button class="filter-btn active" id="dfbtn-all"  onclick="setDelta('all',this)">All</button>
    <button class="filter-btn chg-up"  id="dfbtn-up"   onclick="setDelta('up',this)">↑ Up</button>
    <button class="filter-btn chg-down"id="dfbtn-down" onclick="setDelta('down',this)">↓ Down</button>
    <button class="filter-btn chg-new" id="dfbtn-new"  onclick="setDelta('new',this)">★ New</button>
  </div>
</div>

<div class="main">
  <div class="tabs">
    <button class="tab tab-all active" onclick="switchTab('all',this)">🌐 All Providers</button>
    <button class="tab tab-scw"        onclick="switchTab('scaleway',this)">🟣 Scaleway</button>
    <button class="tab tab-aws"        onclick="switchTab('aws',this)">🟠 AWS EC2</button>
    <button class="tab tab-ovh"        onclick="switchTab('ovh',this)">🔵 OVHcloud</button>
  </div>

  <div id="section-all" class="section visible">
    <div class="table-wrap">
      <div class="table-header">
        <span class="table-title"><span class="provider-dot provider-dot-all"></span> All Providers <span class="count-badge" id="all-count-badge">0</span></span>
      </div>
      <div id="all-table-container"></div>
    </div>
  </div>
  <div id="section-scaleway" class="section">
    <div class="table-wrap">
      <div class="table-header">
        <span class="table-title"><span class="provider-dot provider-dot-scw"></span> Scaleway – fr-par-1 <span class="count-badge" id="scw-count-badge">0</span></span>
      </div>
      <div id="scw-table-container"></div>
    </div>
  </div>
  <div id="section-aws" class="section">
    <div class="table-wrap">
      <div class="table-header">
        <span class="table-title"><span class="provider-dot provider-dot-aws"></span> AWS EC2 – eu-west-3 (Paris) <span class="count-badge" id="aws-count-badge">0</span></span>
      </div>
      <div id="aws-table-container"></div>
    </div>
  </div>
  <div id="section-ovh" class="section">
    <div class="table-wrap">
      <div class="table-header">
        <span class="table-title"><span class="provider-dot provider-dot-ovh"></span> OVHcloud – GRA/SBG (Paris) <span class="count-badge" id="ovh-count-badge">0</span></span>
      </div>
      <div id="ovh-table-container"></div>
    </div>
  </div>
</div>

<footer>
  Data from public APIs:
  <a href="https://www.scaleway.com/en/pricing/" target="_blank">Scaleway</a> ·
  <a href="https://aws.amazon.com/ec2/pricing/on-demand/" target="_blank">AWS EC2</a> ·
  <a href="https://www.ovhcloud.com/en-gb/public-cloud/prices/" target="_blank">OVHcloud</a>
  · Updated daily via GitHub Actions · Prices exclude VAT
</footer>

<script>
const RAW           = {json_payload};
const BASELINE      = {baseline_payload};   // null if no baseline exists yet
const BASELINE_DATE = {baseline_date_js};

let currentArch  = 'all';
let currentSort  = 'price_asc';
let currentSearch= '';
let currentDelta = 'all';

// ─── flatten + annotate with delta ───────────────────────────────────────────
function flatten(data) {{
  const all = [];
  for (const [pKey, pData] of Object.entries(data.providers)) {{
    for (const inst of pData.instances) {{
      const curPrice = inst.hourly_usd ?? inst.hourly_eur ?? 0;
      let delta = {{ type:'none', pct:0 }};
      if (BASELINE) {{
        const basePrice = BASELINE[pKey + '|' + inst.name];
        if (basePrice == null) {{
          delta = {{ type:'new', pct:0 }};
        }} else if (basePrice === 0 || curPrice === 0) {{
          delta = {{ type:'same', pct:0 }};
        }} else {{
          const pct = ((curPrice - basePrice) / basePrice) * 100;
          delta = {{ type: Math.abs(pct) < 0.001 ? 'same' : pct > 0 ? 'up' : 'down', pct: Math.abs(pct) }};
        }}
      }}
      all.push({{ ...inst, provider:pKey, provider_name:pData.name, curPrice, delta }});
    }}
  }}
  return all;
}}

const ALL = flatten(RAW);

// ─── formatters ──────────────────────────────────────────────────────────────
function fHourly(i)  {{ return i.hourly_usd!=null ? '$'+i.hourly_usd.toFixed(4)+'/hr' : i.hourly_eur!=null ? '€'+i.hourly_eur.toFixed(4)+'/hr' : '—'; }}
function fMonthly(i) {{ return i.monthly_usd!=null? '$'+i.monthly_usd.toFixed(2)+'/mo': i.monthly_eur!=null? '€'+i.monthly_eur.toFixed(2)+'/mo': '—'; }}

function deltaHtml(d) {{
  if (!BASELINE) return '<span class="delta delta-none">—</span>';
  switch(d.type) {{
    case 'up':   return `<span class="delta delta-up">↑ +${{d.pct.toFixed(2)}}%</span>`;
    case 'down': return `<span class="delta delta-down">↓ -${{d.pct.toFixed(2)}}%</span>`;
    case 'new':  return `<span class="delta delta-new">★ NEW</span>`;
    case 'same': return `<span class="delta delta-same">—</span>`;
    default:     return `<span class="delta delta-none">—</span>`;
  }}
}}

// ─── filter + sort ───────────────────────────────────────────────────────────
function applyFilters(list) {{
  return list.filter(i => {{
    if (currentSearch && !i.name.toLowerCase().includes(currentSearch)) return false;
    if (currentArch === 'arm64')  return i.arch === 'arm64';
    if (currentArch === 'x86_64') return i.arch === 'x86_64';
    if (currentArch === 'gpu')    return i.gpu > 0;
    if (currentDelta !== 'all')   return i.delta.type === currentDelta;
    return true;
  }});
}}

function applySort(list) {{
  return [...list].sort((a,b) => {{
    switch(currentSort) {{
      case 'price_asc':   return a.curPrice - b.curPrice;
      case 'price_desc':  return b.curPrice - a.curPrice;
      case 'vcpu_asc':    return a.vcpu - b.vcpu;
      case 'vcpu_desc':   return b.vcpu - a.vcpu;
      case 'ram_asc':     return a.ram_gb - b.ram_gb;
      case 'ram_desc':    return b.ram_gb - a.ram_gb;
      case 'name_asc':    return a.name.localeCompare(b.name);
      case 'delta_desc': {{
        const order = {{new:0,up:1,down:2,same:3,none:4}};
        const ta = order[a.delta.type]??5, tb = order[b.delta.type]??5;
        return ta !== tb ? ta-tb : b.delta.pct - a.delta.pct;
      }}
      default: return 0;
    }}
  }});
}}

// ─── render ──────────────────────────────────────────────────────────────────
function pc(provider) {{ return {{scaleway:'scw',aws:'aws',ovh:'ovh'}}[provider]||'all'; }}

function renderTable(list, containerId, showProv=false) {{
  const el = document.getElementById(containerId);
  if (!list.length) {{
    el.innerHTML = `<div class="no-results"><div class="icon">🔍</div><p>No instances match your filters.</p></div>`;
    return;
  }}
  const maxP = Math.max(...list.map(i=>i.curPrice), 0.0001);
  const rows = list.map(i => {{
    const pct  = Math.max(3, Math.round((i.curPrice/maxP)*100));
    const cls  = pc(i.provider);
    const chips = [];
    if (i.arch==='arm64') chips.push(`<span class="chip chip-arm">ARM</span>`);
    if (i.gpu>0)          chips.push(`<span class="chip chip-gpu">GPU ×${{i.gpu}}</span>`);
    if (i.end_of_service) chips.push(`<span class="chip chip-eos">EOS</span>`);
    const provChip = showProv ? `<span class="chip chip-prov chip-prov-${{cls}}">${{i.provider_name}}</span> ` : '';
    return `<tr>
      <td>${{provChip}}<span class="iname">${{i.name}}</span> ${{chips.join(' ')}}</td>
      <td>${{i.vcpu}}</td>
      <td>${{i.ram_gb}} GB</td>
      <td class="price">${{fHourly(i)}}</td>
      <td><span class="price price-sub">${{fMonthly(i)}}</span></td>
      <td>${{deltaHtml(i.delta)}}</td>
      <td><div class="bar-wrap"><div class="bar bar-${{cls}}" style="width:${{pct}}%"></div></div></td>
    </tr>`;
  }}).join('');

  el.innerHTML = `<table>
    <thead><tr>
      <th>Instance</th>
      <th onclick="sortBy('vcpu')">vCPU <span class="si">↕</span></th>
      <th onclick="sortBy('ram')">RAM <span class="si">↕</span></th>
      <th onclick="sortBy('price')">Hourly <span class="si">↕</span></th>
      <th>Monthly (est.)</th>
      <th onclick="sortBy('delta')">${{BASELINE?'Δ vs Baseline <span class="si">↕</span>':'Δ'}}</th>
      <th>Relative Cost</th>
    </tr></thead>
    <tbody>${{rows}}</tbody>
  </table>`;
}}

function renderAll() {{
  const fAll = applySort(applyFilters(ALL));
  const fScw = applySort(applyFilters(ALL.filter(i=>i.provider==='scaleway')));
  const fAws = applySort(applyFilters(ALL.filter(i=>i.provider==='aws')));
  const fOvh = applySort(applyFilters(ALL.filter(i=>i.provider==='ovh')));
  renderTable(fAll,'all-table-container',true);
  renderTable(fScw,'scw-table-container');
  renderTable(fAws,'aws-table-container');
  renderTable(fOvh,'ovh-table-container');
  document.getElementById('all-count-badge').textContent = fAll.length+' instances';
  document.getElementById('scw-count-badge').textContent = fScw.length+' instances';
  document.getElementById('aws-count-badge').textContent = fAws.length+' instances';
  document.getElementById('ovh-count-badge').textContent = fOvh.length+' instances';
}}

// ─── event handlers ──────────────────────────────────────────────────────────
function switchTab(tab, el) {{
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('visible'));
  document.getElementById('section-'+tab).classList.add('visible');
}}

function setArch(arch, el) {{
  currentArch = arch;
  document.querySelectorAll('#arch-group .filter-btn').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
  renderAll();
}}

function setDelta(delta, el) {{
  currentDelta = delta;
  document.querySelectorAll('#delta-group .filter-btn').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
  renderAll();
}}

function sortBy(col) {{
  if (col === 'delta') {{ currentSort = 'delta_desc'; }}
  else if (currentSort === col+'_asc') {{ currentSort = col+'_desc'; }}
  else {{ currentSort = col+'_asc'; }}
  document.getElementById('sort-by').value = currentSort;
  renderAll();
}}

// ─── init ─────────────────────────────────────────────────────────────────────
function init() {{
  const scw = RAW.providers.scaleway.instances;
  const aws = RAW.providers.aws.instances;
  const ovh = RAW.providers.ovh.instances;

  document.getElementById('scw-count').textContent = scw.length;
  document.getElementById('aws-count').textContent = aws.length;
  document.getElementById('ovh-count').textContent = ovh.length;
  document.getElementById('stat-total').textContent = ALL.length;
  document.getElementById('updated-at').textContent = RAW.updated_at.replace('T',' ').replace('Z',' UTC');

  const sorted = [...ALL].sort((a,b)=>a.curPrice-b.curPrice);
  const cheapest = sorted[0];
  if (cheapest) {{
    document.getElementById('stat-cheapest').textContent = fHourly(cheapest);
    document.getElementById('stat-cheapest-name').textContent = cheapest.name+' ('+cheapest.provider_name+')';
  }}
  ['scaleway','aws','ovh'].forEach(p => {{
    const cheapP = [...ALL].filter(i=>i.provider===p).sort((a,b)=>a.curPrice-b.curPrice)[0];
    const idMap  = {{scaleway:'scw',aws:'aws',ovh:'ovh'}};
    if (cheapP) {{
      document.getElementById('stat-'+idMap[p]).textContent     = fHourly(cheapP);
      document.getElementById('stat-'+idMap[p]+'-name').textContent = cheapP.name;
    }}
  }});

  // Baseline summary bar
  if (BASELINE) {{
    const ups   = ALL.filter(i=>i.delta.type==='up').length;
    const downs = ALL.filter(i=>i.delta.type==='down').length;
    const news  = ALL.filter(i=>i.delta.type==='new').length;
    const bar = document.getElementById('baseline-bar');
    bar.style.display = 'flex';
    document.getElementById('baseline-date').textContent = (BASELINE_DATE||'—').replace('T',' ').replace('Z',' UTC');
    document.getElementById('chg-up').textContent   = `↑ ${{ups}} higher`;
    document.getElementById('chg-down').textContent = `↓ ${{downs}} lower  `;
    document.getElementById('chg-new').textContent  = `★ ${{news}} new`;
  }}

  document.getElementById('search').addEventListener('input', e => {{
    currentSearch = e.target.value.trim().toLowerCase();
    renderAll();
  }});
  document.getElementById('sort-by').addEventListener('change', e => {{
    currentSort = e.target.value;
    renderAll();
  }});

  renderAll();
}}

document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>
"""


def main():
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} not found. Run scripts/fetch_prices.py first.")
        exit(1)
    data     = load_data()
    baseline = load_baseline()
    html     = build_html(data, baseline)
    OUT_FILE.write_text(html, encoding="utf-8")
    scw = len(data["providers"]["scaleway"]["instances"])
    aws = len(data["providers"]["aws"]["instances"])
    ovh = len(data["providers"]["ovh"]["instances"])
    base_msg = f"baseline: {BASELINE_FILE}" if baseline else "no baseline yet"
    print(f"Built index.html  ({scw} SCW + {aws} AWS + {ovh} OVH = {scw+aws+ovh} total, {base_msg})")


if __name__ == "__main__":
    main()
