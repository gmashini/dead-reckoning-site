/**
 * March Madness 2026 — Main JS
 * Reads bracket_data.json and renders full SPA.
 */

// ── GLOBAL STATE ─────────────────────────────────────────────
let DATA = null;
let TEAMS_ARR = [];  // [{name, ...team_data}, ...]
let SORT_STATE = { odds: { key: "model_champion_prob", dir: -1 }, stats: { key: "win_pct", dir: -1 } };
let ACTIVE_ROUND = "Champion";

const REGION_COLORS = { East: "#003399", West: "#8B1A1A", South: "#1a6b1a", Midwest: "#7a3a00" };

// ── INIT ─────────────────────────────────────────────────────
async function init() {
  try {
    const resp = await fetch("bracket_data.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    DATA = await resp.json();
    TEAMS_ARR = Object.entries(DATA.teams || {}).map(([name, d]) => ({ name, ...d }));
    renderAll();
  } catch (e) {
    document.body.innerHTML = `
      <div style="padding:80px;text-align:center;font-family:monospace;color:#666">
        <div style="font-size:48px;margin-bottom:16px">&#9634;</div>
        <div style="font-size:18px;font-weight:800;margin-bottom:8px">DATA NOT FOUND</div>
        <div style="font-size:13px;color:#999;margin-bottom:20px">bracket_data.json missing — run the build script first</div>
        <pre style="background:#111;color:#4af;padding:16px;font-size:12px;display:inline-block">python scripts/build.py --full</pre>
      </div>`;
  }
}

function renderAll() {
  renderHero();
  renderBracketTree();
  renderContenders();
  renderOddsTable();
  renderMonteCarlo();
  renderUpsets();
  bindEvents();
}

// ── BRACKET TREE ─────────────────────────────────────────────
function renderBracketTree() {
  const pb = DATA.predicted_bracket;
  const container = id("bracket-tree-container");
  if (!pb || !container) return;

  const regions = pb.regions;
  const ROUNDS_L = ["R64", "R32", "S16", "E8"];   // left half: left → right
  const ROUNDS_R = ["R64", "R32", "S16", "E8"];   // DOM order reversed by bk-cols-rtl → visual E8 near center, R64 far right

  function teamHtml(name, seed, isWinner) {
    const cls = isWinner ? "bk-team bk-winner" : "bk-team bk-loser";
    const pickCls = isWinner ? "bk-pick-icon bk-picked" : "bk-pick-icon bk-unpicked";
    return `<div class="${cls}" onclick="openTeamModal('${esc(name)}')">
      <span class="bk-seed">${seed}</span>
      <span class="bk-name">${esc(name)}</span>
      <span class="${pickCls}">${isWinner ? "✓" : ""}</span>
    </div>`;
  }

  function gameHtml(g) {
    return `<div class="bk-game">
      ${teamHtml(g.t1, g.s1, g.t1 === g.winner)}
      <div class="bk-divider"></div>
      ${teamHtml(g.t2, g.s2, g.t2 === g.winner)}
      <div class="bk-info-icon">i</div>
    </div>`;
  }

  function regionCols(regionData, roundOrder) {
    return roundOrder.map(rnd => {
      const games = regionData.rounds[rnd] || [];
      return `<div class="bk-col" data-round="${rnd}">${games.map(gameHtml).join("")}</div>`;
    }).join("");
  }

  function f4Html(g, side) {
    return `<div class="bk-f4-col bk-f4-${side}">
      <div class="bk-f4-inner">
        <div class="bk-f4-label">Final Four</div>
        <div class="bk-game">
          ${teamHtml(g.t1, g.s1, g.t1 === g.winner)}
          <div class="bk-divider"></div>
          ${teamHtml(g.t2, g.s2, g.t2 === g.winner)}
          <div class="bk-info-icon">i</div>
        </div>
      </div>
    </div>`;
  }

  function ncgHtml(g) {
    const td = DATA.teams[g.winner] || {};
    const color = REGION_COLORS[td.region] || "#003399";
    const logoLetter = g.winner ? g.winner[0].toUpperCase() : "?";
    const t1Win = g.t1 === g.winner;
    const t2Win = g.t2 === g.winner;

    return `<div class="bk-ncg-col">
      <div class="bk-ncg-inner">

        <div class="bk-champ-box">
          <div class="bk-champ-header">
            <div class="bk-champ-title">Championship Game</div>
            <div class="bk-champ-date">Mon 4/6, 8:30PM ET</div>
          </div>

          <div class="bk-champ-matchup">
            <div class="bk-champ-team bk-champ-left" onclick="openTeamModal('${esc(g.t1)}')">
              <span class="bk-champ-pick-icon ${t1Win ? 'bk-picked' : 'bk-unpicked'}">${t1Win ? '✓' : ''}</span>
              <span class="bk-champ-team-seed">${g.s1}</span>
              <span class="bk-champ-team-name">${esc(g.t1)}</span>
            </div>
            <div class="bk-champ-team bk-champ-right" onclick="openTeamModal('${esc(g.t2)}')">
              <span class="bk-champ-team-name">${esc(g.t2)}</span>
              <span class="bk-champ-team-seed">${g.s2}</span>
              <span class="bk-champ-pick-icon ${t2Win ? 'bk-picked' : 'bk-unpicked'}">${t2Win ? '✓' : ''}</span>
            </div>
          </div>

          <div class="bk-tiebreaker">
            <div class="bk-tb-label">Tiebreaker: Total Combined Final Score</div>
            <input type="number" class="bk-tb-input" value="115" id="tiebreaker-input">
          </div>
        </div>

        <div class="bk-bracket-buttons">
          <button class="bk-btn-clear">Clear Picks</button>
          <button class="bk-btn-save" disabled>Save Picks</button>
        </div>

        <div class="bk-champion-section">
          <div class="bk-champion-label">Champion</div>
          <div class="bk-champion-team" onclick="openTeamModal('${esc(g.winner)}')">
            <div class="bk-champion-logo" style="background:${color}">${logoLetter}</div>
            <div class="bk-champion-name">${g.w_seed} ${esc(g.winner)}</div>
          </div>
        </div>

      </div>
    </div>`;
  }

  container.innerHTML = `<div class="bk-scroll"><div class="bk-full">
    <div class="bk-half bk-half-left">
      <div class="bk-region-row">
        <div class="bk-region-lbl" style="border-color:${REGION_COLORS.East}">EAST</div>
        <div class="bk-region-cols">${regionCols(regions.East, ROUNDS_L)}</div>
      </div>
      <div class="bk-region-separator"></div>
      <div class="bk-region-row">
        <div class="bk-region-lbl" style="border-color:${REGION_COLORS.South}">SOUTH</div>
        <div class="bk-region-cols">${regionCols(regions.South, ROUNDS_L)}</div>
      </div>
    </div>
    ${f4Html(pb.f4_left, "left")}
    ${ncgHtml(pb.ncg)}
    ${f4Html(pb.f4_right, "right")}
    <div class="bk-half bk-half-right">
      <div class="bk-region-row">
        <div class="bk-region-lbl" style="border-color:${REGION_COLORS.West}">WEST</div>
        <div class="bk-region-cols bk-cols-rtl">${regionCols(regions.West, ROUNDS_R)}</div>
      </div>
      <div class="bk-region-separator"></div>
      <div class="bk-region-row">
        <div class="bk-region-lbl" style="border-color:${REGION_COLORS.Midwest}">MIDWEST</div>
        <div class="bk-region-cols bk-cols-rtl">${regionCols(regions.Midwest, ROUNDS_R)}</div>
      </div>
    </div>
  </div></div>`;
}

// ── HERO ─────────────────────────────────────────────────────
function renderHero() {
  const mi = DATA.model_info || {};
  const updated = DATA.updated ? new Date(DATA.updated).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit"
  }) : "—";
  const el = id("hero-updated");
  if (el) el.textContent = `UPDATED ${updated.toUpperCase()}`;
  setVal("stat-accuracy", mi.accuracy ? `${(mi.accuracy * 100).toFixed(1)}%` : "—");
  setVal("stat-games", mi.training_samples ? mi.training_samples.toLocaleString() : "—");
  setVal("stat-teams", TEAMS_ARR.length.toString());
}

