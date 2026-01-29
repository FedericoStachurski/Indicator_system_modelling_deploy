from __future__ import annotations

from typing import Dict, List
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import your model core (run uvicorn from repo root or set PYTHONPATH=.)
from soil_ode_UI.soil_model_core import LandConfig, simulate_multi_land, SCENARIOS

app = FastAPI(title="Soil Index Dashboard API")
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


# ----------------------------
# API schemas
# ----------------------------
class LandIn(BaseModel):
    name: str
    alpha: float
    S0: float
    scenario_name: str
    deg_params: Dict
    land_fraction: float
    P_max: float


class SimRequest(BaseModel):
    lands: List[LandIn]
    T_max: float = 50.0
    n_points: int = 300

    population_growth_rate: float = 0.02
    income_growth_rate: float = 0.014
    inflation_rate: float = 0.017


# ----------------------------
# API routes
# ----------------------------
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


@app.get("/api/scenarios")
def scenarios():
    return {"scenarios": list(SCENARIOS.keys())}

@app.get("/paper", response_class=HTMLResponse)
def paper():
    return """
    <!doctype html>
    <html>
    <head>
      <title>Food System Model — Paper</title>
      <style>
        html, body { margin:0; height:100%; }
        iframe {
          width:100%;
          height:100%;
          border:none;
        }
      </style>
    </head>
    <body>
      <iframe src="/static/paper/Food_system_model_equations.pdf"></iframe>
    </body>
    </html>
    """



@app.post("/api/simulate")
def simulate(req: SimRequest):
    lands = [LandConfig(**l.model_dump()) for l in req.lands]

    res = simulate_multi_land(
        lands=lands,
        T_max=req.T_max,
        n_points=req.n_points,
        population_growth_rate=req.population_growth_rate,
        income_growth_rate=req.income_growth_rate,
        inflation_rate=req.inflation_rate,
    )

    return {
        "t": res.t.tolist(),
        "weighted_soil": res.weighted_soil.tolist(),
        "soils": res.soils.tolist(),
        "land_names": res.land_names,
        "total_production": res.total_production.tolist(),
        "population": res.population.tolist(),
        "self_sufficiency_ratio": res.self_sufficiency_ratio.tolist(),
        "average_real_income": res.average_real_income.tolist(),
        "affordability_index": res.affordability_index.tolist(),
        "production_by_land": (res.productions * 560_000).tolist(),  # scale back to tonnes
        "population": res.population.tolist(),
        "self_sufficiency_ratio": res.self_sufficiency_ratio.tolist(),
        "average_real_income": res.average_real_income.tolist(),
        "affordability_index": res.affordability_index.tolist(),
    }


