// Small SVG line charts: hairline grid, 2px lines, one y axis, a safe band or limit lines, a cursor at the
// current year, and a crosshair tooltip on hover. Series colours are the validated categorical slots 1-3.
const NS = "http://www.w3.org/2000/svg";
const SLOTS = ["var(--series-1)", "var(--series-2)", "var(--series-3)"];

function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}

export function fmt(v, digits = 3) {
  if (v == null || Number.isNaN(v)) return "–";
  const a = Math.abs(v);
  if (a !== 0 && (a >= 1e6 || a < 1e-3)) return v.toExponential(Math.max(0, digits - 1)).replace("e+", "e");
  if (a >= 1000) return Math.round(v).toLocaleString("en");
  return Number(v.toPrecision(digits)).toString();
}

function niceTicks(lo, hi, count = 4) {
  const span = hi - lo || Math.abs(hi) || 1;
  const step0 = span / count;
  const mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= count + 0.5);
  const ticks = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) ticks.push(Number(v.toPrecision(12)));
  return ticks;
}

function thin(x, y, max = 700) {
  if (x.length <= max) return [x, y];
  const k = Math.ceil(x.length / max), xo = [], yo = [];
  for (let i = 0; i < x.length; i += k) { xo.push(x[i]); yo.push(y[i]); }
  xo.push(x[x.length - 1]); yo.push(y[y.length - 1]);
  return [xo, yo];
}

/**
 * series: [{name, x, y}]; options: title, sub, yFormat, xFormat, band [lo, hi], limits [{y, label}],
 * log (plot log10 of positive values), height, unit.
 */
