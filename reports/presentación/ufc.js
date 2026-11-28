/* =====================================================================
   Diapositivas 14–18 · Monte Carlo con peleas reales de la UFC
   Adaptación de la pestaña «🎲 Monte Carlo» de app.py (monte_carlo.py).
   Datos: datos_mma.js (generado por exportar_datos.py).
   ===================================================================== */
(() => {
  "use strict";
  const { $, $$, C, fmt, makeChart, axes, roundedBar, niceStep, traceDrawer, pushHist, renderMath } = window.MC;

  const pct = (x, d = 1) => `${fmt(100 * x, d)} %`;
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  // Generador pseudoaleatorio con semilla (mulberry32): misma semilla → mismos números
  function rngFrom(seed) {
    let a = (seed >>> 0) + 0x9e3779b9;
    return () => {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* ------------------------------------------------------------------
     Datos
     ------------------------------------------------------------------ */
  const BANDS = ["50–60 %", "60–70 %", "70–80 %", "80 % o más", "Todas"];
  // Igual que pd.cut([.5,.6,.7,.8,1], include_lowest=True): intervalos cerrados por la derecha
  const bandOf = (p) => (p <= 0.6 ? 0 : p <= 0.7 ? 1 : p <= 0.8 ? 2 : 3);
  const DATA = window.MMA;
  if (!DATA) {
    $$(".s-one, .s-hist, .s-test, .s-concl").forEach((s) => s.insertAdjacentHTML("beforeend",
      '<div class="nodata card">Falta <b>datos_mma.js</b>. Ejecuta <code>python "reports/presentación/exportar_datos.py"</code>.</div>'));
    return;
  }
  const FIGHTS = DATA.fights.map(([date, fav, dog, p, won]) => ({ date, fav, dog, p, won, band: bandOf(p) }));
  const groupOf = (b) => (b === 4 ? FIGHTS : FIGHTS.filter((f) => f.band === b));

  const PRESETS = [
    ["Steveson", "Sharaf"],
    ["Topuria", "Gaethje"],
    ["Topuria", "Oliveira"],
  ].map(([a, b]) => FIGHTS.filter((f) => f.fav.includes(a) && f.dog.includes(b)).pop()).filter(Boolean);

  /* ------------------------------------------------------------------
     12 · Sortear u para una pelea
     ------------------------------------------------------------------ */
  const uFight = PRESETS[0] || { fav: "el favorito", dog: "el rival", p: 0.904, won: 0, date: "" };
  $("#u-title").innerHTML = `${esc(uFight.fav)} vs. ${esc(uFight.dog)} · \\(p = ${uFight.p.toFixed(3)}\\)`;
  $("#u-fav").style.width = `${100 * uFight.p}%`;
  $("#u-fav").textContent = `gana ${uFight.fav.split(" ").pop()}`;
  $("#u-p").style.left = `${100 * uFight.p}%`;
  $("#u-p").textContent = `p = ${uFight.p.toFixed(3)}`;
  const uHistory = [];
  $("#u-roll").onclick = () => {
    const u = Math.random();
    const fav = u < uFight.p;
    uHistory.push(fav);
    const mark = document.createElement("div");
    mark.className = `ubar-mark ${fav ? "fav" : "dog"}`;
    mark.style.left = `${100 * u}%`;
    mark.innerHTML = `<span>u = ${u.toFixed(3)}</span>`;
    $$(".ubar-mark", $("#u-track")).forEach((m) => m.classList.add("old"));
    $("#u-track").appendChild(mark);
    const ups = uHistory.filter((x) => !x).length;
    $("#u-read").innerHTML = `${fav ? `\\(u &lt; p\\): <b class="t-fav">gana ${esc(uFight.fav)}</b>` : `\\(u \\ge p\\): <b class="t-dog">¡sorpresa! gana ${esc(uFight.dog)}</b>`}`
      + ` &nbsp;·&nbsp; Lanzamientos: <b>${uHistory.length}</b> · sorpresas: <b>${ups}</b>`;
    renderMath($("#u-read"));
  };

  /* ------------------------------------------------------------------
     13 · Una pelea, muchas veces
     ------------------------------------------------------------------ */
  const CUSTOM = "custom";
  const one = { hist: [], truth: 0.1 };
  $("#mc-fight").innerHTML = PRESETS.map((f, i) => `<option value="${i}">${esc(f.fav)} vs. ${esc(f.dog)} · ${f.date.slice(0, 4)}</option>`).join("")
    + `<option value="${CUSTOM}">Probabilidad personalizada</option>`;
  $("#mc-n").innerHTML = [10, 50, 100, 500, 1000, 5000, 20000, 100000]
    .map((n) => `<option value="${n}"${n === 500 ? " selected" : ""}>${fmt(n)}</option>`).join("");

  const oneChart = makeChart($("#mc-conv"), traceDrawer(one, () => ({
    truth: one.truth, ylo: 0, yhi: Math.min(1, Math.max(0.2, one.truth * 2.6)),
    ylab: "frecuencia de sorpresas", xlab: "número de simulaciones (escala log)",
    fmtY: (v) => pct(v, v < 0.1 && v > 0 ? 1 : 0), truthLabel: `real: ${pct(one.truth)}`,
    funnel: true, lineColor: C.rust, truthColor: C.blue,
  })), $("#mc-tip"));

  function runOne() {
    const sel = $("#mc-fight").value;
    const custom = sel === CUSTOM;
    $("#mc-custom").style.display = custom ? "" : "none";
    let p, fav, dog, real = "";
    if (custom) {
      p = +$("#mc-p").value / 100; fav = "el favorito"; dog = "el no favorito";
      $("#mc-p-lbl").textContent = `${$("#mc-p").value} %`;
    } else {
      const f = PRESETS[+sel];
      ({ p, fav, dog } = f);
      real = ` En la realidad ganó <b class="${f.won ? "t-fav" : "t-dog"}">${esc(f.won ? fav : dog)}</b>.`;
    }
    const N = +$("#mc-n").value, rng = rngFrom(+$("#mc-seed").value || 0), q = 1 - p;
    one.truth = q; one.hist = [];
    const coins = [];
    let ups = 0;
    for (let i = 1; i <= N; i++) {
      const won = rng() < p;
      if (!won) ups++;
      if (i <= 300) coins.push(won);
      pushHist(one, i, ups / i, 1.96 * Math.sqrt((q * (1 - q)) / i));
    }
    const est = ups / N, se = Math.sqrt((est * (1 - est)) / N);
    $("#mc-odds").innerHTML = `Cuota de apertura: <b class="t-fav">${esc(fav)} ${pct(p)}</b> · <span class="t-dog">${esc(dog)} ${pct(q)}</span>.${real}`;
    $("#mc-k1").textContent = `Sorpresas en ${fmt(N)} peleas`;
    $("#mc-v1").textContent = fmt(ups);
    $("#mc-v2").textContent = pct(est, 2);
    const diff = 100 * (est - q);
    $("#mc-d2").textContent = `${diff >= 0 ? "+" : "−"}${fmt(Math.abs(diff), 2)} pts vs. real`;
    $("#mc-v3").textContent = `±${pct(se, 2)}`;
    $("#mc-coins-title").innerHTML = `<b>Las primeras ${coins.length} peleas simuladas</b>, una por cuadrito:`;
    $("#mc-coins").innerHTML = coins.map((w) => `<span class="${w ? "w" : "u"}"></span>`).join("");
    $("#mc-coin-legend").innerHTML = `<span><i style="background:var(--blue)"></i>gana ${esc(fav)}</span><span><i style="background:var(--rust)"></i>sorpresa: gana ${esc(dog)}</span>`;
    oneChart.render();
  }
  ["#mc-fight", "#mc-n", "#mc-seed"].forEach((s) => $(s).addEventListener("change", runOne));
  $("#mc-p").addEventListener("input", runOne);
  $("#mc-reroll").onclick = () => { $("#mc-seed").value = (+$("#mc-seed").value || 0) + 1; runOne(); };

  /* ------------------------------------------------------------------
     Grupo de favoritos compartido por las diapositivas 14 y 15
     ------------------------------------------------------------------ */
  let band = 2;
  $$(".band-seg").forEach((seg) => {
    seg.innerHTML = BANDS.map((b, i) => `<button data-band="${i}">${b}</button>`).join("");
    seg.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      band = +b.dataset.band;
      syncBand(); runSample(); runTest();
    });
  });
  function syncBand() {
    $$(".band-seg button").forEach((b) => b.classList.toggle("on", +b.dataset.band === band));
  }

  /* ------------------------------------------------------------------
     14 · Así se juega una historia
     ------------------------------------------------------------------ */
  let sampleSeed = 7;
  function runSample() {
    const g = groupOf(band), rng = rngFrom(sampleSeed);
    // muestra de 8 peleas sin reemplazo (Fisher–Yates parcial)
    const idx = g.map((_, i) => i);
    for (let i = 0; i < 8; i++) { const j = i + Math.floor(rng() * (idx.length - i)); [idx[i], idx[j]] = [idx[j], idx[i]]; }
    const rows = idx.slice(0, 8).map((i) => g[i]).sort((a, b) => a.date.localeCompare(b.date));
    const pill = (fav) => (fav ? '<span class="pill fav">✓ favorito</span>' : '<span class="pill dog">✗ sorpresa</span>');
    $("#h-table").innerHTML = "<tr><th>Fecha</th><th>Favorito</th><th>Rival</th><th>p (cuota)</th><th>u aleatorio</th><th>Simulación</th><th>Realidad</th></tr>"
      + rows.map((f) => {
        const u = rng();
        return `<tr><td>${f.date}</td><td>${esc(f.fav)}</td><td>${esc(f.dog)}</td><td class="num">${pct(f.p)}</td>`
          + `<td class="num"><b>${u.toFixed(3)}</b></td><td>${pill(u < f.p)}</td><td>${pill(f.won)}</td></tr>`;
      }).join("");
    $("#h-caption").innerHTML = `<b>${fmt(g.length)} peleas</b> en el grupo, un número aleatorio \\(u\\) por pelea. Aquí van ocho:`;
    renderMath($("#h-caption"));
    // una historia alternativa completa
    let wins = 0;
    for (const f of g) if (rng() < f.p) wins++;
    const real = g.reduce((s, f) => s + f.won, 0);
    $("#h-one").innerHTML = `<div class="k">Una historia alternativa completa</div>`
      + `<div class="cmp"><div><span class="big t-fav">${fmt(wins)}</span>favoritos ganan en la simulación</div>`
      + `<div><span class="big">${fmt(real)}</span>ganaron en la realidad</div></div>`
      + `<div class="d">de ${fmt(g.length)} peleas. ¿La diferencia es suerte? → repetir miles de veces.</div>`;
  }
  $("#h-resample").onclick = () => { sampleSeed++; runSample(); };

  /* ------------------------------------------------------------------
     15 · Prueba de calibración: miles de historias
     ------------------------------------------------------------------ */
  $("#t-n").innerHTML = [100, 500, 2000, 5000, 20000]
    .map((n) => `<option value="${n}"${n === 2000 ? " selected" : ""}>${fmt(n)}</option>`).join("");
  const test = { sims: [], target: 0, observed: 0, group: [], token: 0 };

  function percentile(sorted, q) {
    const i = (sorted.length - 1) * q, lo = Math.floor(i), hi = Math.ceil(i);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (i - lo);
  }
  function pValue(sims, obs) {
    const n = sims.length;
    let le = 0, ge = 0;
    for (const s of sims) { if (s <= obs) le++; if (s >= obs) ge++; }
    return Math.min(1, 2 * Math.min((le + 1) / (n + 1), (ge + 1) / (n + 1)));
  }

  function runTest() {
    const token = ++test.token;
    const g = groupOf(band), probs = Float64Array.from(g, (f) => f.p);
    const total = +$("#t-n").value, rng = rngFrom(+$("#t-seed").value || 0);
    Object.assign(test, { sims: [], target: total, group: g, observed: g.reduce((s, f) => s + f.won, 0) });
    const meanP = probs.reduce((a, b) => a + b, 0) / probs.length;
    $("#t-obs").textContent = fmt(test.observed);
    $("#t-obs-d").textContent = `${pct(test.observed / g.length)} de ${fmt(g.length)} peleas`;
    $("#t-exp-d").textContent = `prob. media del mercado: ${pct(meanP)}`;
    const perFrame = Math.max(1, Math.floor(400000 / probs.length));
    const step = () => {
      if (token !== test.token) return; // se cambiaron los parámetros: abandonar esta corrida
      const end = Math.min(total, test.sims.length + perFrame);
      while (test.sims.length < end) {
        let w = 0;
        for (let i = 0; i < probs.length; i++) if (rng() < probs[i]) w++;
        test.sims.push(w);
      }
      updateTestCards();
      testChart.render();
      if (test.sims.length < total) requestAnimationFrame(step);
    };
    step();
  }

  function updateTestCards() {
    const s = test.sims, n = s.length;
    if (!n) return;
    const sorted = Float64Array.from(s).sort();
    const lo = percentile(sorted, 0.025), hi = percentile(sorted, 0.975);
    const mean = s.reduce((a, b) => a + b, 0) / n, pv = pValue(s, test.observed);
    Object.assign(test, { lo, hi });
    $("#t-exp").textContent = fmt(mean);
    $("#t-rng").textContent = `${fmt(lo)}–${fmt(hi)}`;
    $("#t-p").textContent = pv.toFixed(4);
    $("#t-p-d").textContent = `bilateral · mínimo posible ${(2 / (n + 1)).toFixed(4)}`;
    $("#t-progress").textContent = n < test.target ? `simulando… ${fmt(n)} / ${fmt(test.target)}` : `${fmt(n)} historias`;
    const v = $("#t-verdict"), o = test.observed;
    if (n < test.target) { v.className = "verdict"; v.textContent = ""; return; }
    if (o >= lo && o <= hi) {
      v.className = "verdict ok";
      v.innerHTML = "✓ La realidad cae dentro de lo que el azar produce normalmente: los datos son <b>compatibles con una cuota bien calibrada</b> en este grupo.";
    } else if (o > hi) {
      v.className = "verdict warn";
      v.innerHTML = "⚠ La realidad queda <b>a la derecha</b> de casi todas las historias: estos favoritos ganaron más de lo que decía la cuota. El mercado los <b>infravaloraba</b>.";
    } else {
      v.className = "verdict warn";
      v.innerHTML = "⚠ La realidad queda <b>a la izquierda</b> de casi todas las historias: estos favoritos ganaron menos de lo que decía la cuota.";
    }
  }

  const testChart = makeChart($("#t-canvas"), (ch) => {
    const { ctx, w, h } = ch, s = test.sims;
    if (!s.length) return;
    const obs = test.observed;
    let mn = Infinity, mx = -Infinity;
    for (const v of s) { if (v < mn) mn = v; if (v > mx) mx = v; }
    mn = Math.min(mn, obs); mx = Math.max(mx, obs);
    const pad = Math.max(3, 0.08 * (mx - mn));
    const x0 = mn - pad, x1 = mx + pad;
    // ancho de barra: 1 victoria, o agrupado si el rango es muy amplio
    const bw = Math.max(1, Math.ceil((x1 - x0) / 70));
    const start = Math.floor(x0 / bw) * bw, nb = Math.ceil((x1 - start) / bw);
    const counts = new Array(nb).fill(0);
    for (const v of s) counts[Math.floor((v - start) / bw)]++;
    const ymax = Math.max(...counts) * 1.12;
    const box = { l: 84, r: w - 20, t: 30, b: h - 58 };
    const X = (v) => box.l + ((v - x0) / (x1 - x0)) * (box.r - box.l);
    const Y = (c) => box.b - (c / ymax) * (box.b - box.t);
    const xs = niceStep((x1 - x0) / 7), ys = niceStep(ymax / 4);
    const xt = [], yt = [];
    for (let v = Math.ceil(x0 / xs) * xs; v <= x1; v += xs) xt.push({ x: X(v), label: fmt(v) });
    for (let v = 0; v <= ymax; v += ys) yt.push({ y: Y(v), label: fmt(v) });
    // rango 95 %
    if (test.lo != null) {
      ctx.fillStyle = "rgba(47,102,144,.13)";
      ctx.fillRect(X(test.lo), box.t, X(test.hi) - X(test.lo), box.b - box.t);
    }
    axes(ctx, box, { xticks: xt, yticks: yt, xlab: "victorias de favoritos en cada historia simulada", ylab: "historias simuladas" });
    ctx.fillStyle = C.blue;
    counts.forEach((c, i) => {
      const a = X(start + i * bw - 0.5), b = X(start + (i + 1) * bw - 0.5), y = Y(c);
      if (c) roundedBar(ctx, a + 1, y, Math.max(1, b - a - 2), box.b - y, 3);
      ch.hits.push({ rect: true, x0: a, x1: b, ytop: y,
        html: `${bw === 1 ? `${fmt(start + i * bw)} victorias` : `${fmt(start + i * bw)}–${fmt(start + (i + 1) * bw - 1)} victorias`}<br><b>${fmt(c)}</b> historias` });
    });
    // realidad
    const xo = X(obs);
    ctx.strokeStyle = C.rust; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(xo, box.t - 6); ctx.lineTo(xo, box.b); ctx.stroke();
    ctx.fillStyle = C.rust; ctx.font = "700 19px Inter, sans-serif"; ctx.textBaseline = "top";
    const right = xo > (box.l + box.r) / 2;
    ctx.textAlign = right ? "right" : "left";
    ctx.fillText(`Realidad: ${fmt(obs)}`, xo + (right ? -10 : 10), box.t - 4);
  }, $("#t-tip"));

  $("#t-n").addEventListener("change", runTest);
  $("#t-seed").addEventListener("change", runTest);
  $("#t-reroll").onclick = () => { $("#t-seed").value = (+$("#t-seed").value || 0) + 1; runTest(); };

  /* ------------------------------------------------------------------
     16 · Conclusiones (tabla de monte_carlo.py: 20 000 simulaciones, semilla 42)
     ------------------------------------------------------------------ */
  const S = DATA.summary || [];
  $("#c-kicker").textContent = `${fmt(FIGHTS.length)} peleas · ${DATA.first_date.slice(0, 4)}–${DATA.last_date.slice(0, 4)}`;
  makeChart($("#c-canvas"), (ch) => {
    const { ctx, w, h } = ch;
    if (!S.length) return;
    const box = { l: 150, r: w - 150, t: 20, b: h - 58 };
    const lo = 0.5, hi = 0.95;
    const X = (v) => box.l + ((v - lo) / (hi - lo)) * (box.r - box.l);
    const rowH = (box.b - box.t) / S.length;
    const xt = [];
    for (let v = 0.5; v <= hi + 1e-9; v += 0.05) xt.push({ x: X(v), label: `${Math.round(100 * v)} %` });
    axes(ctx, box, { xticks: xt, yticks: [], xlab: "victorias de favoritos (% de las peleas del grupo)" });
    ctx.save();
    ctx.strokeStyle = "rgba(0,0,0,.06)";
    xt.forEach((t) => { ctx.beginPath(); ctx.moveTo(t.x, box.t); ctx.lineTo(t.x, box.b); ctx.stroke(); });
    ctx.restore();
    ctx.font = "600 18px Inter, sans-serif"; ctx.textBaseline = "middle";
    S.forEach((r, i) => {
      const y = box.t + rowH * (i + 0.5), n = r.fights;
      const a = X(r.simulated_95_low / n), b = X(r.simulated_95_high / n);
      const ok = r.observed_favorite_wins >= r.simulated_95_low && r.observed_favorite_wins <= r.simulated_95_high;
      if (r.band === "Todas") {
        ctx.strokeStyle = C.rule; ctx.setLineDash([4, 4]);
        ctx.beginPath(); ctx.moveTo(0, y - rowH / 2); ctx.lineTo(w, y - rowH / 2); ctx.stroke(); ctx.setLineDash([]);
      }
      ctx.fillStyle = C.ink; ctx.textAlign = "right"; ctx.fillText(r.band, box.l - 16, y);
      // rango simulado
      ctx.fillStyle = "rgba(47,102,144,.2)"; ctx.strokeStyle = C.blue; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.roundRect(a, y - 13, Math.max(2, b - a), 26, 6); ctx.fill(); ctx.stroke();
      // esperado
      const e = X(r.expected_wins / n);
      ctx.strokeStyle = C.blue; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(e, y - 18); ctx.lineTo(e, y + 18); ctx.stroke();
      // observado
      const o = X(r.observed_win_rate);
      ctx.beginPath(); ctx.arc(o, y, 10, 0, 7); ctx.fillStyle = C.rust; ctx.fill();
      ctx.lineWidth = 2.5; ctx.strokeStyle = "#fff"; ctx.stroke();
      // valor p
      ctx.textAlign = "left"; ctx.fillStyle = ok ? C.inkSoft : C.rust;
      ctx.font = `${ok ? 500 : 700} 17px Inter, sans-serif`;
      ctx.fillText(`p = ${r.p_value.toFixed(4)}`, box.r + 18, y);
      ctx.font = "600 18px Inter, sans-serif";
      ch.hits.push({ rect: true, x0: box.l, x1: box.r, y0: y - rowH / 2, y1: y + rowH / 2, ytop: y - 16,
        html: `<b>${r.band}</b> · ${fmt(n)} peleas<br>cuota media: ${pct(r.mean_market_probability)}<br>`
          + `observado: ${pct(r.observed_win_rate)} (${fmt(r.observed_favorite_wins)})<br>`
          + `rango 95 %: ${fmt(r.simulated_95_low)}–${fmt(r.simulated_95_high)} · p = ${r.p_value.toFixed(4)}` });
    });
  }, $("#c-tip"));

  const by = Object.fromEntries(S.map((r) => [r.band, r]));
  const note = (cls, title, body) => `<div class="note card ${cls}"><h3>${title}</h3><p>${body}</p></div>`;
  if (S.length) {
    const a = by["50–60 %"], b = by["60–70 %"], c = by["70–80 %"], d = by["80 % o más"], t = by["Todas"];
    $("#c-notes").innerHTML =
      note("ok", "Favoritos parejos: cuotas calibradas",
        `Con cuotas de 50–70 % la realidad cae dentro del rango simulado (p = ${a.p_value.toFixed(2)} y ${b.p_value.toFixed(2)}). Ahí el mercado acierta.`)
      + note("warn", "Favoritos claros: el mercado se queda corto",
        `Con 70–80 % ganaron ${pct(c.observed_win_rate)} frente al ${pct(c.mean_market_probability)} esperado (p = ${c.p_value.toFixed(4)}); con 80 % o más, ${pct(d.observed_win_rate)} frente a ${pct(d.mean_market_probability)}.`)
      + note("", "¿Y las sorpresas?",
        `Existen y son normales: el KO de Sharaf a Steveson pasa ~1 de cada 10 veces. Lo raro no es una sorpresa, sino <b>demasiadas o muy pocas</b>.`)
      + note("muted", "Con cautela",
        `Son varias pruebas a la vez (p global = ${t.p_value.toFixed(4)}), y se usan cuotas de apertura, no de cierre.`);
  }

  /* ------------------------------------------------------------------
     Inicio
     ------------------------------------------------------------------ */
  syncBand();
  runOne();
  runSample();
  addEventListener("load", () => { runTest(); });
})();