# ----------------------------
# Single-page dashboard
# ----------------------------
HTML_PAGE = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Soil Health & Food Affordability</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>

  <style>
    html, body { height: 100%; margin: 0; overflow: hidden; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }

    :root{
  --base-font: 15px;   /* try 14–16px */
  --small-font: 13px;
    }

    body{
    font-size: var(--base-font);
    }

    .header .title{
    font-size: 15px;
    }

    .control h4{
    font-size: 14px;
    }

    .labelrow{
    font-size: 23px;
    }

    .btn{
    font-size: 33px;
    }

    .app{
      height: 100vh;
      display: grid;
      grid-template-rows: 44px 1fr;
      background: linear-gradient(to top, #bdecb6 0%, #ffffff 70%);
    }

    .header{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px 10px;
      border-bottom: 1px solid rgba(0,0,0,0.12);
      background: rgba(255,255,255,0.7);
      backdrop-filter: blur(6px);
    }

    .header .title{ font-weight: 700; font-size: 13px; }

    .btn{
      background: #222;
      color: #fff;
      border: 1px solid #000;
      border-radius: 10px;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 12px;
    }

    /* plots area (compact tiles) */
    .plots{
    height: 100%;
    display: grid;
    grid-template-columns: repeat(3, 1fr);

    /* FIXED tile height instead of stretching */
    grid-auto-rows: 340px;          /* try 120px or 110px */
    align-content: start;           /* tiles start at top */

    gap: 6px;
    padding: 8px;
    }

    .card{
      height: 100%;
      border: 1px solid rgba(0,0,0,0.14);
      border-radius: 10px;
      background: rgba(255,255,255,0.65);
      box-shadow: 0 1px 6px rgba(0,0,0,0.05);
      padding: 2px;
    }
    .plot{ width: 100%; height: 100%; min-height: 0; }

    /* modal overlay + panel */
    .modal-overlay{
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.35);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 999;
    }
    .modal-overlay.open{ display: flex; }

    .modal{
      width: min(980px, 94vw);
      max-height: 86vh;
      overflow: auto;         /* scroll inside modal only */
      background: rgba(255,255,255,0.92);
      border: 1px solid rgba(0,0,0,0.18);
      border-radius: 14px;
      box-shadow: 0 10px 35px rgba(0,0,0,0.25);
      padding: 12px;
    }

    .modal-header{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .modal-title{ font-weight: 800; font-size: 14px; }

    .grid-controls{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .control{
      border: 1px solid rgba(0,0,0,0.10);
      border-radius: 12px;
      padding: 10px;
      background: rgba(255,255,255,0.75);
      display: grid;
      gap: 8px;
    }

    .control h4{ margin: 0; font-size: 13px; }

    .row{ display: grid; gap: 4px; }
    .labelrow{ display: flex; justify-content: space-between; font-size: 12px; }
    input[type="range"]{ width: 100%; }
    input[type="text"]{ width: 100%; padding: 6px 8px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.18); }
    .small{ font-size: 12px; color: #333; }
  </style>
</head>

<body>
  <div class="app">
    <div class="header">
      <div class="title">Soil Health & Food Affordability — Dashboard</div>
      <button class="btn" id="openControls">Controls </button>
      <button class="btn" onclick="window.open('/paper')">Paper </button>

    </div>

    <div class="plots">
      <div class="card"><div id="plotSoil" class="plot"></div></div>
      <div class="card"><div id="plotProd" class="plot"></div></div>
      <div class="card"><div id="plotPop" class="plot"></div></div>
      <div class="card"><div id="plotSSR" class="plot"></div></div>
      <div class="card"><div id="plotInc" class="plot"></div></div>
      <div class="card"><div id="plotAff" class="plot"></div></div>
    </div>
  </div>

  <!-- Modal overlay -->
  <div class="modal-overlay" id="overlay">
    <div class="modal" id="modal">
      <div class="modal-header">
        <div class="modal-title">Simulation controls</div>
        <button class="btn" id="closeControls">Close ✖</button>
      </div>

      <div class="grid-controls">
        <!-- Global -->
        <div class="control">
          <h4>Global</h4>

          <div class="row">
            <div class="labelrow"><span><b>T_max</b></span><span id="tmaxLabel" class="small"></span></div>
            <input id="tmax" type="range" min="10" max="250" step="10" value="50">
          </div>

          <div class="row">
            <div class="labelrow"><span><b>Pop growth</b></span><span id="popLabel" class="small"></span></div>
            <input id="pop" type="range" min="0" max="0.1" step="0.005" value="0.02">
          </div>

          <div class="row">
            <div class="labelrow"><span><b>n_points</b></span><span id="nLabel" class="small"></span></div>
            <input id="n" type="range" min="120" max="600" step="30" value="300">
          </div>
        </div>

        <!-- Lands header + buttons (full width) -->
        <div class="control" style="grid-column: 1 / -1;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0;">Lands</h4>
            <div style="display:flex; gap:6px;">
              <button class="btn" id="addLandBtn" type="button">+ Add land</button>
              <button class="btn" id="removeLandBtn" type="button">- Remove last</button>
            </div>
          </div>

          <div id="landsContainer" class="grid-controls" style="grid-template-columns: 1fr 1fr; margin-top:8px;"></div>
          <div class="small">Each land uses “Constant degradation D” for now (D_const per land).</div>
        </div>
      </div>
    </div>
  </div>

<script>
const el = (id) => document.getElementById(id);

// Modal open/close
const overlay = el("overlay");
el("openControls").addEventListener("click", () => overlay.classList.add("open"));
el("closeControls").addEventListener("click", () => overlay.classList.remove("open"));
overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.classList.remove("open"); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") overlay.classList.remove("open"); });

// ------- Land state (dynamic) -------
let landsState = [
  { name: "Land 1", share: 50, alpha: 0.20, s0: 0.80, pmax: 10.0, dconst: 0.10 },
];

function renderLands() {
  const container = el("landsContainer");
  container.innerHTML = "";

  landsState.forEach((land, i) => {
    const card = document.createElement("div");
    card.className = "control";
    card.style.padding = "10px";

    card.innerHTML = `
      <h4>${land.name}</h4>

      <div class="row">
        <div class="labelrow"><span>Name</span><span class="small"></span></div>
        <input id="landName_${i}" type="text" value="${land.name}" />
      </div>

      <div class="row">
        <div class="labelrow"><span>Share (%)</span><span id="shareLabel_${i}" class="small"></span></div>
        <input id="share_${i}" type="range" min="0" max="100" step="1" value="${land.share}">
      </div>

      <div class="row">
        <div class="labelrow"><span>α (recovery)</span><span id="alphaLabel_${i}" class="small"></span></div>
        <input id="alpha_${i}" type="range" min="0" max="1" step="0.01" value="${land.alpha}">
      </div>

      <div class="row">
        <div class="labelrow"><span>S₀</span><span id="s0Label_${i}" class="small"></span></div>
        <input id="s0_${i}" type="range" min="0" max="1" step="0.01" value="${land.s0}">
      </div>

      <div class="row">
        <div class="labelrow"><span>P_max</span><span id="pmaxLabel_${i}" class="small"></span></div>
        <input id="pmax_${i}" type="range" min="0" max="40" step="0.5" value="${land.pmax}">
      </div>

      <div class="row">
        <div class="labelrow"><span>D_const</span><span id="dLabel_${i}" class="small"></span></div>
        <input id="d_${i}" type="range" min="0" max="1" step="0.01" value="${land.dconst}">
      </div>
    `;

    container.appendChild(card);

    const nameInp  = el(`landName_${i}`);
    const shareInp = el(`share_${i}`);
    const alphaInp = el(`alpha_${i}`);
    const s0Inp    = el(`s0_${i}`);
    const pmaxInp  = el(`pmax_${i}`);
    const dInp     = el(`d_${i}`);

    const updateFromUI = () => {
      landsState[i].name   = nameInp.value || `Land ${i+1}`;
      landsState[i].share  = +shareInp.value;
      landsState[i].alpha  = +alphaInp.value;
      landsState[i].s0     = +s0Inp.value;
      landsState[i].pmax   = +pmaxInp.value;
      landsState[i].dconst = +dInp.value;

      // Update title
      card.querySelector("h4").textContent = landsState[i].name;

      setLandLabels(i);
      triggerSim();
    };

    [nameInp, shareInp, alphaInp, s0Inp, pmaxInp, dInp].forEach(inp => {
      inp.addEventListener("input", updateFromUI);
    });

    setLandLabels(i);
  });
}

function setLandLabels(i){
  el(`shareLabel_${i}`).textContent = `${landsState[i].share}%`;
  el(`alphaLabel_${i}`).textContent = landsState[i].alpha.toFixed(2);
  el(`s0Label_${i}`).textContent = landsState[i].s0.toFixed(2);
  el(`pmaxLabel_${i}`).textContent = landsState[i].pmax.toFixed(1);
  el(`dLabel_${i}`).textContent = landsState[i].dconst.toFixed(2);
}

// ------- Global labels -------
function setGlobalLabels() {
  el("tmaxLabel").textContent = el("tmax").value + " yrs";
  el("popLabel").textContent  = (+el("pop").value).toFixed(3);
  el("nLabel").textContent    = el("n").value;
}

// ------- Add/remove buttons -------
el("addLandBtn").addEventListener("click", () => {
  if (landsState.length >= 10) return;

  landsState.push({
    name: `Land ${landsState.length + 1}`,
    share: Math.round(100 / (landsState.length + 1)),
    alpha: 0.20,
    s0: 0.80,
    pmax: 10.0,
    dconst: landsState[0]?.dconst ?? 0.10
  });

  // rough re-balance to sum ~ 100
  const each = Math.floor(100 / landsState.length);
  const remainder = 100 - each * (landsState.length - 1);
  landsState = landsState.map((l, idx) => ({...l, share: idx === landsState.length-1 ? remainder : each}));

  renderLands();
  triggerSim();
});

el("removeLandBtn").addEventListener("click", () => {
  if (landsState.length <= 1) return;
  landsState.pop();
  renderLands();
  triggerSim();
});

// ------- Simulation + plots -------
async function runSim() {
  setGlobalLabels();

  const sumShares = Math.max(landsState.reduce((a,l)=>a+l.share,0), 1e-9);

  const payload = {
    T_max: +el("tmax").value,
    n_points: +el("n").value,
    population_growth_rate: +el("pop").value,
    lands: landsState.map((l) => ({
      name: l.name,
      alpha: l.alpha,
      S0: l.s0,
      scenario_name: "Constant degradation D",
      deg_params: { "D_const": l.dconst },
      land_fraction: l.share / sumShares,
      P_max: l.pmax
    }))
  };

  const resp = await fetch("/api/simulate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });

  const data = await resp.json();
  const t = data.t;

  const commonLayout = (title, ytitle) => ({
    title: {text: title, font: {size: 15}},
    margin: {l: 58, r: 6, t: 28, b: 20},
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    xaxis: {tickfont: {size: 11}},
    yaxis: {title: {text: ytitle, font: {size: 19}}, tickfont: {size: 11}},
    legend: {font: {size: 18}, orientation: "h", y: -0.25}
  });

  // Soil plot: one line per land + weighted
  const soilTraces = [];

  // Production plot: one line per land + total
  const prodTraces = [];

  for (let i = 0; i < data.land_names.length; i++) {
    soilTraces.push({
      x: t,
      y: data.soils[i],
      type: "scatter",
      name: data.land_names[i],
      line: {width: 5}
    });
  }
  soilTraces.push({
    x: t,
    y: data.weighted_soil,
    type: "scatter",
    name: "Weighted",
    line: {width: 5, dash: "dash"}
  });

  

  // per-land production lines
  for (let i = 0; i < data.land_names.length; i++) {
prodTraces.push({
    x: t,
    y: data.production_by_land[i],
    type: "scatter",
    name: data.land_names[i],
    line: { width: 5  },
    showlegend: false   //
});
}

  // total production line
prodTraces.push({
x: t,
y: data.total_production,
type: "scatter",
name: "Total",
line: { width: 5, dash: "dash" },
showlegend: false
});

Plotly.react(
"plotProd",
prodTraces,
{
    ...commonLayout("Production", "Tonnes"),
    showlegend: false
},
{ displayModeBar: false }
);

  Plotly.react("plotSoil", soilTraces, commonLayout("Soil", "Index"), {displayModeBar: false});


  Plotly.react("plotPop",
    [{x: t, y: data.population, type: "scatter", name: "Population"}],
    commonLayout("Population", "People"),
    {displayModeBar: false}
  );

  Plotly.react("plotSSR",
    [{x: t, y: data.self_sufficiency_ratio, type: "scatter", name: "SSR"}],
    commonLayout("Self-sufficiency", "%"),
    {displayModeBar: false}
  );

  Plotly.react("plotInc",
    [{x: t, y: data.average_real_income, type: "scatter", name: "Real income"}],
    commonLayout("Real income", "£ (real)"),
    {displayModeBar: false}
  );

  Plotly.react("plotAff",
    [{x: t, y: data.affordability_index, type: "scatter", name: "Affordability"}],
    commonLayout("Affordability", "Index"),
    {displayModeBar: false}
  );
}

// Debounce
let timer = null;
function triggerSim(){
  clearTimeout(timer);
  timer = setTimeout(runSim, 140);
}

// Global sliders -> sim
["tmax","pop","n"].forEach((id) => {
  el(id).addEventListener("input", () => triggerSim());
});

// Init
renderLands();
runSim();
</script>

</body>
</html>
"""
