import { loadData, valueAt } from "./data.js";
import { noStage, Stage } from "./scene.js";
import { fmt } from "./charts.js";
import { makeModel } from "./estimates.js";
import {
  compareTab, experiments, forcesTab, notesTab, orbitTab, plotsTab, safetyTab, structureTab, summaryTab, validationTab, validity,
} from "./panels.js";
import { dataPanel, modelPanel, outliner, store } from "./studio.js";

const SPEEDS = [10, 50, 100, 250, 500];   // simulated years per second
const TABS = ["Summary", "Forces & momentum", "Orbit", "Structure", "Earth safety", "Plots", "Validation", "Model notes", "Compare & export"];
const VIEW_NAMES = { system: "Solar system", earth: "Earth tow", mars: "Mars tow", octo: "Octo-Earth", top: "Top view" };
const $ = (id) => document.getElementById(id);

async function main() {
  document.documentElement.dataset.theme = store.get("theme", "dark");
  let d;
  try {
    d = await loadData();
  } catch (err) {
    $("data").innerHTML = `<p style="padding:12px">Could not load the run data (${err.message}). Build it with <code>npm run data</code>.</p>`;
    return;
  }
  const end = d.milestones.end;
  const model = makeModel(d);
  const night = d.config.night;
  const earthTow = d.config.tows.find((t) => t.target === "earth");
  const state = { t: 0, playing: false, speed: 3, tab: "Summary", exp: null, plot: "earth_a", lastView: "system" };
  // The what-if settings behind the left panel's sliders. The run itself never changes.
  const whatIf = {
    target: d.config.arrival.target_au, massKg: earthTow.asteroid_mass_kg, distKm: earthTow.distance_km,
    sunMode: "run", sunSats: Math.round(model.sunAreaNeeded(d.config.arrival.target_au) / night.sunlight_satellite_unit_km2 / 100) * 100,
    moonMode: "auto", moonPanels: Math.round(model.moonAreaFor(night.full_moon_lux_today, d.config.arrival.target_au) / night.moon_reflector_unit_km2),
    phaseDeg: 0,
  };
  let stage;
  try {
    stage = new Stage($("scene"), $("labels"), $("scale-note"), d);
  } catch {
    stage = noStage(d, $("scale-note"));
  }
  const ctx = { live: [], charts: [], t: () => state.t, goto: (t) => setTime(t) };
  const exps = experiments(d);

  // Panels
  const left = modelPanel(d, model, {
    whatIf, exps, speeds: SPEEDS, state, runExperiment: (exp) => runExperiment(exp),
    setSpeed: (i) => { state.speed = i; }, onChange: () => { stage.setWhatIf(whatIf.target); refreshPanel(true); },
  });
  $("model").replaceChildren(left.el);
  const scene = outliner(d, stage.bodyList, {
    focus: (id) => {
      if (stage.view !== "system" && stage.view !== "top") setView("system");
      stage.focus(id);
    },
  });
  $("outliner").replaceChildren(scene.el);
  $("outliner").classList.toggle("closed", !scene.open);
  const right = dataPanel(d, model);
  $("data").replaceChildren(right.el);
  $("validity").innerHTML = validity(d);

  function runExperiment(exp, scroll = true) {
    state.exp = exp;
    left.markExperiment(exp);
    setView(exp.view);
    setTime(exp.t);
    setPlaying(exp.play && exp.t < end);
    setTab(exp.tab);
    if (scroll && window.matchMedia("(max-width: 900px)").matches) $("viewport").scrollIntoView({ behavior: "smooth" });
  }

  // Results tabs, inside the right panel
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
    refreshPanel(true);
  }

  // Views: the workspace tabs, and the top view's button in the bottom-right corner
  function setView(view) {
    if (view !== "top") state.lastView = view;
    stage.setView(view);
    const top = view === "top";
    $("views").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.view === view));
    $("top-view").classList.toggle("on", top);
    $("top-view").setAttribute("aria-pressed", top);
    $("top-zoom").hidden = !top;
    refreshPanel(true);
  }
  const toggleTop = () => setView(stage.view === "top" ? state.lastView : "top");
  $("views").querySelectorAll("button").forEach((b) => (b.onclick = () => setView(b.dataset.view)));
  $("top-view").onclick = toggleTop;
  $("top-zoom").querySelectorAll("button").forEach((b) => (b.onclick = () => {
    stage.setTopZoom(b.dataset.z);
    $("top-zoom").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
  }));
  $("scales").querySelectorAll("button").forEach((b) => (b.onclick = () => {
    stage.setScale(b.dataset.scale);
    $("scales").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    refreshPanel(true);
  }));

  // Floating panels: T and N, as in Blender
  function toggleDock(side, show) {
    const dock = $(`dock-${side}`);
    const on = show ?? dock.classList.contains("hidden");
    dock.classList.toggle("hidden", !on);
    $(`toggle-${side}`).classList.toggle("on", on);
    store.set(`dock:${side}`, on ? "1" : "0");
  }
  for (const side of ["left", "right"]) {
    toggleDock(side, store.get(`dock:${side}`, "1") === "1");
    $(`toggle-${side}`).onclick = () => toggleDock(side);
  }

  // Timeline
  const slider = $("time"), yearInput = $("year-input");
  slider.max = String(Math.round(end * 10));
  yearInput.max = String(Math.floor(end));
  slider.oninput = () => { setPlaying(false); setTime(Number(slider.value) / 10); };
  yearInput.onchange = () => { setPlaying(false); setTime(Number(yearInput.value)); };
  const marks = [
    [d.milestones.marsCrosses21, "Mars crosses Jupiter's 2:1", "2:1"],
    [d.milestones.marsParks, "Mars parks", "Mars parks"],
    [d.milestones.beltEntry, "Earth enters the belt", "Belt"],
    [d.milestones.earthArrives, "Earth arrives", "Arrives"],
  ].filter(([t]) => t != null);
  $("marks").innerHTML = marks.map(([t, text, short], i) => {
    const x = (t / end) * 100;
    return `<span class="mark${x > 85 ? " right" : ""}" style="left:${x}%;top:${(i % 2) * 12}px" data-t="${t}" title="year ${Math.round(t).toLocaleString("en")}"><span class="long">${text}</span><span class="short">${short}</span></span>`;
  }).join("");
  $("marks").querySelectorAll(".mark").forEach((m) => (m.onclick = () => { setPlaying(false); setTime(Number(m.dataset.t)); }));

  function setTime(t) {
    state.t = Math.max(0, Math.min(end, t));
    slider.value = String(Math.round(state.t * 10));
    if (document.activeElement !== yearInput) yearInput.value = String(Math.round(state.t));
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
  const togglePlay = () => {
    if (!state.playing && state.t >= end) setTime(0);
    setPlaying(!state.playing);
  };
  $("play").onclick = togglePlay;
  $("reset").onclick = () => { setPlaying(false); setTime(0); };
  $("to-end").onclick = () => { setPlaying(false); setTime(end); };
  $("theme").onclick = () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    store.set("theme", next);
  };

  // Keys, as in Blender: Space plays, T and N toggle the panels, 7 is the top view, Home resets the camera.
  document.addEventListener("keydown", (e) => {
    const tag = e.target.tagName;
    if (e.ctrlKey || e.metaKey || e.altKey || ["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
    if (e.code === "Space" && tag !== "BUTTON") { e.preventDefault(); togglePlay(); }
    else if (e.key === "t" || e.key === "T") toggleDock("left");
    else if (e.key === "n" || e.key === "N") toggleDock("right");
    else if (e.key === "7" || e.code === "Numpad7") toggleTop();
    else if (e.key === "Home") stage.resetCamera();
  });

  // Everything that follows the clock or the sliders, throttled to a few times a second; a skipped update runs
  // once the wait is over, so the panels never stay on an old year.
  let lastPanel = 0, pending = 0;
  function refreshPanel(force = false) {
    const now = performance.now();
    clearTimeout(pending);
    if (!force && now - lastPanel < 200) {
      pending = setTimeout(() => refreshPanel(true), 200 - (now - lastPanel));
      return;
    }
    lastPanel = now;
    const t = state.t;
    const s = model.state(t, whatIf);
    stage.setReflectors({ sunKm2: s.sunArea, moonKm2: s.moonArea, sunSats: s.sunSats, moonPanels: s.moonPanels });
    left.update(t, s);
    scene.update(t, s);
    right.update(t, s);
    for (const f of ctx.live) f(t);
    for (const c of ctx.charts) c.setCursor?.(t);
    $("hud").innerHTML = [
      `<b>${VIEW_NAMES[stage.view]}</b>`, stage.scale === "vis" ? "Visualisation" : "True scale",
      `Earth ${s.a.toFixed(3)} AU`, `beam ${fmt(valueAt(d, "beam_w", t), 2)} W`,
      `${s.sunEst ? "≈" : ""}${s.temp.toFixed(1)} K`, `${s.sunEst ? "≈" : ""}${(s.share * 100).toFixed(1)}% sunlight`,
    ].map((x) => `<span>${x}</span>`).join("");
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
  // ?capture: no clock of its own; a script steps it frame by frame (scripts/video.mjs makes the demo video).
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
