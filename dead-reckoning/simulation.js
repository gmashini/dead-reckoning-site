/**
 * Dead Reckoning Simulation Engine
 *
 * Runs 20,000 Monte Carlo trials to model the probability-weighted impact of
 * AI-driven events across 11 economic dimensions. Each trial samples event
 * occurrences from their probability ranges, applies three-tier impact vectors
 * (minimal / most_likely / outsized), and propagates chain reactions where
 * cascading events boost each other's probabilities.
 *
 * Key concepts:
 *   - Latent drivers: trial-level random factors (adoption friction, regulatory
 *     tightening, compute constraints) that correlate event probabilities
 *   - Soft clamping: tanh-based bounds that prevent runaway metric accumulation
 *   - Chain reactions: ordered event sequences where earlier events boost the
 *     probability of later ones, plus a systemic cascade impact
 */

let CATEGORY_COLORS = {};
let METRIC_COLORS = {};
const METRIC_COLOR_PALETTE = ['#9B7AE8','#F07070','#5B8DEF','#4ADE80','#FB923C','#EC4899','#0EA5E9','#FBBF24','#8B5CF6','#60a5fa','#34d399','#f87171','#a78bfa','#38bdf8','#facc15','#f472b6'];

function initModelConstants(MODEL) {
  CATEGORY_COLORS = {};
  for (const [name, data] of Object.entries(MODEL.categories)) {
    CATEGORY_COLORS[name] = data.color;
  }
  METRIC_COLORS = {};
  Object.keys(MODEL.baselines).forEach((key, i) => {
    METRIC_COLORS[key] = METRIC_COLOR_PALETTE[i % METRIC_COLOR_PALETTE.length];
  });
}

/* Normalize baselines: plain numbers → full objects */
function normalizeBaselines(baselines) {
  for (const [key, val] of Object.entries(baselines)) {
    if (typeof val !== 'object' || val === null) {
      const label = key
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, s => s.toUpperCase())
        .trim();
      baselines[key] = {
        value: val,
        unit: 'index',
        label: label,
        description: '',
        higherIsBetter: !key.toLowerCase().includes('stress') && !key.toLowerCase().includes('constraint'),
        primary: false,
        bounds: [val * 0.65, val * 1.35]
      };
    }
  }
  return baselines;
}

function getMetricUnit(baselines, key) {
  const raw = baselines[key]?.unit || '';
  if (!raw || raw === 'percentile' || raw === 'index') return '';
  if (raw === '%') return '%';
  if (raw === 'OEE %') return '%';
  if (raw === 'x EV/Rev') return 'x';
  return ' ' + raw;
}

let MODEL = null;

async function init() {
  const res = await fetch('model-data.json');
  MODEL = await res.json();
  normalizeBaselines(MODEL.baselines);

  initModelConstants(MODEL);

  // Set date
  const d = new Date(MODEL.date + 'T00:00:00');
  document.getElementById('model-date').textContent =
    'Model updated ' + d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  // Update description with dynamic dimension count
  const descEl = document.querySelector('#how-it-works .description');
  if (descEl) {
    const metricKeys = Object.keys(MODEL.baselines);
    const dimNames = metricKeys.map(k => MODEL.baselines[k].label).join(', ');
    descEl.textContent = `This model maps the risks and opportunities of artificial intelligence across multiple sectors assigning each item a probability range, timing window, and three-tier impact assessment (minimal, most likely, and outsized) across ${metricKeys.length} dimensions including ${dimNames}. Chain reactions model how events cascade across sectors, with probability boosts reflecting empirically observed correlations.`;
  }

  renderHowItWorks();
  renderCommentary();
  renderSectorOverview();

  // Run simulation
  const { results, resultsIndep } = runSimulation(20000);
  const baselines = MODEL.baselines;
  const dims = (MODEL.impactSchema && MODEL.impactSchema.dimensions) ? MODEL.impactSchema.dimensions : Object.keys(baselines);
  const metricKeys = dims;
  const stats = computeAllStats(results, metricKeys);
  const statsIndep = computeAllStats(resultsIndep, metricKeys);

  renderSimSummary(stats, results);
  renderMetricCards(stats);
  renderScenarioTable(stats);
  renderStatBars(stats);
  renderHistograms(results, resultsIndep);
  renderChainFrequency(results);
}