// ── TOP CONTENDERS ───────────────────────────────────────────
function renderContenders() {
  const container = id("contenders-grid");
  if (!container) return;

  const top = TEAMS_ARR.slice().sort((a, b) => (b.model_champion_prob || 0) - (a.model_champion_prob || 0)).slice(0, 12);
  container.innerHTML = top.map(t => contenderCard(t)).join("");
}

function contenderCard(t) {
  const edge = t.model_edge;
  const edgeClass = edge === null ? "edge-neu" : edge > 0.005 ? "edge-pos" : edge < -0.005 ? "edge-neg" : "edge-neu";
  const edgeStr = edge === null ? "—" : `${edge > 0 ? "+" : ""}${(edge * 100).toFixed(1)}%`;
  const color = REGION_COLORS[t.region] || "#003399";
  const modelPct = t.model_champion_prob || 0;
  const marketPct = t.odds_champion_prob;

  return `<div class="contender-card" style="--region-color:${color}" onclick="openTeamModal('${esc(t.name)}')">
    <div class="contender-seed">SEED ${t.seed} · ${t.region?.toUpperCase()}</div>
    <div class="contender-name">${esc(t.name)}</div>
    <div class="prob-bar-track"><div class="prob-bar-fill" style="width:${Math.min(modelPct*300, 100)}%"></div></div>
    <div class="contender-probs" style="margin-top:12px">
      <div class="contender-prob-row">
        <span class="contender-prob-label">MODEL</span>
        <span class="contender-prob-val model">${fmtPct(modelPct)}</span>
      </div>
      <div class="contender-prob-row">
        <span class="contender-prob-label">MARKET</span>
        <span class="contender-prob-val market">${marketPct != null ? fmtPct(marketPct) : "N/A"}</span>
      </div>
    </div>
    <div class="contender-edge ${edgeClass}">EDGE: ${edgeStr}</div>
  </div>`;
}

