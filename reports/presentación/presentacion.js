/* =====================================================================
   Método de Monte Carlo — lógica de la presentación y demos interactivas
   ===================================================================== */
(() => {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const C = {
    rust: css("--rust"), blue: css("--blue"), blueSoft: css("--blue-soft"),
    ink: css("--ink"), inkSoft: css("--ink-soft"), rule: css("--rule"), gold: css("--gold"),
  };
  const fmt = (x, d = 0) => x.toLocaleString("es-MX", { minimumFractionDigits: d, maximumFractionDigits: d });

  /* ------------------------------------------------------------------
     Escalado del escenario 1600×900 a la ventana
     ------------------------------------------------------------------ */
  const stage = $("#stage");
  let SCALE = 1;
  function fit() {
    SCALE = Math.min(innerWidth / 1600, innerHeight / 900);
    stage.style.transform = `translate(-50%, -50%) scale(${SCALE})`;
    charts.forEach((c) => c.resize());
  }

  /* ------------------------------------------------------------------
     Navegación con fragmentos
     ------------------------------------------------------------------ */
  const slides = $$(".slide");
  let cur = 0;

  function show(i, { revealAll = false } = {}) {
    cur = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach((s, k) => {
      s.classList.toggle("active", k === cur);
      s.classList.toggle("past", k < cur);
    });
    const frags = $$(".frag", slides[cur]);
    frags.forEach((f) => f.classList.toggle("shown", revealAll));
    $("#progress").style.width = `${((cur + 1) / slides.length) * 100}%`;
    $("#counter").textContent = `${cur + 1} / ${slides.length}`;
    history.replaceState(null, "", `#${cur + 1}`);
    document.title = `${slides[cur].dataset.title} · Método de Monte Carlo`;
    charts.forEach((c) => c.resize());
  }
  function next() {
    const hidden = $$(".frag:not(.shown)", slides[cur]);
    if (hidden.length) hidden[0].classList.add("shown");
    else if (cur < slides.length - 1) show(cur + 1);
  }
  function prev() {
    const shown = $$(".frag.shown", slides[cur]);
    if (shown.length) shown[shown.length - 1].classList.remove("shown");
    else if (cur > 0) show(cur - 1, { revealAll: true });
  }
  function toggleFS() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
    else document.exitFullscreen?.();
  }

  addEventListener("keydown", (e) => {
    if (e.target.matches("input, select")) return;
    const k = e.key;
    if (["ArrowRight", "PageDown", " ", "Enter"].includes(k)) { e.preventDefault(); next(); }
    else if (["ArrowLeft", "PageUp", "Backspace"].includes(k)) { e.preventDefault(); prev(); }
    else if (k === "Home") show(0);
    else if (k === "End") show(slides.length - 1, { revealAll: true });
    else if (k === "f" || k === "F") toggleFS();
    else if (k === "?") $("#help").classList.toggle("on");
    else if (k === "Escape") $("#help").classList.remove("on");
  });
  $("#next").onclick = next;
  $("#prev").onclick = prev;
  $("#fs").onclick = toggleFS;
  $("#help").onclick = () => $("#help").classList.remove("on");
  // Los botones no deben quedarse con el foco (si no, Espacio los volvería a pulsar)
  document.addEventListener("click", (e) => { if (e.target.closest("button")) e.target.closest("button").blur(); });

  /* ------------------------------------------------------------------
     Utilidades de gráficas (canvas nítido dentro del escenario escalado)
     ------------------------------------------------------------------ */
  const charts = [];
  function makeChart(canvas, draw, tipEl) {
    const ctx = canvas.getContext("2d");
    const ch = { canvas, ctx, w: 0, h: 0, hits: [], tip: tipEl, draw };
    ch.resize = () => {
      const w = canvas.offsetWidth, h = canvas.offsetHeight;
      if (!w || !h) return;
      const r = (window.devicePixelRatio || 1) * SCALE;
      canvas.width = Math.round(w * r); canvas.height = Math.round(h * r);
      ctx.setTransform(r, 0, 0, r, 0, 0);
      ch.w = w; ch.h = h;
      ch.render();
    };
    ch.render = () => { if (!ch.w) return; ctx.clearRect(0, 0, ch.w, ch.h); ch.hits = []; draw(ch); };
    if (tipEl) {
      canvas.addEventListener("mousemove", (e) => {
        const b = canvas.getBoundingClientRect();
        const x = (e.clientX - b.left) / SCALE, y = (e.clientY - b.top) / SCALE;
        let best = null, bd = Infinity;
        for (const h of ch.hits) {
          const d = h.rect
            ? (x >= h.x0 && x <= h.x1 && (h.y0 == null || (y >= h.y0 && y <= h.y1)) ? 0 : Infinity)
            : Math.hypot(h.x - x, h.y - y);
          if (d < bd && d < (h.rect ? 1 : 14)) { bd = d; best = h; }
        }
        if (best) {
          tipEl.innerHTML = best.html;
          tipEl.style.left = `${best.rect ? (best.x0 + best.x1) / 2 : best.x}px`;
          tipEl.style.top = `${best.rect ? Math.max(best.ytop, 30) : best.y}px`;
          tipEl.classList.add("on");
        } else tipEl.classList.remove("on");
      });
      canvas.addEventListener("mouseleave", () => tipEl.classList.remove("on"));
    }
    charts.push(ch);
    return ch;
  }

  function axes(ctx, box, { xticks, yticks, xlab, ylab }) {
    ctx.save();
    ctx.font = "15px Inter, sans-serif";
    ctx.fillStyle = C.inkSoft;
    ctx.strokeStyle = "rgba(0,0,0,.08)";
    ctx.lineWidth = 1;
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    for (const t of yticks) {
      ctx.beginPath(); ctx.moveTo(box.l, t.y); ctx.lineTo(box.r, t.y); ctx.stroke();
      ctx.fillText(t.label, box.l - 8, t.y);
    }
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    for (const t of xticks) ctx.fillText(t.label, t.x, box.b + 8);
    ctx.strokeStyle = "rgba(0,0,0,.35)";
    ctx.beginPath(); ctx.moveTo(box.l, box.b); ctx.lineTo(box.r, box.b); ctx.stroke();
    if (xlab) { ctx.fillText(xlab, (box.l + box.r) / 2, box.b + 30); }
    if (ylab) {
      ctx.save(); ctx.translate(box.l - 62, (box.t + box.b) / 2); ctx.rotate(-Math.PI / 2);
      ctx.textBaseline = "middle"; ctx.fillText(ylab, 0, 0); ctx.restore();
    }
    ctx.restore();
  }

  function roundedBar(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h);
    ctx.beginPath();
    ctx.moveTo(x, y + h);
    ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h); ctx.closePath(); ctx.fill();
  }

  /* ------------------------------------------------------------------
     3 · Teorema del Límite Central
     ------------------------------------------------------------------ */
  const DISTS = {
    unif: { mu: 0.5, var: 1 / 12, lo: 0, hi: 1, step: 0, draw: () => Math.random() },
    exp: { mu: 1, var: 1, lo: 0, hi: Infinity, step: 0, draw: () => -Math.log(1 - Math.random()) },
    dado: { mu: 3.5, var: 35 / 12, lo: 1, hi: 6, step: 1, draw: () => 1 + Math.floor(Math.random() * 6) },
    bern: { mu: 0.1, var: 0.09, lo: 0, hi: 1, step: 1, draw: () => (Math.random() < 0.1 ? 1 : 0) },
  };
  const clt = { means: [], dist: "exp", n: 5 };

  function runCLT() {
    const d = DISTS[clt.dist], n = clt.n, M = 5000;
    clt.means = new Float64Array(M);
    for (let m = 0; m < M; m++) {
      let s = 0;
      for (let i = 0; i < n; i++) s += d.draw();
      clt.means[m] = s / n;
    }
    cltChart.render();
    const mean = clt.means.reduce((a, b) => a + b, 0) / M;
    const sd = Math.sqrt(clt.means.reduce((a, b) => a + (b - mean) ** 2, 0) / (M - 1));
    $("#clt-read").innerHTML =
      `Media de las medias: <b>${fmt(mean, 3)}</b> (μ = ${fmt(d.mu, 3)}) &nbsp;·&nbsp; ` +
      `Desv. obs.: <b>${fmt(sd, 4)}</b> · σ/√n = <b>${fmt(Math.sqrt(d.var / n), 4)}</b>`;
  }

  const cltChart = makeChart($("#clt-canvas"), (ch) => {
    const { ctx, w, h } = ch;
    if (!clt.means.length) return;
    const d = DISTS[clt.dist], n = clt.n, s = Math.sqrt(d.var / n);
    let lo = Math.max(d.lo, d.mu - 4 * s), hi = Math.min(d.hi, d.mu + 4.5 * s);
    // Para distribuciones discretas la media vive en una retícula de paso step/n
    let bw, edges0;
    const lat = d.step / n;
    if (lat && (hi - lo) / lat <= 70) {
      bw = lat; lo = Math.round(lo / lat) * lat - lat / 2; hi = Math.round(hi / lat) * lat + lat / 2;
    } else { const k = 42; bw = (hi - lo) / k; }
    edges0 = lo;
    const nb = Math.max(1, Math.round((hi - lo) / bw));
    const counts = new Array(nb).fill(0);
    for (const m of clt.means) {
      const b = Math.floor((m - edges0) / bw);
      if (b >= 0 && b < nb) counts[b]++;
    }
    const M = clt.means.length;
    const dens = counts.map((c) => c / (M * bw));
    const pdf = (x) => Math.exp(-0.5 * ((x - d.mu) / s) ** 2) / (s * Math.sqrt(2 * Math.PI));
    const ymax = Math.max(...dens, pdf(d.mu)) * 1.08;
    const box = { l: 78, r: w - 16, t: 10, b: h - 58 };
    const X = (x) => box.l + ((x - lo) / (hi - lo)) * (box.r - box.l);
    const Y = (y) => box.b - (y / ymax) * (box.b - box.t);

    const yt = [], xt = [];
    const ystep = niceStep(ymax / 4);
    for (let v = 0; v <= ymax; v += ystep) yt.push({ y: Y(v), label: fmt(v, ystep < 1 ? (ystep < 0.1 ? 2 : 1) : 0) });
    const xstep = niceStep((hi - lo) / 6);
    for (let v = Math.ceil(lo / xstep) * xstep; v <= hi; v += xstep) xt.push({ x: X(v), label: fmt(v, xstep < 1 ? (xstep < 0.1 ? 2 : 1) : 0) });
    axes(ctx, box, { xticks: xt, yticks: yt, xlab: "media muestral  X̄ₙ", ylab: "densidad" });

    ctx.fillStyle = C.blue;
    const gap = 2;
    counts.forEach((c, i) => {
      const x0 = X(edges0 + i * bw), x1 = X(edges0 + (i + 1) * bw);
      const y = Y(dens[i]);
      if (c > 0) roundedBar(ctx, x0 + gap / 2, y, Math.max(1, x1 - x0 - gap), box.b - y, 4);
      ch.hits.push({
        rect: true, x0, x1, ytop: y,
        html: `X̄ ∈ [${fmt(edges0 + i * bw, 3)}, ${fmt(edges0 + (i + 1) * bw, 3)})<br><b>${fmt(c)}</b> medias (${fmt((100 * c) / M, 1)} %)`,
      });
    });
    ctx.strokeStyle = C.rust; ctx.lineWidth = 3; ctx.beginPath();
    for (let i = 0; i <= 300; i++) {
      const x = lo + ((hi - lo) * i) / 300;
      i ? ctx.lineTo(X(x), Y(pdf(x))) : ctx.moveTo(X(x), Y(pdf(x)));
    }
    ctx.stroke();
  }, $("#clt-tip"));

  function niceStep(raw) {
    const p = 10 ** Math.floor(Math.log10(raw)), f = raw / p;
    return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p;
  }

  $("#clt-n").addEventListener("input", (e) => { clt.n = +e.target.value; $("#clt-n-lbl").textContent = clt.n; runCLT(); });
  $("#clt-dist").addEventListener("change", (e) => { clt.dist = e.target.value; runCLT(); });
  $("#clt-run").onclick = runCLT;

  /* ------------------------------------------------------------------
     7 · Convergencia σ/√N (log–log)
     ------------------------------------------------------------------ */
  const P_IN = Math.PI / 4, SIG_PI = 4 * Math.sqrt(P_IN * (1 - P_IN));
  const conv = { pts: [], running: false };
  const NS = []; for (let e = 1; e <= 5.001; e += 0.25) NS.push(Math.round(10 ** e));
  function piEstimate(N) {
    let k = 0;
    for (let i = 0; i < N; i++) { const u = Math.random() * 2 - 1, v = Math.random() * 2 - 1; if (u * u + v * v <= 1) k++; }
    return (4 * k) / N;
  }
  function runConv() {
    if (conv.running) return;
    conv.running = true; conv.pts = [];
    let i = 0;
    const step = () => {
      const N = NS[i];
      for (let r = 0; r < 30; r++) { const est = piEstimate(N); conv.pts.push({ N, est, err: Math.abs(est - Math.PI), jit: (Math.random() - 0.5) * 0.06 }); }
      convChart.render();
      if (++i < NS.length) requestAnimationFrame(step); else conv.running = false;
    };
    requestAnimationFrame(step);
  }
  const convChart = makeChart($("#conv-canvas"), (ch) => {
    const { ctx, w, h } = ch;
    const box = { l: 90, r: w - 20, t: 14, b: h - 60 };
    const lx0 = 0.8, lx1 = 5.2, ly0 = -4.5, ly1 = 0.8;
    const X = (N) => box.l + ((Math.log10(N) - lx0) / (lx1 - lx0)) * (box.r - box.l);
    const Y = (e) => box.b - ((Math.log10(Math.max(e, 10 ** ly0)) - ly0) / (ly1 - ly0)) * (box.b - box.t);
    const sup = ["⁰", "¹", "²", "³", "⁴", "⁵"];
    const xt = [1, 2, 3, 4, 5].map((e) => ({ x: X(10 ** e), label: `10${sup[e]}` }));
    const yt = [-4, -3, -2, -1, 0].map((e) => ({ y: Y(10 ** e), label: e === 0 ? "1" : `10⁻${sup[-e]}` }));
    axes(ctx, box, { xticks: xt, yticks: yt, xlab: "número de simulaciones N (escala log)", ylab: "|π̂ − π| (escala log)" });

    // puntos
    for (const p of conv.pts) {
      const x = X(p.N) + p.jit * (box.r - box.l) / (lx1 - lx0), y = Y(p.err);
      ctx.beginPath(); ctx.arc(x, y, 4.5, 0, 7);
      ctx.fillStyle = "rgba(47,102,144,.55)"; ctx.fill();
      ch.hits.push({ x, y, html: `N = <b>${fmt(p.N)}</b><br>π̂ = ${fmt(p.est, 5)}<br>|error| = ${p.err.toExponential(2)}` });
    }
    // línea teórica σ/√N
    ctx.strokeStyle = C.rust; ctx.lineWidth = 3; ctx.beginPath();
    ctx.moveTo(X(10 ** lx0), Y(SIG_PI / Math.sqrt(10 ** lx0)));
    ctx.lineTo(X(10 ** lx1), Y(SIG_PI / Math.sqrt(10 ** lx1)));
    ctx.stroke();
    // anotación ×100 → ÷10
    const a = 10 ** 2, b = 10 ** 4;
    const ya = Y(SIG_PI / Math.sqrt(a)), yb = Y(SIG_PI / Math.sqrt(b));
    ctx.save();
    ctx.strokeStyle = C.inkSoft; ctx.setLineDash([5, 5]); ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(X(a), ya - 40); ctx.lineTo(X(b), ya - 40); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(X(b) + 40, ya); ctx.lineTo(X(b) + 40, yb); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = C.ink; ctx.font = "600 18px Inter, sans-serif";
    ctx.textAlign = "center"; ctx.fillText("N × 100", (X(a) + X(b)) / 2, ya - 52);
    ctx.textAlign = "left"; ctx.fillText("error ÷ 10", X(b) + 50, (ya + yb) / 2);
    ctx.restore();
    if (!conv.pts.length) {
      ctx.fillStyle = C.inkSoft; ctx.font = "italic 22px Inter, sans-serif"; ctx.textAlign = "center";
      ctx.fillText("Pulsa «Correr» para lanzar 30 estimaciones de π por cada N", (box.l + box.r) / 2, box.t + 40);
    }
  }, $("#conv-tip"));
  $("#conv-run").onclick = runConv;
  $("#conv-clear").onclick = () => { conv.pts = []; convChart.render(); };

  /* ------------------------------------------------------------------
     Trayectoria de una estimación con banda IC 95 % (dados y π)
     ------------------------------------------------------------------ */
  // opts puede ser un objeto o una función que lo devuelve (para ejes que cambian).
  // funnel: true → la banda es el embudo ±hw alrededor del valor real (no del estimado).
  function traceDrawer(state, opts) {
    return (ch) => {
      const { truth, ylo, yhi, ylab, decimals, truthLabel, funnel = false, xlab = "N (escala log)",
              fmtY = (v) => fmt(v, decimals), lineColor = C.blue, truthColor = C.rust,
              bandColor = "rgba(47,102,144,.18)" } = typeof opts === "function" ? opts() : opts;
      const { ctx, w, h } = ch;
      const box = { l: 74, r: w - 18, t: 12, b: h - 50 };
      const H = state.hist;
      const nmax = Math.max(10, H.length ? H[H.length - 1].n : 10);
      const X = (n) => box.l + (Math.log10(n) / Math.log10(nmax)) * (box.r - box.l);
      const Y = (v) => box.b - ((v - ylo) / (yhi - ylo)) * (box.b - box.t);
      const xt = [];
      for (let e = 0; 10 ** e <= nmax; e++) xt.push({ x: X(10 ** e), label: fmt(10 ** e) });
      const ys = niceStep((yhi - ylo) / 4), yt = [];
      for (let v = Math.ceil(ylo / ys) * ys; v <= yhi + 1e-9; v += ys) yt.push({ y: Y(v), label: fmtY(v) });
      axes(ctx, box, { xticks: xt, yticks: yt, xlab, ylab });
      // valor verdadero
      ctx.strokeStyle = truthColor; ctx.lineWidth = 2.5; ctx.setLineDash([8, 6]);
      ctx.beginPath(); ctx.moveTo(box.l, Y(truth)); ctx.lineTo(box.r, Y(truth)); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = C.ink; ctx.font = "600 15px Inter, sans-serif"; ctx.textAlign = "left"; ctx.textBaseline = "top";
      ctx.fillText(truthLabel, box.l + 6, Y(truth) + 6);
      if (!H.length) return;
      ctx.save(); ctx.beginPath(); ctx.rect(box.l, box.t, box.r - box.l, box.b - box.t); ctx.clip();
      // banda IC
      const mid = (p) => (funnel ? truth : p.est);
      ctx.fillStyle = bandColor; ctx.beginPath();
      H.forEach((p, i) => (i ? ctx.lineTo(X(p.n), Y(mid(p) + p.hw)) : ctx.moveTo(X(p.n), Y(mid(p) + p.hw))));
      for (let i = H.length - 1; i >= 0; i--) ctx.lineTo(X(H[i].n), Y(mid(H[i]) - H[i].hw));
      ctx.closePath(); ctx.fill();
      // trayectoria
      ctx.strokeStyle = lineColor; ctx.lineWidth = 2; ctx.beginPath();
      H.forEach((p, i) => (i ? ctx.lineTo(X(p.n), Y(p.est)) : ctx.moveTo(X(p.n), Y(p.est))));
      ctx.stroke();
      const L = H[H.length - 1];
      ctx.beginPath(); ctx.arc(X(L.n), Y(L.est), 5, 0, 7); ctx.fillStyle = lineColor; ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = "#fff"; ctx.stroke();
      ctx.restore();
      for (const p of H) ch.hits.push({ x: X(p.n), y: Y(p.est), html: `N = <b>${fmt(p.n)}</b><br>estimación = ${fmtY(p.est)}<br>${funnel ? "embudo" : "IC"} 95 %: ±${fmtY(p.hw)}` });
    };
  }
  function pushHist(state, n, est, hw) {
    const H = state.hist, last = H[H.length - 1];
    if (!last || n < 200 || n >= last.n * 1.015) H.push({ n, est, hw });
  }

  /* ------------------------------------------------------------------
     8 · Dos dados: P(suma > 10)
     ------------------------------------------------------------------ */
  (function buildGrid() {
    const g = $("#grid36");
    g.innerHTML = '<div class="h"></div>' + [1, 2, 3, 4, 5, 6].map((j) => `<div class="h">${j}</div>`).join("");
    for (let i = 1; i <= 6; i++) {
      g.innerHTML += `<div class="h">${i}</div>`;
      for (let j = 1; j <= 6; j++) g.innerHTML += `<div class="c${i + j > 10 ? " hit" : ""}">${i + j}</div>`;
    }
  })();
  const PIPS = { 1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8] };
  function paintDie(el, v) {
    el.innerHTML = Array.from({ length: 9 }, (_, i) => `<i class="${PIPS[v].includes(i) ? "on" : ""}"></i>`).join("");
    el.classList.remove("roll"); void el.offsetWidth; el.classList.add("roll");
  }
  const dice = { n: 0, k: 0, hist: [] };
  const diceChart = makeChart($("#dice-canvas"), traceDrawer(dice, { truth: 1 / 12, ylo: 0, yhi: 0.3, ylab: "P̂(A)", decimals: 2, truthLabel: "1/12 ≈ 0.0833" }), $("#dice-tip"));
  function rollDice(times) {
    $("#dice-right").classList.add("dim");
    $("#dice-panel").classList.add("on");
    let a, b;
    for (let t = 0; t < times; t++) {
      a = 1 + Math.floor(Math.random() * 6); b = 1 + Math.floor(Math.random() * 6);
      dice.n++; if (a + b > 10) dice.k++;
      const p = dice.k / dice.n;
      pushHist(dice, dice.n, p, 1.96 * Math.sqrt((p * (1 - p)) / dice.n));
    }
    paintDie($("#d1"), a); paintDie($("#d2"), b);
    const sum = $("#dsum"); sum.textContent = `= ${a + b}${a + b > 10 ? "  ✓ A" : ""}`; sum.classList.toggle("hit", a + b > 10);
    const p = dice.k / dice.n, hw = 1.96 * Math.sqrt((p * (1 - p)) / dice.n);
    $("#dice-read").innerHTML = `Lanzamientos: <b>${fmt(dice.n)}</b> · Éxitos: <b>${fmt(dice.k)}</b> · ` +
      `\\(\\hat p\\) = <b>${fmt(p, 4)}</b> ± ${fmt(hw, 4)} &nbsp;(exacto 0.0833)`;
    renderMath($("#dice-read"));
    diceChart.resize();
  }
  $("#dice-1").onclick = () => rollDice(1);
  $("#dice-100").onclick = () => rollDice(100);
  $("#dice-10k").onclick = () => rollDice(10000);
  $("#dice-reset").onclick = () => {
    Object.assign(dice, { n: 0, k: 0, hist: [] });
    $("#dice-right").classList.remove("dim"); $("#dice-panel").classList.remove("on");
    diceChart.render();
  };

  /* ------------------------------------------------------------------
     9 · Estimación de π con puntos en el cuadrado
     ------------------------------------------------------------------ */
  const pi = { n: 0, k: 0, hist: [], pts: [], playing: false };
  const piBoard = makeChart($("#pi-canvas"), (ch) => {
    const { ctx, w, h } = ch, S = Math.min(w, h), pad = 10;
    const P = (u) => pad + ((u + 1) / 2) * (S - 2 * pad);
    ctx.fillStyle = "#fbfaf7"; ctx.fillRect(P(-1), P(-1), P(1) - P(-1), P(1) - P(-1));
    const r = pi.n < 3000 ? 3.2 : pi.n < 20000 ? 2 : 1.3;
    for (const [u, v, inside] of pi.pts) {
      ctx.fillStyle = inside ? C.blue : C.rust;
      ctx.beginPath(); ctx.arc(P(u), P(-v), r, 0, 7); ctx.fill();
    }
    ctx.strokeStyle = "rgba(0,0,0,.45)"; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.arc(P(0), P(0), (P(1) - P(-1)) / 2, 0, 7); ctx.stroke();
    ctx.strokeStyle = "rgba(0,0,0,.6)"; ctx.lineWidth = 1.5; ctx.strokeRect(P(-1), P(-1), P(1) - P(-1), P(1) - P(-1));
    ctx.strokeStyle = "rgba(0,0,0,.12)"; ctx.beginPath(); ctx.moveTo(P(0), P(-1)); ctx.lineTo(P(0), P(1)); ctx.moveTo(P(-1), P(0)); ctx.lineTo(P(1), P(0)); ctx.stroke();
    if (!pi.n) {
      ctx.fillStyle = C.inkSoft; ctx.font = "italic 22px Inter, sans-serif"; ctx.textAlign = "center";
      ctx.fillText("Lanza puntos al azar en el cuadrado", S / 2, S / 2);
    }
  });
  const piTrace = makeChart($("#pi-trace"), traceDrawer(pi, { truth: Math.PI, ylo: 2.6, yhi: 3.7, ylab: "π̂", decimals: 1, truthLabel: "π = 3.14159…" }), $("#pi-tip"));
  function addPi(m) {
    for (let t = 0; t < m; t++) {
      const u = Math.random() * 2 - 1, v = Math.random() * 2 - 1, inside = u * u + v * v <= 1;
      pi.n++; if (inside) pi.k++;
      if (pi.pts.length < 60000) pi.pts.push([u, v, inside]);
      const p = pi.k / pi.n;
      pushHist(pi, pi.n, 4 * p, 1.96 * 4 * Math.sqrt((p * (1 - p)) / pi.n));
    }
    const est = (4 * pi.k) / pi.n, hw = 1.96 * 4 * Math.sqrt(((pi.k / pi.n) * (1 - pi.k / pi.n)) / pi.n);
    $("#pi-est").textContent = fmt(est, 4);
    $("#pi-ci").textContent = `± ${fmt(hw, 4)}`;
    $("#pi-n").textContent = fmt(pi.n);
    $("#pi-in").textContent = fmt(pi.k);
    $("#pi-err").textContent = fmt(Math.abs(est - Math.PI), 4);
    piBoard.render(); piTrace.render();
  }
  $$(".s-pi [data-add]").forEach((b) => (b.onclick = () => addPi(+b.dataset.add)));
  $("#pi-play").onclick = () => {
    pi.playing = !pi.playing;
    $("#pi-play").textContent = pi.playing ? "❚❚ Pausa" : "▶ Animar";
    const tick = () => {
      if (!pi.playing) return;
      addPi(Math.max(5, Math.round(pi.n * 0.03)));
      if (pi.n >= 50000) { pi.playing = false; $("#pi-play").textContent = "▶ Animar"; return; }
      requestAnimationFrame(tick);
    };
    tick();
  };
  $("#pi-reset").onclick = () => {
    Object.assign(pi, { n: 0, k: 0, hist: [], pts: [], playing: false });
    $("#pi-play").textContent = "▶ Animar";
    ["#pi-est", "#pi-err"].forEach((s) => ($(s).textContent = "—"));
    $("#pi-ci").textContent = ""; $("#pi-n").textContent = "0"; $("#pi-in").textContent = "0";
    piBoard.render(); piTrace.render();
  };

  /* ------------------------------------------------------------------
     Matemáticas (KaTeX) e inicio
     ------------------------------------------------------------------ */
  function renderMath(el) {
    if (window.renderMathInElement) {
      renderMathInElement(el, {
        delimiters: [{ left: "$$", right: "$$", display: true }, { left: "\\(", right: "\\)", display: false }],
        throwOnError: false,
      });
    }
  }

  addEventListener("resize", fit);
  addEventListener("load", () => {
    renderMath(document.body);
    fit();
    runCLT();
    // Modo vista previa (index.html?todo#n): todo visible y demos ya corridas
    if (PREVIEW) { runConv(); rollDice(3000); addPi(1000); }
  });
  const PREVIEW = new URLSearchParams(location.search).has("todo");
  // Utilidades compartidas con ufc.js (diapositivas de MMA)
  window.MC = { $, $$, C, fmt, makeChart, axes, roundedBar, niceStep, traceDrawer, pushHist, renderMath, PREVIEW };
  fit();
  show((parseInt(location.hash.slice(1), 10) || 1) - 1, { revealAll: PREVIEW });
})();