/* ── Flatten items ───────────────────────────────── */
function getAllItems() {
  const items = [];
  for (const [cat, data] of Object.entries(MODEL.categories)) {
    data.opportunities.forEach(o => items.push({ ...o, type: 'opp', category: cat }));
    data.risks.forEach(r => items.push({ ...r, type: 'risk', category: cat }));
  }
  return items;
}


/* ── Sampling + Validation Helpers ─────────────────── */
function clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }

/**
 * Soft-clamp a value toward bounds using tanh saturation.
 * Small deviations from baseline pass through nearly linearly, while large
 * deviations saturate toward the bound. This prevents metrics from reaching
 * unrealistic extremes when many events fire in the same trial.
 */
function softClamp(value, baseline, bounds) {
  if (!bounds || bounds.length !== 2) return value;
  const [lo, hi] = bounds;
  const delta = value - baseline;
  if (Math.abs(delta) < 1e-9) return baseline;
  if (delta > 0) {
    const maxUp = hi - baseline;
    if (maxUp <= 0) return baseline;
    return baseline + maxUp * Math.tanh(delta / maxUp);
  } else {
    const maxDown = baseline - lo;
    if (maxDown <= 0) return baseline;
    return baseline - maxDown * Math.tanh(-delta / maxDown);
  }
}

// Sample an event probability from its [low, high] percent range.
// Uniform is a reasonable first upgrade over midpoint; swap for Beta later if desired.
function sampleProb(rangePct) {
  const lo = clamp((rangePct?.[0] ?? 0) / 100, 0, 1);
  const hi = clamp((rangePct?.[1] ?? 0) / 100, 0, 1);
  if (hi < lo) return lo;
  return lo + Math.random() * (hi - lo);
}

// Sample which impact scenario occurs (minimal / most_likely / outsized).
function sampleImpactScenario(impactObj, weights = { minimal: 0.25, most_likely: 0.55, outsized: 0.20 }) {
  if (!impactObj) return { key: 'most_likely', vec: [] };
  const r = Math.random();
  const wMin = weights.minimal ?? 0.25;
  const wML  = weights.most_likely ?? 0.55;
  // outsized is residual
  if (r < wMin) return { key: 'minimal', vec: impactObj.minimal || [] };
  if (r < wMin + wML) return { key: 'most_likely', vec: impactObj.most_likely || [] };
  return { key: 'outsized', vec: impactObj.outsized || [] };
}

function validateModelOrThrow(MODEL, items, dims) {
  const baselineKeys = Object.keys(MODEL.baselines || {});
  const dimSet = new Set(dims);

  const missingBaselines = dims.filter(d => !baselineKeys.includes(d));
  if (missingBaselines.length) {
    console.warn('[model] Missing baselines for dimensions:', missingBaselines);
  }

  for (const item of items) {
    const p = item.probability || [0, 0];
    if (p[0] < 0 || p[1] > 100 || p[1] < p[0]) {
      console.warn('[model] Invalid probability range for', item.id, p);
    }
    const impacts = item.impact || {};
    for (const k of ['minimal', 'most_likely', 'outsized']) {
      const v = impacts[k] || [];
      if (v.length && v.length !== dims.length) {
        console.warn('[model] Impact vector length mismatch for', item.id, k, v.length, 'expected', dims.length);
      }
    }
  }

  for (const chain of (MODEL.chainReactions || [])) {
    for (const step of (chain.steps || [])) {
      const ok = items.some(i => i.id === step.item);
      if (!ok) console.warn('[model] Chain step references missing item:', chain.id, step.item);
    }
  }
}

/* ── Monte Carlo Engine ──────────────────────────── */

