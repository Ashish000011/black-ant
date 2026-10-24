import { loadData, valueAt } from "./data.js";
import { Stage } from "./scene.js";
import { fmt } from "./charts.js";
import {
  compareTab, experiments, forcesTab, notesTab, orbitTab, plotsTab, safetyTab, structureTab, summaryTab, validationTab, validity,
} from "./panels.js";

const SPEEDS = [10, 50, 100, 250, 500];   // simulated years per second
const TABS = ["Summary", "Forces & momentum", "Orbit", "Structure", "Earth safety", "Plots", "Validation", "Model notes", "Compare & export"];
const $ = (id) => document.getElementById(id);

const store = {
  get(k, fallback) { try { return localStorage.getItem(k) ?? fallback; } catch { return fallback; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private window: keep defaults */ } },
};

async function main() {
  document.documentElement.dataset.theme = store.get("theme", "dark");
  let d;
  try {
    d = await loadData();
  } catch (err) {
    $("panel").innerHTML = `<p>Could not load the run data (${err.message}). Build it with <code>npm run data</code>.</p>`;
    return;
  }
  const end = d.milestones.end;
  const state = { t: 0, playing: false, speed: Number($("speed").value), tab: "Summary", exp: null, plot: "earth_a" };
  const stage = new Stage($("scene"), $("labels"), $("scale-note"), d);
  const ctx = { live: [], charts: [], t: () => state.t, goto: (t) => setTime(t) };

  // Enablers in the left column
  $("enablers").innerHTML = Object.entries(d.config.enablers.covers).map(([k, v]) => `<li><b>${k}</b>: ${v}</li>`).join("");
  $("validity").innerHTML = validity(d);

  // Experiments
  const exps = experiments(d);
  const expBox = $("experiments");
  for (const exp of exps) {
    const card = document.createElement("div");
    card.className = "exp";
    card.innerHTML = `<div class="letter">${exp.id}</div><div class="title">${exp.title}</div><button>Run</button><div class="q">${exp.q}</div>`;
    card.onclick = () => runExperiment(exp);
    exp.card = card;
    expBox.appendChild(card);
  }

  function runExperiment(exp, scroll = true) {
    state.exp = exp;
    exps.forEach((e) => e.card.classList.toggle("on", e === exp));
    setView(exp.view);
    setTime(exp.t);
    setPlaying(exp.play && exp.t < end);
    setTab(exp.tab === "Summary" ? "Summary" : exp.tab);
    if (scroll && window.matchMedia("(max-width: 900px)").matches) document.querySelector(".stage").scrollIntoView({ behavior: "smooth" });
  }

  // Tabs
  const tabBox = $("tabs");
  for (const name of TABS) {
    const b = document.createElement("button");
    b.textContent = name;
    b.setAttribute("role", "tab");
    b.onclick = () => setTab(name);
    tabBox.appendChild(b);
  }
  function setTab(name) {
    state.tab = name;
    tabBox.querySelectorAll("button").forEach((b) => {
      b.classList.toggle("on", b.textContent === name);
      b.setAttribute("aria-selected", b.textContent === name);
    });
    ctx.live = [];
    ctx.charts = [];
    const exp = state.exp || exps.find((e) => e.id === "B");
    const view = {
      "Summary": () => summaryTab(d, ctx, exp),
      "Forces & momentum": () => forcesTab(d, ctx),
      "Orbit": () => orbitTab(d, ctx),
      "Structure": () => structureTab(d, ctx),
      "Earth safety": () => safetyTab(d, ctx),
      "Plots": () => plotsTab(d, ctx, state),
      "Validation": () => validationTab(d),
      "Model notes": () => notesTab(d),
      "Compare & export": () => compareTab(d, ctx),
    }[name]();
    $("panel").replaceChildren(view);
    $("panel").scrollTop = 0;
    refreshPanel(true);
  }

  // Views and scale
  function setView(view) {
    stage.setView(view);
    $("live").style.display = view === "octo" ? "none" : "";
    $("views").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.view === view));
  }
  $("views").querySelectorAll("button").forEach((b) => (b.onclick = () => setView(b.dataset.view)));
  $("scales").querySelectorAll("button").forEach((b) => (b.onclick = () => {
    stage.setScale(b.dataset.scale);
    $("scales").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
  }));

  // Timeline
  const slider = $("time");
  slider.max = String(Math.round(end * 10));
  slider.oninput = () => { setPlaying(false); setTime(Number(slider.value) / 10); };
  const marks = [
    [d.milestones.marsCrosses21, "Mars crosses Jupiter's 2:1", "2:1"],
    [d.milestones.marsParks, "Mars parks", "Mars parks"],
    [d.milestones.beltEntry, "Earth enters the belt", "Belt"],
    [d.milestones.earthArrives, "Earth arrives", "Arrives"],
  ].filter(([t]) => t != null);
  $("marks").innerHTML = marks.map(([t, text, short], i) => {
    const x = (t / end) * 100;
    return `<span class="mark${x > 85 ? " right" : ""}" style="left:${x}%;top:${(i % 3) * 12}px" data-t="${t}" title="year ${Math.round(t).toLocaleString("en")}"><span class="long">${text}</span><span class="short">${short}</span></span>`;
  }).join("");
  $("marks").querySelectorAll(".mark").forEach((m) => (m.onclick = () => { setPlaying(false); setTime(Number(m.dataset.t)); }));

  function setTime(t) {
    state.t = Math.max(0, Math.min(end, t));
    slider.value = String(Math.round(state.t * 10));
    stage.update(state.t);
    $("year").textContent = `year ${Math.round(state.t).toLocaleString("en")}`;
    $("clock-note").textContent = state.t >= d.milestones.earthArrives ? "Earth at its new orbit" : "";
    refreshPanel();
  }

  // Playback
  function setPlaying(on) {
    state.playing = on;
    $("play").textContent = on ? "Pause" : "Play";
  }
  $("play").onclick = () => {
    if (!state.playing && state.t >= end) setTime(0);
    setPlaying(!state.playing);
  };
  $("reset").onclick = () => { setPlaying(false); setTime(0); };
  const showSpeed = () => ($("speed-label").textContent = `${SPEEDS[state.speed]} yr/s`);
  $("speed").oninput = () => { state.speed = Number($("speed").value); showSpeed(); };
  showSpeed();
  $("theme").onclick = () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    store.set("theme", next);
  };
  $("results-toggle").onclick = () => document.querySelector(".right").scrollIntoView({ behavior: "smooth" });

  // Live readout on the canvas and in the open tab, throttled to a few times a second.
  let lastPanel = 0;
  function refreshPanel(force = false) {
    const now = performance.now();
    if (!force && now - lastPanel < 200) return;
    lastPanel = now;
    for (const f of ctx.live) f(state.t);
    for (const c of ctx.charts) c.setCursor?.(state.t);
    const t = state.t;
    $("live").innerHTML = [
      ["Earth orbit", `${valueAt(d, "earth_a", t).toFixed(3)} AU`],
      ["Mars orbit", `${valueAt(d, "mars_a", t).toFixed(3)} AU`],
      ["Beam power", `${fmt(valueAt(d, "beam_w", t), 2)} W`],
      ["Temperature", `${valueAt(d, "temperature_k", t).toFixed(1)} K`],
      ["Sunlight", `${(valueAt(d, "sunlight_share", t) * 100).toFixed(1)}% of today`],
    ].map(([k, v]) => `<span>${k}</span><span>${v}</span>`).join("");
  }

  let last = performance.now();
  function frame(now) {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    if (state.playing) {
      const next = state.t + dt * SPEEDS[state.speed];
      if (next >= end) { setTime(end); setPlaying(false); } else setTime(next);
    }
    stage.render(now);
    requestAnimationFrame(frame);
  }

  const first = exps.find((e) => e.id === (new URLSearchParams(location.search).get("exp") || "B")) || exps.find((e) => e.id === "B");
  runExperiment(first, false);
  setPlaying(false);
  // ?capture: no clock of its own; a script steps it frame by frame (out/pw/video.mjs makes the demo video).
  if (new URLSearchParams(location.search).has("capture")) {
    window.bench = {
      run: (id) => { runExperiment(exps.find((e) => e.id === id), false); setPlaying(false); },
      view: setView, time: setTime, tab: setTab,
      scale: (s) => $("scales").querySelector(`[data-scale="${s}"]`).click(),
      orbit: (deg) => stage.orbit(deg),
      caption: (text) => { $("caption").hidden = !text; $("caption").textContent = text || ""; },
      frame: (ms) => { stage.render(ms); refreshPanel(true); },
    };
  } else requestAnimationFrame(frame);
}

main();