// ── MODEL vs ODDS TABLE ──────────────────────────────────────
function renderOddsTable(sortKey, sortDir) {
  if (sortKey) {
    if (SORT_STATE.odds.key === sortKey) {
      SORT_STATE.odds.dir *= -1;
    } else {
      SORT_STATE.odds.key = sortKey;
      SORT_STATE.odds.dir = -1;
    }
  }
  const { key, dir } = SORT_STATE.odds;

  const search = (id("odds-search")?.value || "").toLowerCase();
  const region = id("odds-region")?.value || "";

  let rows = TEAMS_ARR.filter(t =>
    (!search || t.name.toLowerCase().includes(search)) &&
    (!region || t.region === region)
  );

  rows.sort((a, b) => {
    let va = getVal(a, key), vb = getVal(b, key);
    return dir * (va < vb ? -1 : va > vb ? 1 : 0);
  });

  const tbody = id("odds-tbody");
  if (!tbody) return;
  tbody.innerHTML = rows.map(t => {
    const edge = t.model_edge;
    const edgeClass = edge === null ? "" : edge > 0.005 ? "edge-pos" : edge < -0.005 ? "edge-neg" : "";
    const edgeStr = edge === null ? "—" : `${edge > 0 ? "+" : ""}${(edge * 100).toFixed(1)}%`;
    const stats = t.stats || {};
    const regionColor = REGION_COLORS[t.region] || "#333";
    return `<tr onclick="openTeamModal('${esc(t.name)}')">
      <td class="team-cell">${esc(t.name)}</td>
      <td><span class="seed-badge">${t.seed}</span></td>
      <td><span class="region-tag" style="background:${regionColor}">${t.region || "—"}</span></td>
      <td><strong>${fmtPct(t.model_champion_prob || 0)}</strong></td>
      <td>${t.odds_champion_prob != null ? fmtPct(t.odds_champion_prob) : "N/A"}</td>
      <td class="${edgeClass}">${edgeStr}</td>
      <td>${fmtNum(stats.win_pct, 3)}</td>
      <td>${fmtNum(stats.ppg, 1)}</td>
    </tr>`;
  }).join("");

  // Update sort indicators on headers
  document.querySelectorAll("#odds-table thead th").forEach(th => {
    th.classList.remove("sort-active", "sort-asc", "sort-desc");
    if (th.dataset.sort === key) {
      th.classList.add("sort-active", dir === -1 ? "sort-desc" : "sort-asc");
    }
  });
}

// ── MONTE CARLO ──────────────────────────────────────────────
function renderMonteCarlo(round) {
  if (round) ACTIVE_ROUND = round;

  // Update button states
  document.querySelectorAll(".round-btn").forEach(btn => {
    btn.classList.toggle("round-btn-active", btn.dataset.round === ACTIVE_ROUND);
  });

  const grid = id("mc-grid");
  if (!grid) return;

  const sorted = TEAMS_ARR.slice().sort((a, b) => {
    const pa = a.monte_carlo?.[ACTIVE_ROUND] || 0;
    const pb = b.monte_carlo?.[ACTIVE_ROUND] || 0;
    return pb - pa;
  });

  const maxPct = sorted[0]?.monte_carlo?.[ACTIVE_ROUND] || 0.01;

  grid.innerHTML = sorted.map((t, i) => {
    const pct = t.monte_carlo?.[ACTIVE_ROUND] || 0;
    if (pct < 0.001) return "";  // Skip near-zero
    const barW = (pct / maxPct * 100).toFixed(1);
    const regionColor = REGION_COLORS[t.region] || "#2563eb";
    const marketPct = ACTIVE_ROUND === "Champion" ? t.odds_champion_prob : null;
    return `<div class="mc-bar-row" onclick="openTeamModal('${esc(t.name)}')">
      <div class="mc-bar-rank">${i + 1}</div>
      <div class="mc-bar-name">${esc(t.name)}<span class="mc-bar-seed">#${t.seed}</span></div>
      <div class="mc-bar-track">
        <div class="mc-bar-fill" style="width:${barW}%;background:${regionColor}"></div>
      </div>
      <div class="mc-bar-pct">${fmtPct(pct)}</div>
      <div class="mc-bar-market">${marketPct != null ? fmtPct(marketPct) : ""}</div>
    </div>`;
  }).join("");

}

