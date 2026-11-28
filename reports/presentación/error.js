/* =====================================================================
   Diapositivas 8–9 · Control probabilístico del error
   8: ¿cuántas simulaciones necesito? (receta del TLC)
   9: cobertura de 100 intervalos de confianza para π
   ===================================================================== */
(() => {
  "use strict";
  const { $, C, fmt, makeChart, axes, niceStep } = window.MC;

  const Z = { 90: 1.6449, 95: 1.96, 99: 2.5758 };
  const SIG_PI = 4 * Math.sqrt((Math.PI / 4) * (1 - Math.PI / 4));

  function confSeg(el, initial, onChange) {
    el.innerHTML = [90, 95, 99].map((c) => `<button data-c="${c}"${c === initial ? ' class="on"' : ""}>${c} %</button>`).join("");
    el.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      el.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
      onChange(+b.dataset.c);
    });
  }

  /* ------------------------------------------------------------------
     8 · Calculadora de N
     ------------------------------------------------------------------ */
  const PROBLEMS = [
    { label: "El valor de π", sigma: SIG_PI },
    { label: "P(suma > 10) con dos dados", sigma: Math.sqrt((1 / 12) * (11 / 12)) },
    { label: "Sorpresa en Steveson vs. Sharaf", sigma: Math.sqrt(0.904 * 0.096) },
    { label: "Cualquier porcentaje (peor caso)", sigma: 0.5 },
  ];
  const EPS = [0.1, 0.05, 0.01, 0.005, 0.001];
  const ctrl = { conf: 95 };
  $("#ctrl-prob").innerHTML = PROBLEMS.map((p, i) => `<option value="${i}">${p.label}</option>`).join("");
  $("#ctrl-eps").innerHTML = EPS.map((e) => `<option value="${e}"${e === 0.01 ? " selected" : ""}>${String(e)}</option>`).join("");

  function calc() {
    const p = PROBLEMS[+$("#ctrl-prob").value], e = +$("#ctrl-eps").value, z = Z[ctrl.conf];
    const n = Math.ceil(((z * p.sigma) / e) ** 2), n2 = Math.ceil(((z * p.sigma) / (e / 2)) ** 2);
    $("#ctrl-n").textContent = fmt(n);
    $("#ctrl-n2").textContent = fmt(n2);
    $("#ctrl-read").innerHTML =
      `Con <b>${fmt(n)}</b> simulaciones, ${ctrl.conf} de cada 100 veces el resultado queda a menos de <b>${String(e)}</b> del valor real. `
      + `Si quisiéramos un dígito más de precisión, necesitaríamos <b>100 veces</b> más.`;
    curve.render();
  }

  // Campana del error: área central 1 − α y colas α/2
  const curve = makeChart($("#ctrl-canvas"), (ch) => {
    const { ctx, w, h } = ch, z = Z[ctrl.conf];
    const box = { l: 20, r: w - 20, t: 30, b: h - 30 };
    const X = (x) => box.l + ((x + 3.6) / 7.2) * (box.r - box.l);
    const pdf = (x) => Math.exp(-x * x / 2);
    const Y = (y) => box.b - y * (box.b - box.t);
    const area = (a, b, color) => {
      ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(X(a), box.b);
      for (let i = 0; i <= 120; i++) { const x = a + ((b - a) * i) / 120; ctx.lineTo(X(x), Y(pdf(x))); }
      ctx.lineTo(X(b), box.b); ctx.closePath(); ctx.fill();
    };
    area(-3.6, -z, "rgba(178,58,23,.28)");
    area(z, 3.6, "rgba(178,58,23,.28)");
    area(-z, z, "rgba(47,102,144,.22)");
    ctx.strokeStyle = C.ink; ctx.lineWidth = 2; ctx.beginPath();
    for (let i = 0; i <= 200; i++) { const x = -3.6 + (7.2 * i) / 200; i ? ctx.lineTo(X(x), Y(pdf(x))) : ctx.moveTo(X(x), Y(pdf(x))); }
    ctx.stroke();
    ctx.strokeStyle = "rgba(0,0,0,.4)"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(box.l, box.b); ctx.lineTo(box.r, box.b); ctx.stroke();
    ctx.setLineDash([5, 4]);
    [-z, z].forEach((v) => { ctx.beginPath(); ctx.moveTo(X(v), box.t - 4); ctx.lineTo(X(v), box.b); ctx.stroke(); });
    ctx.setLineDash([]);
    ctx.textAlign = "center"; ctx.textBaseline = "top"; ctx.fillStyle = C.inkSoft; ctx.font = "15px Inter, sans-serif";
    ctx.fillText("−ε", X(-z), box.b + 6); ctx.fillText("valor real", X(0), box.b + 6); ctx.fillText("+ε", X(z), box.b + 6);
    ctx.font = "700 19px Inter, sans-serif"; ctx.fillStyle = C.blue; ctx.textBaseline = "middle";
    ctx.fillText(`acertamos ${ctrl.conf} %`, X(0), Y(0.42));
    ctx.fillStyle = C.rust; ctx.font = "700 16px Inter, sans-serif";
    const tail = `fallamos ${fmt((100 - ctrl.conf) / 2, 1)} %`;
    ctx.fillText(tail, X(-z - 0.95), Y(0.3)); ctx.fillText(tail, X(z + 0.95), Y(0.3));
    ctx.fillStyle = C.inkSoft; ctx.font = "15px Inter, sans-serif"; ctx.textBaseline = "top";
    ctx.fillText("dónde caen los resultados si repetimos Monte Carlo muchas veces", X(0), 2);
  });

  confSeg($("#ctrl-conf"), 95, (c) => { ctrl.conf = c; calc(); });
  $("#ctrl-prob").addEventListener("change", calc);
  $("#ctrl-eps").addEventListener("change", calc);

  /* ------------------------------------------------------------------
     9 · Cobertura: 100 intervalos para π
     ------------------------------------------------------------------ */
  const cov = { conf: 95, rows: [], total: 0, hits: 0 };
  $("#cov-n").innerHTML = [100, 1000, 10000, 100000]
    .map((n) => `<option value="${n}"${n === 1000 ? " selected" : ""}>${fmt(n)}</option>`).join("");

  function runCover() {
    const N = +$("#cov-n").value, z = Z[cov.conf];
    cov.rows = [];
    for (let r = 0; r < 100; r++) {
      let k = 0;
      for (let i = 0; i < N; i++) { const u = Math.random() * 2 - 1, v = Math.random() * 2 - 1; if (u * u + v * v <= 1) k++; }
      const p = k / N, est = 4 * p, hw = z * 4 * Math.sqrt((p * (1 - p)) / N);
      cov.rows.push({ est, lo: est - hw, hi: est + hw, hit: est - hw <= Math.PI && Math.PI <= est + hw });
    }
    const hits = cov.rows.filter((r) => r.hit).length;
    cov.total += 100; cov.hits += hits;
    $("#cov-hit").textContent = hits;
    $("#cov-acc").textContent = `${fmt((100 * cov.hits) / cov.total, 1)} %`;
    $("#cov-acc-d").textContent = `de ${fmt(cov.total)} intervalos (meta: ${cov.conf} %)`;
    covChart.render();
  }
  function resetCover() { cov.total = 0; cov.hits = 0; runCover(); }

  const covChart = makeChart($("#cov-canvas"), (ch) => {
    const { ctx, w, h } = ch;
    if (!cov.rows.length) return;
    const N = +$("#cov-n").value, s = SIG_PI / Math.sqrt(N);
    const box = { l: 30, r: w - 20, t: 10, b: h - 56 };
    const x0 = Math.PI - 4.2 * s, x1 = Math.PI + 4.2 * s;
    const X = (v) => box.l + ((v - x0) / (x1 - x0)) * (box.r - box.l);
    const rowH = (box.b - box.t) / cov.rows.length;
    const step = niceStep((x1 - x0) / 6), dec = Math.max(0, -Math.floor(Math.log10(step)));
    const xt = [];
    for (let v = Math.ceil(x0 / step) * step; v <= x1; v += step) xt.push({ x: X(v), label: fmt(v, dec) });
    axes(ctx, box, { xticks: xt, yticks: [], xlab: `estimación de π con N = ${fmt(N)} puntos` });
    ctx.save(); ctx.beginPath(); ctx.rect(box.l, box.t, box.r - box.l, box.b - box.t); ctx.clip();
    cov.rows.forEach((r, i) => {
      const y = box.t + rowH * (i + 0.5);
      ctx.strokeStyle = r.hit ? C.blue : C.rust; ctx.lineWidth = r.hit ? 2 : 3.5;
      ctx.beginPath(); ctx.moveTo(X(r.lo), y); ctx.lineTo(X(r.hi), y); ctx.stroke();
      ctx.fillStyle = r.hit ? C.blue : C.rust;
      ctx.beginPath(); ctx.arc(X(r.est), y, r.hit ? 2.2 : 3.2, 0, 7); ctx.fill();
      ch.hits.push({ rect: true, x0: box.l, x1: box.r, y0: y - rowH / 2, y1: y + rowH / 2, ytop: y - 4,
        html: `Experimento ${i + 1}<br>π̂ = ${fmt(r.est, 4)}<br>[${fmt(r.lo, 4)}, ${fmt(r.hi, 4)}]<br>${r.hit ? "✓ atrapa a π" : "✗ no atrapa a π"}` });
    });
    ctx.restore();
    ctx.strokeStyle = C.ink; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(X(Math.PI), box.t - 4); ctx.lineTo(X(Math.PI), box.b); ctx.stroke();
  }, $("#cov-tip"));

  confSeg($("#cov-conf"), 95, (c) => { cov.conf = c; resetCover(); });
  $("#cov-n").addEventListener("change", resetCover);
  $("#cov-run").onclick = runCover;

  calc();
  runCover();
})();