/**
 * Run the full Monte Carlo simulation.
 *
 * For each of `numTrials` trials:
 *   1. Sample latent drivers that create trial-level correlation
 *   2. Fire each event based on its probability (adjusted by drivers)
 *   3. Sample which impact scenario occurs (minimal/most_likely/outsized)
 *   4. Accumulate impact vectors into metric totals
 *   5. Process chain reactions: if early steps fired, boost later steps
 *   6. Soft-clamp all metrics to prevent runaway accumulation
 *
 * Returns two result arrays: `results` (with chains) and `resultsIndep`
 * (without chains) for comparison visualization.
 */
function runSimulation(numTrials) {
  const items = getAllItems();
  const chains = MODEL.chainReactions || [];
  const baselines = MODEL.baselines || {};
  const dims = (MODEL.impactSchema && MODEL.impactSchema.dimensions) ? MODEL.impactSchema.dimensions : Object.keys(baselines);

  validateModelOrThrow(MODEL, items, dims);

  const results = [];
  const resultsIndep = [];

  // Helper to initialize a trial record
  const initTrial = () => {
    const trial = { materialized: [], chainsActivated: [] };
    dims.forEach(d => { trial[d] = (baselines[d] && typeof baselines[d].value === 'number') ? baselines[d].value : 0; });
    return trial;
  };

  const applyImpact = (trial, vec, scale = 1.0) => {
    dims.forEach((d, i) => { trial[d] += (vec && vec[i] != null ? vec[i] : 0) * scale; });
  };

  // Latent drivers create trial-level regimes that correlate event probabilities.
  // High adoption friction → opportunities less likely to realize
  // High regulatory tightening → political/information risks more likely
  // High compute constraint → energy/infrastructure risks more likely
  const sampleDrivers = () => ({
    adoptionFriction: Math.random(),      // higher => opps less likely to realize quickly
    regulatoryTightening: Math.random(),  // higher => political risk items more likely
    computeConstraint: Math.random()      // higher => infra/cost risks more likely
  });

  const probWithDrivers = (item, drivers) => {
    let p = sampleProb(item.probability);

    // Adoption friction dampens opportunities broadly (and slightly dampens some risks tied to rapid rollout)
    if (item.type === 'opp') p -= (drivers.adoptionFriction - 0.5) * 0.10;

    // Regulatory tightening increases politics risks and information-integrity-related risks
    const name = (item.name || '').toLowerCase();
    const detail = (item.detail || '').toLowerCase();
    const text = name + ' ' + detail;
    if (item.type === 'risk' && item.category === 'Politics') p += (drivers.regulatoryTightening - 0.5) * 0.12;
    if (item.type === 'risk' && (text.includes('misinfo') || text.includes('deepfake') || text.includes('fraud'))) {
      p += (drivers.regulatoryTightening - 0.5) * 0.05;
    }

    // Compute constraint increases energy/compute/cost/infrastructure risks and slightly boosts related opportunities
    if (text.includes('energy') || text.includes('compute') || text.includes('semiconductor') || text.includes('data center') || text.includes('power')) {
      if (item.type === 'risk') p += (drivers.computeConstraint - 0.5) * 0.12;
      else p += (drivers.computeConstraint - 0.5) * 0.04;
    }

    return clamp(p, 0, 0.99);
  };

  for (let t = 0; t < numTrials; t++) {
    const drivers = sampleDrivers();

    // Independent run (no chains)
    const trialIndep = initTrial();
    const materializedIndep = new Set();
    for (const item of items) {
      const p = probWithDrivers(item, drivers);
      if (Math.random() < p) {
        materializedIndep.add(item.id);
        trialIndep.materialized.push(item.id);
        const imp = sampleImpactScenario(item.impact).vec;
        applyImpact(trialIndep, imp, 1.0);
      }
    }
    // Soft-clamp metrics to prevent runaway accumulation
    dims.forEach(d => {
      const b = baselines[d];
      if (b && b.bounds) trialIndep[d] = softClamp(trialIndep[d], b.value, b.bounds);
    });
    resultsIndep.push(trialIndep);

    // Chain-linked run
    const trial = initTrial();
    const materialized = new Set();

    // First pass: fire items (baseline realization)
    for (const item of items) {
      const p = probWithDrivers(item, drivers);
      if (Math.random() < p) {
        materialized.add(item.id);
        trial.materialized.push(item.id);
        const imp = sampleImpactScenario(item.impact).vec;
        applyImpact(trial, imp, 1.0);
      }
    }

    // Chain reactions: boosted conditional probabilities; if a chain step "creates" an event, apply its impact once.
    for (const chain of chains) {
      let activated = false;

      for (const step of (chain.steps || [])) {
        const baseItem = items.find(i => i.id === step.item);
        if (!baseItem) { activated = false; break; }

        if (materialized.has(step.item)) {
          activated = true; // chain can proceed
          continue;
        }

        // Only allow chain to create new events after the chain has activated.
        if (!activated) { activated = false; break; }

        const baseP = probWithDrivers(baseItem, drivers);
        const boosted = clamp(baseP + (step.boost || 0) / 100, 0, 0.99);

        if (Math.random() < boosted) {
          materialized.add(step.item);
          trial.materialized.push(step.item);
          const imp = sampleImpactScenario(baseItem.impact).vec;
          applyImpact(trial, imp, 1.0);
        } else {
          activated = false;
          break;
        }
      }

      if (activated) {
        trial.chainsActivated.push(chain.id);
        // Cascade impact is a smaller systemic shock on top of step impacts.
        const ci = sampleImpactScenario(chain.cascadeImpact, { minimal: 0.30, most_likely: 0.50, outsized: 0.20 }).vec;
        applyImpact(trial, ci, 0.30);
      }
    }

    // Soft-clamp metrics to prevent runaway accumulation
    dims.forEach(d => {
      const b = baselines[d];
      if (b && b.bounds) trial[d] = softClamp(trial[d], b.value, b.bounds);
    });
    results.push(trial);
  }

  return { results, resultsIndep };
}