// ── UPSET WATCH ──────────────────────────────────────────────
function renderUpsets() {
  const grid = id("upsets-grid");
  if (!grid) return;

  const alerts = DATA.monte_carlo?.upset_alerts || [];
  if (alerts.length === 0) {
    grid.innerHTML = `<div class="no-upsets">No significant upset alerts detected by model.</div>`;
    return;
  }

  grid.innerHTML = alerts.map(u => {
    return `<div class="upset-card" onclick="openTeamModal('${esc(u.upset_team)}')">
      <div class="upset-header">
        <span class="upset-badge">UPSET ALERT</span>
        <span class="upset-prob">${fmtPct(u.upset_prob)}</span>
      </div>
      <div class="upset-matchup">
        <div>
          <div class="upset-team">${esc(u.upset_team)}</div>
          <div class="upset-seed-tag">SEED ${u.upset_seed}</div>
        </div>
        <div class="upset-vs">OVER</div>
        <div>
          <div class="upset-team">${esc(u.favorite)}</div>
          <div class="upset-seed-tag">SEED ${u.fav_seed}</div>
        </div>
      </div>
      <div class="upset-region">${u.region || ""}</div>
    </div>`;
  }).join("");
}

// ── TEAM MODAL ───────────────────────────────────────────────
function openTeamModal(name) {
  const t = DATA.teams[name];
  if (!t) return;

  id("modal-team-name").textContent = `${name} — SEED ${t.seed} · ${(t.region || "").toUpperCase()}`;
  const s = t.stats || {};
  const mc = t.monte_carlo || {};
  const color = REGION_COLORS[t.region] || "#003399";

  const rounds = ["R64", "R32", "S16", "E8", "F4", "NCG", "Champion"];
  const roundLabels = ["R64", "R32", "S16", "E8", "F4", "FINAL", "CHAMP"];

  id("modal-body").innerHTML = `
    <div class="modal-section">
      <div class="modal-section-title" style="border-color:${color}">SEASON STATS</div>
      <div class="modal-grid">
        <div class="modal-stat"><div class="modal-stat-label">Record</div><div class="modal-stat-val">${s.wins || 0}–${s.losses || 0}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">Win %</div><div class="modal-stat-val">${fmtNum(s.win_pct, 3)}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">PPG</div><div class="modal-stat-val">${fmtNum(s.ppg, 1)}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">Opp PPG</div><div class="modal-stat-val">${fmtNum(s.opp_ppg, 1)}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">FG%</div><div class="modal-stat-val">${fmtPctRaw(s.fg_pct)}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">3P%</div><div class="modal-stat-val">${fmtPctRaw(s.fg3_pct)}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">Adj Off</div><div class="modal-stat-val">${fmtNum(s.adj_off, 1)}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">Adj Def</div><div class="modal-stat-val">${fmtNum(s.adj_def, 1)}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">NET Rank</div><div class="modal-stat-val">${s.net_rank || "—"}</div></div>
      </div>
    </div>
    <div class="modal-section">
      <div class="modal-section-title" style="border-color:${color}">MONTE CARLO ADVANCEMENT (20K RUNS)</div>
      <div class="modal-round-grid">
        ${rounds.map((r, i) => `
          <div class="modal-round-item">
            <div class="modal-round-label">${roundLabels[i]}</div>
            <div class="modal-round-model">${fmtPct(mc[r] || 0)}</div>
            ${r === "Champion" && t.odds_champion_prob != null ? `<div class="modal-round-market">MKT: ${fmtPct(t.odds_champion_prob)}</div>` : ""}
          </div>`).join("")}
      </div>
    </div>
    ${t.odds_champion_prob != null ? `
    <div class="modal-section">
      <div class="modal-section-title" style="border-color:${color}">MODEL vs MARKET</div>
      <div class="modal-grid">
        <div class="modal-stat"><div class="modal-stat-label">Model Champion%</div><div class="modal-stat-val" style="color:${color}">${fmtPct(t.model_champion_prob || 0)}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">Market Champion%</div><div class="modal-stat-val">${fmtPct(t.odds_champion_prob)}</div></div>
        <div class="modal-stat"><div class="modal-stat-label">Edge (Δ)</div><div class="modal-stat-val ${t.model_edge > 0.005 ? "edge-pos" : t.model_edge < -0.005 ? "edge-neg" : ""}">${t.model_edge != null ? (t.model_edge > 0 ? "+" : "") + (t.model_edge * 100).toFixed(1) + "%" : "—"}</div></div>
      </div>
    </div>` : ""}
    ${t.r64_factors ? `
    <div class="modal-section">
      <div class="modal-section-title" style="border-color:${color}">R64 PROBABILITY FACTORS — vs ${esc(t.r64_factors.opponent)}</div>
      <div class="factors-row">
        <div class="factor-block">
          <div class="factor-val">${fmtPct(t.r64_factors.model_prob)}</div>
          <div class="factor-label">ML MODEL</div>
          <div class="factor-weight">× 0.70</div>
        </div>
        <div class="factor-op">+</div>
        <div class="factor-block">
          <div class="factor-val">${fmtPct(t.r64_factors.hist_seed_rate)}</div>
          <div class="factor-label">SEED HISTORY</div>
          <div class="factor-weight">× 0.30</div>
        </div>
        <div class="factor-op">+</div>
        <div class="factor-block">
          <div class="factor-val ${t.r64_factors.h2h_adj > 0 ? 'edge-pos' : t.r64_factors.h2h_adj < 0 ? 'edge-neg' : ''}">${t.r64_factors.h2h_adj !== 0 ? (t.r64_factors.h2h_adj > 0 ? '+' : '') + fmtPct(t.r64_factors.h2h_adj) : '—'}</div>
          <div class="factor-label">H2H ADJ</div>
          <div class="factor-weight">± 5% MAX</div>
        </div>
        <div class="factor-op">=</div>
        <div class="factor-block factor-result-block">
          <div class="factor-val">${fmtPct(t.r64_factors.blended_prob)}</div>
          <div class="factor-label">BLENDED</div>
          <div class="factor-weight">W/ ROUND VAR</div>
        </div>
      </div>
    </div>` : ""}
  `;

  id("modal-overlay").style.display = "flex";
}