export function lineChart({ title, sub, series, yFormat = fmt, xFormat = (v) => Math.round(v).toLocaleString("en"),
  band, limits = [], log = false, height = 170, unit = "", xName = "year" }) {
  const wrap = document.createElement("div");
  wrap.className = "chart";
  if (title) wrap.insertAdjacentHTML("beforeend", `<div class="ttl">${title}</div>`);
  if (sub) wrap.insertAdjacentHTML("beforeend", `<div class="sub">${sub}</div>`);
  const W = 420, H = height, m = { l: 48, r: 58, t: 8, b: 20 };
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title || "chart" });
  wrap.appendChild(svg);

  const tr = (v) => (log ? (v > 0 ? Math.log10(v) : null) : v);
  const data = series.map((s) => {
    const pts = [];
    for (let i = 0; i < s.x.length; i++) {
      const y = s.y[i] == null ? null : tr(s.y[i]);
      if (y != null && Number.isFinite(y)) pts.push([s.x[i], y, s.y[i]]);
    }
    return { ...s, pts };
  });
  const xs = data.flatMap((s) => s.pts.map((p) => p[0]));
  const ys = data.flatMap((s) => s.pts.map((p) => p[1]));
  for (const l of limits) ys.push(tr(l.y));
  if (band) ys.push(tr(band[0]), tr(band[1]));
  let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  if (y0 === y1) { y0 -= Math.abs(y0) * 0.05 || 1; y1 += Math.abs(y1) * 0.05 || 1; }
  const pad = (y1 - y0) * 0.06;
  y0 -= pad; y1 += pad;
  const X = (v) => m.l + ((v - x0) / (x1 - x0 || 1)) * (W - m.l - m.r);
  const Y = (v) => H - m.b - ((v - y0) / (y1 - y0)) * (H - m.t - m.b);

  const yTicks = log ? niceTicks(Math.ceil(y0), Math.floor(y1), 4).filter(Number.isInteger) : niceTicks(y0, y1, 4);
  for (const v of yTicks) {
    el("line", { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), stroke: "var(--grid)", "stroke-width": 1 }, svg);
    el("text", { x: m.l - 6, y: Y(v) + 3, "text-anchor": "end", class: "axis-text" }, svg).textContent = log ? `1e${v}` : yFormat(v);
  }
  el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, stroke: "var(--axis)", "stroke-width": 1 }, svg);
  for (const v of niceTicks(x0, x1, 4)) {
    el("text", { x: X(v), y: H - 5, "text-anchor": "middle", class: "axis-text" }, svg).textContent = xFormat(v);
  }
  if (band) {
    const b0 = Math.max(tr(band[0]), y0), b1 = Math.min(tr(band[1]), y1);
    if (b1 > b0) el("rect", { x: m.l, width: W - m.l - m.r, y: Y(b1), height: Y(b0) - Y(b1), fill: "var(--band)" }, svg);
  }
  for (const l of limits) {
    const y = tr(l.y);
    if (y < y0 || y > y1) continue;
    el("line", { x1: m.l, x2: W - m.r, y1: Y(y), y2: Y(y), stroke: l.color || "var(--critical)", "stroke-width": 1 }, svg);
    el("text", { x: W - m.r + 4, y: Y(y) + 3, class: "end-text" }, svg).textContent = l.label;
  }
  data.forEach((s, k) => {
    const [px, py] = thin(s.pts.map((p) => p[0]), s.pts.map((p) => p[1]));
    const dpath = px.map((x, i) => `${i ? "L" : "M"}${X(x).toFixed(1)},${Y(py[i]).toFixed(1)}`).join("");
    el("path", { d: dpath, fill: "none", stroke: s.color || SLOTS[k], "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    const last = s.pts[s.pts.length - 1];
    if (last && !limits.length) {
      el("circle", { cx: X(last[0]), cy: Y(last[1]), r: 4, fill: s.color || SLOTS[k], stroke: "var(--surface-1)", "stroke-width": 2 }, svg);
      if (data.length === 1) el("text", { x: X(last[0]) + 7, y: Y(last[1]) + 3, class: "end-text" }, svg).textContent = yFormat(last[2]) + unit;
    }
  });
  if (data.length > 1) {
    const lg = document.createElement("div");
    lg.className = "legend";
    lg.innerHTML = data.map((s, k) => `<span><i style="background:${s.color || SLOTS[k]}"></i>${s.name}</span>`).join("");
    wrap.appendChild(lg);
  }

  const cursor = el("line", { y1: m.t, y2: H - m.b, stroke: "var(--text-muted)", "stroke-width": 1, visibility: "hidden" }, svg);
  const hoverLine = el("line", { y1: m.t, y2: H - m.b, stroke: "var(--text-secondary)", "stroke-width": 1, visibility: "hidden" }, svg);
  const dots = data.map((s, k) => el("circle", { r: 4, fill: s.color || SLOTS[k], stroke: "var(--surface-1)", "stroke-width": 2, visibility: "hidden" }, svg));
  const hit = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "transparent" }, svg);
  const tip = document.getElementById("tooltip");
  const nearest = (pts, x) => {
    let lo = 0, hi = pts.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (pts[mid][0] <= x) lo = mid; else hi = mid; }
    return Math.abs(pts[lo][0] - x) < Math.abs(pts[hi][0] - x) ? pts[lo] : pts[hi];
  };
  hit.addEventListener("mousemove", (ev) => {
    const r = svg.getBoundingClientRect();
    const sx = ((ev.clientX - r.left) / r.width) * W;
    const x = x0 + ((sx - m.l) / (W - m.l - m.r)) * (x1 - x0);
    let rows = "";
    let xAt = x;
    data.forEach((s, k) => {
      if (!s.pts.length) return;
      const p = nearest(s.pts, x);
      xAt = p[0];
      dots[k].setAttribute("cx", X(p[0])); dots[k].setAttribute("cy", Y(p[1])); dots[k].setAttribute("visibility", "visible");
      rows += `<div class="row"><i style="background:${s.color || SLOTS[k]}"></i>${data.length > 1 ? s.name + ": " : ""}<b>${yFormat(p[2])}${unit}</b></div>`;
    });
    hoverLine.setAttribute("x1", X(xAt)); hoverLine.setAttribute("x2", X(xAt)); hoverLine.setAttribute("visibility", "visible");
    tip.innerHTML = `<div>${xName} ${xFormat(xAt)}</div>${rows}`;
    tip.hidden = false;
    tip.style.left = `${Math.min(ev.clientX + 14, window.innerWidth - 180)}px`;
    tip.style.top = `${ev.clientY + 12}px`;
  });
  hit.addEventListener("mouseleave", () => {
    tip.hidden = true;
    hoverLine.setAttribute("visibility", "hidden");
    dots.forEach((d) => d.setAttribute("visibility", "hidden"));
  });
  wrap.setCursor = (x) => {
    if (x == null || x < x0 || x > x1) { cursor.setAttribute("visibility", "hidden"); return; }
    cursor.setAttribute("x1", X(x)); cursor.setAttribute("x2", X(x)); cursor.setAttribute("visibility", "visible");
  };
  wrap.onPick = (fn) => hit.addEventListener("click", (ev) => {
    const r = svg.getBoundingClientRect();
    const sx = ((ev.clientX - r.left) / r.width) * W;
    fn(x0 + ((sx - m.l) / (W - m.l - m.r)) * (x1 - x0));
  });
  return wrap;
}
