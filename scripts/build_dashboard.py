#!/usr/bin/env python3
"""
Build the HTML dashboard from data/prices.json.
Outputs: index.html
"""

import json
from pathlib import Path

DATA_FILE = Path("data/prices.json")
OUT_FILE = Path("index.html")


def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)


def build_html(data):
    updated_at = data["updated_at"]
    providers = data["providers"]
    scaleway = providers["scaleway"]["instances"]
    aws = providers["aws"]["instances"]
    ovh = providers["ovh"]["instances"]

    # Embed full data as JSON in the page so JS can filter/sort on the client
    json_payload = json.dumps(data, separators=(",", ":"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cloud VM Price Tracker – Paris Region</title>
  <meta name="description" content="Daily updated VM pricing dashboard for Scaleway, AWS EC2, and OVHcloud in the Paris (EU) region. Compare hourly and monthly prices across providers." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --bg: #0a0e1a;
      --surface: #111827;
      --surface2: #1a2235;
      --border: #1f2d45;
      --accent: #4f8ef7;
      --accent2: #7c5cfc;
      --gold: #f5c842;
      --text: #e2e8f0;
      --text-dim: #64748b;
      --text-muted: #94a3b8;
      --green: #22c55e;
      --red: #ef4444;
      --scw: #6b4fbb;
      --aws: #ff9900;
      --ovh: #0099da;
      --radius: 12px;
      --shadow: 0 4px 24px rgba(0,0,0,0.4);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.6;
    }}
    /* Header */
    header {{
      background: linear-gradient(135deg, #0d1b33 0%, #0a0e1a 100%);
      border-bottom: 1px solid var(--border);
      padding: 24px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
      position: sticky;
      top: 0;
      z-index: 100;
      backdrop-filter: blur(10px);
    }}
    .header-left h1 {{
      font-size: 1.5rem;
      font-weight: 700;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .header-left p {{
      font-size: 0.8rem;
      color: var(--text-dim);
      margin-top: 2px;
    }}
    .header-right {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 500;
      border: 1px solid;
    }}
    .badge-scw {{ background: rgba(107,79,187,0.15); color: #a78bfa; border-color: rgba(107,79,187,0.3); }}
    .badge-aws {{ background: rgba(255,153,0,0.1); color: var(--aws); border-color: rgba(255,153,0,0.25); }}
    .badge-ovh {{ background: rgba(0,153,218,0.1); color: #38bdf8; border-color: rgba(0,153,218,0.25); }}
    .updated {{
      font-size: 0.75rem;
      color: var(--text-dim);
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
    /* Stats bar */
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
      padding: 20px 32px;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
    }}
    .stat-card {{
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 14px 18px;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .stat-card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow); }}
    .stat-label {{ font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.08em; }}
    .stat-value {{ font-size: 1.5rem; font-weight: 700; margin-top: 4px; }}
    .stat-sub {{ font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }}
    /* Controls */
    .controls {{
      padding: 16px 32px;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .search-wrap {{
      position: relative;
      flex: 1;
      min-width: 200px;
      max-width: 340px;
    }}
    .search-icon {{
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-dim);
      font-size: 0.9rem;
      pointer-events: none;
    }}
    input[type="text"], select {{
      width: 100%;
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 0.85rem;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s;
    }}
    input[type="text"] {{ padding-left: 36px; }}
    input[type="text"]:focus, select:focus {{ border-color: var(--accent); }}
    select {{ cursor: pointer; min-width: 130px; }}
    .filter-group {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }}
    .filter-btn {{
      padding: 6px 14px;
      border-radius: 20px;
      border: 1px solid var(--border);
      background: var(--surface2);
      color: var(--text-muted);
      font-size: 0.8rem;
      font-family: inherit;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .filter-btn.active {{ background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600; }}
    /* Tabs / provider sections */
    .main {{
      padding: 24px 32px;
      max-width: 1600px;
      margin: 0 auto;
    }}
    .tabs {{
      display: flex;
      gap: 4px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      overflow-x: auto;
    }}
    .tab {{
      padding: 10px 20px;
      border-radius: 8px 8px 0 0;
      border: 1px solid transparent;
      background: transparent;
      color: var(--text-dim);
      font-size: 0.875rem;
      font-weight: 500;
      cursor: pointer;
      font-family: inherit;
      white-space: nowrap;
      transition: all 0.2s;
      border-bottom: none;
      position: relative;
      bottom: -1px;
    }}
    .tab:hover {{ color: var(--text); background: var(--surface2); }}
    .tab.active {{ background: var(--surface); border-color: var(--border); color: var(--text); border-bottom-color: var(--surface); }}
    .tab-scw.active {{ color: #a78bfa; }}
    .tab-aws.active {{ color: var(--aws); }}
    .tab-ovh.active {{ color: #38bdf8; }}
    .tab-all.active {{ color: var(--accent); }}
    .section {{ display: none; }}
    .section.visible {{ display: block; }}
    /* Table */
    .table-wrap {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    .table-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 20px;
      border-bottom: 1px solid var(--border);
      background: var(--surface2);
    }}
    .table-title {{ font-size: 0.9rem; font-weight: 600; display: flex; align-items: center; gap: 8px; }}
    .count-badge {{
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 0.72rem;
      padding: 2px 8px;
      border-radius: 12px;
    }}
    .provider-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
    .provider-dot-scw {{ background: var(--scw); box-shadow: 0 0 6px var(--scw); }}
    .provider-dot-aws {{ background: var(--aws); box-shadow: 0 0 6px var(--aws); }}
    .provider-dot-ovh {{ background: var(--ovh); box-shadow: 0 0 6px var(--ovh); }}
    .provider-dot-all {{ background: var(--accent); box-shadow: 0 0 6px var(--accent); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.83rem;
    }}
    thead th {{
      background: var(--surface2);
      color: var(--text-dim);
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: 10px 16px;
      text-align: left;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
      transition: color 0.2s;
    }}
    thead th:hover {{ color: var(--accent); }}
    thead th .sort-icon {{ margin-left: 4px; opacity: 0.4; }}
    thead th.sorted {{ color: var(--accent); }}
    thead th.sorted .sort-icon {{ opacity: 1; }}
    tbody tr {{
      border-bottom: 1px solid rgba(31,45,69,0.6);
      transition: background 0.15s;
    }}
    tbody tr:last-child {{ border-bottom: none; }}
    tbody tr:hover {{ background: var(--surface2); }}
    td {{
      padding: 11px 16px;
      vertical-align: middle;
    }}
    .instance-name {{
      font-weight: 600;
      font-size: 0.85rem;
      color: var(--text);
      font-family: 'Courier New', monospace;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 0.7rem;
      font-weight: 500;
    }}
    .chip-gpu {{ background: rgba(245,200,66,0.12); color: var(--gold); border: 1px solid rgba(245,200,66,0.25); }}
    .chip-arm {{ background: rgba(34,197,94,0.1); color: var(--green); border: 1px solid rgba(34,197,94,0.2); }}
    .chip-eos {{ background: rgba(239,68,68,0.1); color: var(--red); border: 1px solid rgba(239,68,68,0.2); }}
    .chip-prov {{
      font-size: 0.68rem;
      padding: 2px 7px;
    }}
    .chip-prov-scw {{ background: rgba(107,79,187,0.15); color: #a78bfa; border: 1px solid rgba(107,79,187,0.25); }}
    .chip-prov-aws {{ background: rgba(255,153,0,0.1); color: var(--aws); border: 1px solid rgba(255,153,0,0.2); }}
    .chip-prov-ovh {{ background: rgba(0,153,218,0.1); color: #38bdf8; border: 1px solid rgba(0,153,218,0.2); }}
    .price {{ font-weight: 600; font-size: 0.9rem; }}
    .price-sub {{ font-size: 0.75rem; color: var(--text-muted); }}
    .price-best {{ color: var(--green); }}
    .bar-wrap {{ display: flex; align-items: center; gap: 8px; min-width: 100px; }}
    .bar {{ height: 5px; border-radius: 3px; background: var(--accent); opacity: 0.7; transition: width 0.4s; min-width: 2px; }}
    .bar-aws {{ background: var(--aws); }}
    .bar-scw {{ background: var(--scw); }}
    .bar-ovh {{ background: var(--ovh); }}
    .bar-all {{ background: var(--accent); }}
    .no-results {{
      padding: 60px 20px;
      text-align: center;
      color: var(--text-dim);
    }}
    .no-results .icon {{ font-size: 2.5rem; margin-bottom: 12px; }}
    /* Footer */
    footer {{
      text-align: center;
      padding: 24px 32px;
      color: var(--text-dim);
      font-size: 0.78rem;
      border-top: 1px solid var(--border);
      margin-top: 40px;
    }}
    footer a {{ color: var(--accent); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}
    /* Responsive */
    @media (max-width: 768px) {{
      header, .stats-bar, .controls, .main {{ padding-left: 16px; padding-right: 16px; }}
      .stats-bar {{ grid-template-columns: repeat(2, 1fr); }}
      table {{ font-size: 0.78rem; }}
      td, thead th {{ padding: 8px 10px; }}
      .bar-wrap {{ min-width: 60px; }}
      .header-left h1 {{ font-size: 1.2rem; }}
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
    <span class="updated">
      <span class="dot"></span>
      Updated: <span id="updated-at">—</span>
    </span>
  </div>
</header>

<div class="stats-bar">
  <div class="stat-card">
    <div class="stat-label">Total Instances</div>
    <div class="stat-value" id="stat-total" style="color: var(--accent);">—</div>
    <div class="stat-sub">across 3 providers</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Cheapest VM</div>
    <div class="stat-value" id="stat-cheapest" style="color: var(--green); font-size: 1.1rem;">—</div>
    <div class="stat-sub" id="stat-cheapest-name">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Scaleway Min</div>
    <div class="stat-value" id="stat-scw" style="color: #a78bfa; font-size: 1.1rem;">—</div>
    <div class="stat-sub" id="stat-scw-name">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">AWS EC2 Min</div>
    <div class="stat-value" id="stat-aws" style="color: var(--aws); font-size: 1.1rem;">—</div>
    <div class="stat-sub" id="stat-aws-name">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">OVHcloud Min</div>
    <div class="stat-value" id="stat-ovh" style="color: #38bdf8; font-size: 1.1rem;">—</div>
    <div class="stat-sub" id="stat-ovh-name">—</div>
  </div>
</div>

<div class="controls">
  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input type="text" id="search" placeholder="Search instance (e.g. t3.medium, GP1-S…)" />
  </div>
  <select id="sort-by">
    <option value="price_asc">Price: Low → High</option>
    <option value="price_desc">Price: High → Low</option>
    <option value="vcpu_asc">vCPU: Low → High</option>
    <option value="vcpu_desc">vCPU: High → Low</option>
    <option value="ram_asc">RAM: Low → High</option>
    <option value="ram_desc">RAM: High → Low</option>
    <option value="name_asc">Name: A → Z</option>
  </select>
  <div class="filter-group">
    <button class="filter-btn active" id="btn-all-arch" onclick="setArch('all', this)">All CPU</button>
    <button class="filter-btn" onclick="setArch('x86_64', this)">x86</button>
    <button class="filter-btn" onclick="setArch('arm64', this)">ARM</button>
    <button class="filter-btn" onclick="setArch('gpu', this)">GPU</button>
  </div>
</div>

<div class="main">
  <div class="tabs">
    <button class="tab tab-all active" onclick="switchTab('all', this)">🌐 All Providers</button>
    <button class="tab tab-scw" onclick="switchTab('scaleway', this)">🟣 Scaleway</button>
    <button class="tab tab-aws" onclick="switchTab('aws', this)">🟠 AWS EC2</button>
    <button class="tab tab-ovh" onclick="switchTab('ovh', this)">🔵 OVHcloud</button>
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
  Data sourced from public APIs: <a href="https://www.scaleway.com/en/pricing/" target="_blank">Scaleway</a> ·
  <a href="https://aws.amazon.com/ec2/pricing/on-demand/" target="_blank">AWS EC2</a> ·
  <a href="https://www.ovhcloud.com/en-gb/public-cloud/prices/" target="_blank">OVHcloud</a>
  · Updated daily via GitHub Actions · All prices exclude VAT · USD/EUR as returned by each provider's API
</footer>

<script>
const RAW = {json_payload};

let currentTab = 'all';
let currentArch = 'all';
let currentSearch = '';
let currentSort = 'price_asc';
let sortDir = {{ col: 'price', dir: 1 }};

// Normalise all instances into flat list with provider tag
function flatten(data) {{
  const all = [];
  for (const [pKey, pData] of Object.entries(data.providers)) {{
    for (const inst of pData.instances) {{
      all.push({{ ...inst, provider: pKey, provider_name: pData.name }});
    }}
  }}
  return all;
}}

const ALL_INSTANCES = flatten(RAW);

function getPrice(inst) {{
  if (inst.hourly_usd != null) return inst.hourly_usd;
  if (inst.hourly_eur != null) return inst.hourly_eur;
  return 0;
}}

function formatHourly(inst) {{
  if (inst.hourly_usd != null) return '$' + inst.hourly_usd.toFixed(4) + '/hr';
  if (inst.hourly_eur != null) return '€' + inst.hourly_eur.toFixed(4) + '/hr';
  return '—';
}}

function formatMonthly(inst) {{
  if (inst.monthly_usd != null) return '$' + inst.monthly_usd.toFixed(2) + '/mo';
  if (inst.monthly_eur != null) return '€' + inst.monthly_eur.toFixed(2) + '/mo';
  return '—';
}}

function filter(list) {{
  return list.filter(inst => {{
    // search
    if (currentSearch) {{
      const q = currentSearch.toLowerCase();
      if (!inst.name.toLowerCase().includes(q)) return false;
    }}
    // arch
    if (currentArch === 'arm64') return inst.arch === 'arm64';
    if (currentArch === 'x86_64') return inst.arch === 'x86_64';
    if (currentArch === 'gpu') return inst.gpu > 0;
    return true;
  }});
}}

function sortList(list) {{
  return [...list].sort((a, b) => {{
    switch (currentSort) {{
      case 'price_asc':  return getPrice(a) - getPrice(b);
      case 'price_desc': return getPrice(b) - getPrice(a);
      case 'vcpu_asc':   return a.vcpu - b.vcpu;
      case 'vcpu_desc':  return b.vcpu - a.vcpu;
      case 'ram_asc':    return a.ram_gb - b.ram_gb;
      case 'ram_desc':   return b.ram_gb - a.ram_gb;
      case 'name_asc':   return a.name.localeCompare(b.name);
      default: return 0;
    }}
  }});
}}

function maxPrice(list) {{
  return Math.max(...list.map(getPrice), 0.0001);
}}

function providerClass(provider) {{
  return {{ scaleway: 'scw', aws: 'aws', ovh: 'ovh' }}[provider] || 'all';
}}

function renderTable(list, containerId, showProvider = false) {{
  const container = document.getElementById(containerId);
  if (!list.length) {{
    container.innerHTML = `<div class="no-results"><div class="icon">🔍</div><p>No instances match your filters.</p></div>`;
    return;
  }}
  const maxP = maxPrice(list);
  let rows = list.map(inst => {{
    const pct = Math.max(3, Math.round((getPrice(inst) / maxP) * 100));
    const pc = providerClass(inst.provider);
    const chips = [];
    if (inst.arch === 'arm64') chips.push(`<span class="chip chip-arm">ARM</span>`);
    if (inst.gpu > 0) chips.push(`<span class="chip chip-gpu">GPU ×${{inst.gpu}}</span>`);
    if (inst.end_of_service) chips.push(`<span class="chip chip-eos">EOS</span>`);
    const provChip = showProvider
      ? `<span class="chip chip-prov chip-prov-${{pc}}">${{inst.provider_name}}</span> `
      : '';
    return `<tr>
      <td>${{provChip}}<span class="instance-name">${{inst.name}}</span> ${{chips.join(' ')}}</td>
      <td>${{inst.vcpu}}</td>
      <td>${{inst.ram_gb}} GB</td>
      <td class="price">${{formatHourly(inst)}}</td>
      <td><span class="price price-sub">${{formatMonthly(inst)}}</span></td>
      <td><div class="bar-wrap"><div class="bar bar-${{pc}}" style="width:${{pct}}%"></div></div></td>
    </tr>`;
  }}).join('');

  container.innerHTML = `<table>
    <thead>
      <tr>
        <th>Instance</th>
        <th onclick="setSortCol('vcpu')">vCPU <span class="sort-icon">↕</span></th>
        <th onclick="setSortCol('ram')">RAM <span class="sort-icon">↕</span></th>
        <th onclick="setSortCol('price')">Hourly <span class="sort-icon">↕</span></th>
        <th onclick="setSortCol('price')">Monthly (est.) <span class="sort-icon">↕</span></th>
        <th>Relative Cost</th>
      </tr>
    </thead>
    <tbody>${{rows}}</tbody>
  </table>`;
}}

function setSortCol(col) {{
  if (currentSort.startsWith(col)) {{
    currentSort = currentSort.endsWith('asc') ? col + '_desc' : col + '_asc';
  }} else {{
    currentSort = col + '_asc';
  }}
  document.getElementById('sort-by').value = currentSort;
  renderAll();
}}

function renderAll() {{
  const allFiltered = sortList(filter(ALL_INSTANCES));
  const scwFiltered = sortList(filter(ALL_INSTANCES.filter(i => i.provider === 'scaleway')));
  const awsFiltered = sortList(filter(ALL_INSTANCES.filter(i => i.provider === 'aws')));
  const ovhFiltered = sortList(filter(ALL_INSTANCES.filter(i => i.provider === 'ovh')));

  renderTable(allFiltered, 'all-table-container', true);
  renderTable(scwFiltered, 'scw-table-container', false);
  renderTable(awsFiltered, 'aws-table-container', false);
  renderTable(ovhFiltered, 'ovh-table-container', false);

  document.getElementById('all-count-badge').textContent = allFiltered.length + ' instances';
  document.getElementById('scw-count-badge').textContent = scwFiltered.length + ' instances';
  document.getElementById('aws-count-badge').textContent = awsFiltered.length + ' instances';
  document.getElementById('ovh-count-badge').textContent = ovhFiltered.length + ' instances';
}}

function switchTab(tab, el) {{
  currentTab = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  document.querySelectorAll('.section').forEach(s => s.classList.remove('visible'));
  document.getElementById('section-' + tab).classList.add('visible');
}}

function setArch(arch, el) {{
  currentArch = arch;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  renderAll();
}}

// Init
function init() {{
  // Counts in header
  const scw = RAW.providers.scaleway.instances;
  const aws = RAW.providers.aws.instances;
  const ovh = RAW.providers.ovh.instances;

  document.getElementById('scw-count').textContent = scw.length;
  document.getElementById('aws-count').textContent = aws.length;
  document.getElementById('ovh-count').textContent = ovh.length;
  document.getElementById('stat-total').textContent = ALL_INSTANCES.length;
  document.getElementById('updated-at').textContent = RAW.updated_at.replace('T', ' ').replace('Z', ' UTC');

  // Stats
  const cheapestAll = [...ALL_INSTANCES].sort((a,b) => getPrice(a) - getPrice(b))[0];
  if (cheapestAll) {{
    document.getElementById('stat-cheapest').textContent = formatHourly(cheapestAll);
    document.getElementById('stat-cheapest-name').textContent = cheapestAll.name + ' (' + cheapestAll.provider_name + ')';
  }}
  const cheapestScw = [...scw].sort((a,b) => getPrice(a) - getPrice(b))[0];
  if (cheapestScw) {{
    document.getElementById('stat-scw').textContent = formatHourly(cheapestScw);
    document.getElementById('stat-scw-name').textContent = cheapestScw.name;
  }}
  const cheapestAws = [...aws].sort((a,b) => getPrice(a) - getPrice(b))[0];
  if (cheapestAws) {{
    document.getElementById('stat-aws').textContent = formatHourly(cheapestAws);
    document.getElementById('stat-aws-name').textContent = cheapestAws.name;
  }}
  const cheapestOvh = [...ovh].sort((a,b) => getPrice(a) - getPrice(b))[0];
  if (cheapestOvh) {{
    document.getElementById('stat-ovh').textContent = formatHourly(cheapestOvh);
    document.getElementById('stat-ovh-name').textContent = cheapestOvh.name;
  }}

  // Events
  document.getElementById('search').addEventListener('input', e => {{
    currentSearch = e.target.value.trim();
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
    data = load_data()
    html = build_html(data)
    OUT_FILE.write_text(html, encoding="utf-8")
    scw = len(data["providers"]["scaleway"]["instances"])
    aws = len(data["providers"]["aws"]["instances"])
    ovh = len(data["providers"]["ovh"]["instances"])
    print(f"✓ Built index.html  ({scw} SCW + {aws} AWS + {ovh} OVH = {scw+aws+ovh} total instances)")


if __name__ == "__main__":
    main()