function closeModal() {
  id("modal-overlay").style.display = "none";
}

// ── EVENT BINDING ────────────────────────────────────────────
function bindEvents() {
  // Table sort headers
  document.querySelectorAll("#odds-table thead th[data-sort]").forEach(th => {
    th.addEventListener("click", () => renderOddsTable(th.dataset.sort));
  });

  // Table search/filter
  id("odds-search")?.addEventListener("input", () => renderOddsTable());
  id("odds-region")?.addEventListener("change", () => renderOddsTable());

  // Monte Carlo round selector
  document.querySelectorAll(".round-btn").forEach(btn => {
    btn.addEventListener("click", () => renderMonteCarlo(btn.dataset.round));
  });

  // Modal close
  id("modal-close")?.addEventListener("click", closeModal);
  id("modal-overlay")?.addEventListener("click", e => {
    if (e.target === id("modal-overlay")) closeModal();
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeModal();
  });
}

// ── HELPERS ──────────────────────────────────────────────────
function id(elId) { return document.getElementById(elId); }
function setVal(elId, val) { const el = id(elId); if (el) el.textContent = val; }
function esc(str) { return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function fmtPct(v) { return v == null ? "—" : (v * 100).toFixed(1) + "%"; }
function fmtPctRaw(v) { if (!v || v === 0) return "—"; return v < 1 ? (v * 100).toFixed(1) + "%" : v.toFixed(1) + "%"; }
function fmtNum(v, dec) { return (v == null || v === 0) ? "—" : Number(v).toFixed(dec); }

function getVal(t, key) {
  const map = {
    team: t.name, seed: t.seed, region: t.region,
    model_champion_prob: t.model_champion_prob || 0,
    odds_champion_prob: t.odds_champion_prob || 0,
    model_edge: t.model_edge || -999,
    win_pct: t.stats?.win_pct || 0,
    ppg: t.stats?.ppg || 0,
  };
  return map[key] ?? 0;
}

function getStatsVal(t, key) {
  const s = t.stats || {};
  const map = { team: t.name, seed: t.seed, region: t.region, ...s };
  return map[key] ?? 0;
}

// ── START ────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", init);