/* ── Stats ───────────────────────────────────────── */
function percentile(arr, p) {
  const sorted = [...arr].sort((a, b) => a - b);
  const idx = (p / 100) * (sorted.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
}

function computeStats(values) {
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  return {
    mean: Math.round(mean * 100) / 100,
    p5: Math.round(percentile(values, 5) * 100) / 100,
    p25: Math.round(percentile(values, 25) * 100) / 100,
    p50: Math.round(percentile(values, 50) * 100) / 100,
    p75: Math.round(percentile(values, 75) * 100) / 100,
    p95: Math.round(percentile(values, 95) * 100) / 100,
  };
}

function computeAllStats(results, metricKeys) {
  const stats = {};
  metricKeys.forEach(k => {
    stats[k] = computeStats(results.map(r => r[k]));
  });
  return stats;
}

/* ── Rendering Functions ─────────────────────────────
 * Each render function reads from the computed stats and MODEL data
 * to populate a specific section of the page.
 * They generate HTML strings and inject them via innerHTML.
 */

function renderHowItWorks() {
  const items = getAllItems();
  const chains = MODEL.chainReactions;
  const catCount = Object.keys(MODEL.categories).length;
  const features = [
    { number: items.length + '+', label: `events modeled across ${catCount} categories — each with probability ranges and timing.`, color: '#5B8DEF' },
    { number: chains.length, label: 'chain reactions capture how events cascade across categories. When one fires, it boosts or suppresses others.', color: '#9B7AE8' },
    { number: '20K', label: 'simulations run to reveal the full range of possible outcomes — not just a single forecast.', color: '#FB923C' },
  ];
  const container = document.getElementById('how-it-works-features');
  container.innerHTML = features.map(f => `
    <div class="feature-row">
      <div class="feature-number" style="background:${f.color}">${f.number}</div>
      <span style="font-size:1rem;color:var(--text-secondary);line-height:1.6;flex:1">${f.label}</span>
    </div>
  `).join('');
}

function renderCommentary() {
  const c = MODEL.commentary;
  if (!c) return;
  document.getElementById('commentary-summary').textContent = c.summary;

  const themesContainer = document.getElementById('key-themes');
  themesContainer.innerHTML = c.keyThemes.map((t, i) => `
    <div class="theme-card">
      <div class="theme-card-header" onclick="toggleTheme(${i})">
        <h4>${t.theme}</h4>
        <span class="chevron" id="theme-chev-${i}">&#9660;</span>
      </div>
      <div class="theme-card-body" id="theme-body-${i}">
        <p>${t.narrative}</p>
      </div>
    </div>
  `).join('');

  if (c.modelAssumptions) {
    document.getElementById('assumptions-box').style.display = 'block';
    document.getElementById('assumptions-text').textContent = c.modelAssumptions;
  }
}

function toggleTheme(i) {
  const body = document.getElementById('theme-body-' + i);
  const chev = document.getElementById('theme-chev-' + i);
  body.classList.toggle('open');
  chev.classList.toggle('open');
}

function renderSectorOverview() {
  const grid = document.getElementById('sector-grid');
  const cats = Object.entries(MODEL.categories);
  grid.innerHTML = cats.map(([name, cat]) => {
    const color = CATEGORY_COLORS[name] || '#5B8DEF';
    const oppAvg = cat.opportunities.length > 0
      ? Math.round(cat.opportunities.reduce((s, o) => s + (o.probability[0] + o.probability[1]) / 2, 0) / cat.opportunities.length)
      : 0;
    const riskAvg = cat.risks.length > 0
      ? Math.round(cat.risks.reduce((s, r) => s + (r.probability[0] + r.probability[1]) / 2, 0) / cat.risks.length)
      : 0;
    return `
      <div class="sector-card" style="border-left-color:${color}">
        <h4 style="color:${color}">${name}</h4>
        <div class="sector-stat">
          <span class="dot" style="background:var(--accent-green)"></span>
          <span>Avg opportunity: <span class="val">${oppAvg}%</span></span>
        </div>
        <div class="sector-stat">
          <span class="dot" style="background:var(--accent-red)"></span>
          <span>Avg risk: <span class="val">${riskAvg}%</span></span>
        </div>
        <div class="sector-stat" style="margin-top:6px;">
          <span style="font-size:0.8rem;color:var(--text-dim)">${cat.opportunities.length} opps &middot; ${cat.risks.length} risks</span>
        </div>
      </div>
    `;
  }).join('');
}

function renderSimSummary(stats, results) {
  const baselines = MODEL.baselines;
  const dims = (MODEL.impactSchema && MODEL.impactSchema.dimensions) ? MODEL.impactSchema.dimensions : Object.keys(baselines);
  const metricKeys = dims;
  const chainsActivated = results.reduce((s, r) => s + r.chainsActivated.length, 0) / results.length;

  // Build dynamic bullets for primary metrics
  const bullets = [];
  metricKeys.filter(k => baselines[k].primary).forEach(k => {
    const b = baselines[k];
    const unit = getMetricUnit(baselines, k);
    bullets.push(`${b.label}: median <span class="val">${stats[k].p50}${unit}</span> (from ${b.value}${unit} baseline)`);
  });
  bullets.push(`Average chains activated per trial: <span class="val">${chainsActivated.toFixed(1)}</span>`);

  document.getElementById('sim-bullets').innerHTML = bullets.map(b => `
    <li><span class="bullet-dot"></span><span>${b}</span></li>
  `).join('');
}

function renderMetricCards(stats) {
  const baselines = MODEL.baselines;
  const dims = (MODEL.impactSchema && MODEL.impactSchema.dimensions) ? MODEL.impactSchema.dimensions : Object.keys(baselines);
  const metricKeys = dims;

  document.getElementById('metric-cards').innerHTML = metricKeys.map(key => {
    const s = stats[key];
    const b = baselines[key];
    const color = METRIC_COLORS[key];
    const unit = getMetricUnit(baselines, key);
    const label = b.label || key;
    const hib = b.higherIsBetter !== false;
    const change = s.p50 - b.value;
    const sign = change >= 0 ? '+' : '';
    const changeColor = hib
      ? (change >= 0 ? 'var(--positive)' : 'var(--negative)')
      : (change > 0 ? 'var(--negative)' : 'var(--positive)');
    return `
      <div class="metric-card">
        <div class="metric-label" style="color:${color}">${label}</div>
        <div class="metric-value" style="color:${color}">${s.p50}${unit}</div>
        <div class="metric-change" style="color:${changeColor}">${sign}${change.toFixed(2)}${unit} from baseline</div>
        <div class="metric-baseline">Baseline: ${b.value}${unit}</div>
      </div>
    `;
  }).join('');
}

function renderScenarioTable(stats) {
  const baselines = MODEL.baselines;
  const dims = (MODEL.impactSchema && MODEL.impactSchema.dimensions) ? MODEL.impactSchema.dimensions : Object.keys(baselines);
  const metricKeys = dims;

  document.getElementById('scenario-tbody').innerHTML = metricKeys.map(key => {
    const s = stats[key];
    const b = baselines[key];
    const color = METRIC_COLORS[key];
    const unit = getMetricUnit(baselines, key);
    const label = b.label || key;
    const hib = b.higherIsBetter !== false;
    const bull = hib ? s.p75 : s.p25;
    const base = s.p50;
    const bear = hib ? s.p25 : s.p75;
    const tail = hib ? s.p5 : s.p95;
    return `
      <tr>
        <td class="metric-name" style="color:${color}">${label}</td>
        <td>${b.value}${unit}</td>
        <td>${bull}${unit}</td>
        <td>${base}${unit}</td>
        <td>${bear}${unit}</td>
        <td>${tail}${unit}</td>
      </tr>
    `;
  }).join('');
}

function renderStatBars(stats) {
  const baselines = MODEL.baselines;
  const container = document.getElementById('stat-bars');
  const dims = (MODEL.impactSchema && MODEL.impactSchema.dimensions) ? MODEL.impactSchema.dimensions : Object.keys(baselines);
  const metricKeys = dims;

  metricKeys.forEach(key => {
    const s = stats[key];
    const b = baselines[key];
    const color = METRIC_COLORS[key];
    const label = b.label || key;
    const min = Math.min(s.p5, b.value) - 2;
    const max = Math.max(s.p95, b.value) + 2;
    const range = max - min;
    const pct = v => ((v - min) / range * 100).toFixed(1);

    const el = document.createElement('div');
    el.className = 'stat-bar-item';
    el.innerHTML = `
      <h4 style="color:${color}">${label}</h4>
      <div class="bar-track">
        <div class="bar-range" style="left:${pct(s.p5)}%;right:${100 - pct(s.p95)}%;background:${color}"></div>
        <div class="bar-iqr" style="left:${pct(s.p25)}%;right:${100 - pct(s.p75)}%;background:${color}"></div>
        <div class="bar-median" style="left:${pct(s.p50)}%;background:${color}"></div>
        <div class="bar-baseline" style="left:${pct(b.value)}%;" title="Baseline: ${b.value}"></div>
      </div>
      <div class="bar-labels">
        <span>P5: ${s.p5}</span>
        <span>P25: ${s.p25}</span>
        <span>P50: ${s.p50}</span>
        <span>P75: ${s.p75}</span>
        <span>P95: ${s.p95}</span>
      </div>
    `;
    container.appendChild(el);
  });
}

function renderHistograms(results, resultsIndep) {
  const baselines = MODEL.baselines;
  const dims = (MODEL.impactSchema && MODEL.impactSchema.dimensions) ? MODEL.impactSchema.dimensions : Object.keys(baselines);
  const metricKeys = dims;
  const container = document.getElementById('histogram-grid');

  metricKeys.forEach(key => {
    const color = METRIC_COLORS[key];
    const unit = getMetricUnit(baselines, key);
    const label = baselines[key].label || key;
    const vals = results.map(r => r[key]);
    const valsAlt = resultsIndep.map(r => r[key]);
    const baseline = baselines[key].value;

    const allVals = [...vals, ...valsAlt];
    const min = Math.min(...allVals);
    const max = Math.max(...allVals);
    const buckets = 30;
    const step = (max - min) / buckets || 1;

    function toBins(data) {
      const bins = new Array(buckets).fill(0);
      data.forEach(v => {
        const idx = Math.min(Math.floor((v - min) / step), buckets - 1);
        bins[idx]++;
      });
      return bins;
    }

    const bins = toBins(vals);
    const binsAlt = toBins(valsAlt);
    const maxBin = Math.max(...bins, ...binsAlt);

    const w = 100;
    const h = 100;
    const barW = w / buckets;

    const barsChain = bins.map((b, i) => {
      const bh = maxBin > 0 ? (b / maxBin) * h : 0;
      return `<rect x="${i * barW}" y="${h - bh}" width="${barW - 0.5}" height="${bh}" fill="${color}" opacity="0.6" rx="1"/>`;
    }).join('');

    const barsIndep = binsAlt.map((b, i) => {
      const bh = maxBin > 0 ? (b / maxBin) * h : 0;
      return `<rect x="${i * barW}" y="${h - bh}" width="${barW - 0.5}" height="${bh}" fill="rgba(255,255,255,0.12)" rx="1"/>`;
    }).join('');

    const baselineX = ((baseline - min) / (max - min)) * w;

    const card = document.createElement('div');
    card.className = 'histogram-card';
    card.innerHTML = `
      <h4 style="color:${color}">${label} Distribution</h4>
      <div style="display:flex;gap:16px;margin-bottom:12px;font-size:0.8rem;">
        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:14px;height:10px;border-radius:3px;background:${color};opacity:0.6"></span><span style="color:var(--text-secondary)">Chains</span></span>
        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:14px;height:10px;border-radius:3px;background:rgba(255,255,255,0.12)"></span><span style="color:var(--text-muted)">Independent</span></span>
      </div>
      <svg viewBox="0 0 ${w} ${h + 10}" class="histogram-canvas" preserveAspectRatio="none">
        ${barsIndep}
        ${barsChain}
        <line x1="${baselineX}" y1="0" x2="${baselineX}" y2="${h}" stroke="rgba(255,255,255,0.4)" stroke-width="0.5" stroke-dasharray="2,2"/>
      </svg>
      <div style="display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:0.7rem;color:var(--text-dim);margin-top:4px;">
        <span>${min.toFixed(1)}${unit}</span>
        <span>Baseline: ${baseline}${unit}</span>
        <span>${max.toFixed(1)}${unit}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderChainFrequency(results) {
  const chains = MODEL.chainReactions;
  const total = results.length;
  const freqs = {};
  chains.forEach(c => freqs[c.id] = { name: c.name, count: 0 });
  results.forEach(r => r.chainsActivated.forEach(id => { if (freqs[id]) freqs[id].count++; }));

  const sorted = Object.values(freqs).sort((a, b) => b.count - a.count);
  const maxCount = sorted[0]?.count || 1;

  document.getElementById('freq-bars').innerHTML = sorted.map(f => {
    const pct = (f.count / total * 100).toFixed(0);
    const barPct = (f.count / maxCount * 100).toFixed(0);
    return `
      <div class="freq-bar-row">
        <span class="freq-bar-label">${f.name}</span>
        <div class="freq-bar-track">
          <div class="freq-bar-fill" style="width:${barPct}%;background:var(--accent-purple)"></div>
        </div>
        <span class="freq-bar-val">${pct}%</span>
      </div>
    `;
  }).join('');
}

init();
