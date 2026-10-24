// The 3D views. Solar system: AU, heliocentric ecliptic. Earth tow and Mars tow: 1,000 km units in the planet's
// own frame, with the Sun towards the top of the screen and "ahead along the orbit" to the right.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { AU_KM, G, MASS, positionAt, towActive, towLocalAt, valueAt } from "./data.js";

const KM_AU = 1 / AU_KM;
const RADIUS_KM = { sun: 696000, earth: 6371, mars: 3389.5, jupiter: 69911, moon: 1737.4 };
// Visualisation sizes in the solar-system view (AU); distances are always true.
const VIS_AU = { sun: 0.09, earth: 0.05, mars: 0.04, jupiter: 0.12 };
const CLOSE_VIS = { planet: 6, moon: 6, rock: 30, mirror: 4 };
const HILL_KM_PER_AU = { earth: 1.5026e6, mars: 7.114e5 };

// Ecliptic (x, y, z) to three.js (x, z, -y): the ecliptic is the ground plane, its north pole is up.
const ecl = (p, s = 1) => new THREE.Vector3(p[0] * s, p[2] * s, -p[1] * s);
// Planet frame [out, ahead, up] (km) to three.js units of 1,000 km: ahead is +x, out is +z (towards the viewer).
const loc = (v) => new THREE.Vector3(v[1] / 1e3, v[2] / 1e3, v[0] / 1e3);

function hash3(x, y, z) {
  const s = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
  return s - Math.floor(s);
}
function noise3(x, y, z) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const xf = x - xi, yf = y - yi, zf = z - zi;
  const f = (t) => t * t * (3 - 2 * t);
  const u = f(xf), v = f(yf), w = f(zf);
  let out = 0;
  for (let dz = 0; dz < 2; dz++) for (let dy = 0; dy < 2; dy++) for (let dx = 0; dx < 2; dx++) {
    const h = hash3(xi + dx, yi + dy, zi + dz);
    out += h * (dx ? u : 1 - u) * (dy ? v : 1 - v) * (dz ? w : 1 - w);
  }
  return out;
}
function fbm(x, y, z) {
  let a = 0.5, f = 1, s = 0;
  for (let o = 0; o < 5; o++) { s += a * noise3(x * f, y * f, z * f); f *= 2; a *= 0.5; }
  return s;
}

// A procedural planet texture (the page loads no images): noise on the sphere, so there is no seam.
function planetTexture(kind) {
  const w = 512, h = 256;
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const g = c.getContext("2d");
  const img = g.createImageData(w, h);
  for (let j = 0; j < h; j++) {
    const lat = Math.PI / 2 - (j / h) * Math.PI;
    for (let i = 0; i < w; i++) {
      const lon = (i / w) * 2 * Math.PI;
      const x = Math.cos(lat) * Math.cos(lon), y = Math.cos(lat) * Math.sin(lon), z = Math.sin(lat);
      const n = fbm(x * 2.2 + 5, y * 2.2 + 1, z * 2.2 + 3);
      let r, gg, b;
      if (kind === "earth") {
        if (Math.abs(lat) > 1.22 + 0.1 * (n - 0.5)) { r = 235; gg = 240; b = 245; }
        else if (n > 0.53) { const k = (n - 0.53) * 4; r = 70 + 90 * k; gg = 110 + 40 * k; b = 50 + 20 * k; }
        else { const k = n / 0.53; r = 18 + 20 * k; gg = 60 + 50 * k; b = 130 + 60 * k; }
      } else if (kind === "mars") {
        const k = n; r = 150 + 80 * k; gg = 70 + 40 * k; b = 40 + 20 * k;
        if (Math.abs(lat) > 1.35) { r = 230; gg = 225; b = 220; }
      } else {
        const k = fbm(x * 9, y * 9, z * 9); r = 110 + 60 * k; gg = 105 + 50 * k; b = 100 + 40 * k;
      }
      const o = (j * w + i) * 4;
      img.data[o] = r; img.data[o + 1] = gg; img.data[o + 2] = b; img.data[o + 3] = 255;
    }
  }
  g.putImageData(img, 0, 0);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function glowTexture(inner = "rgba(255,230,160,1)") {
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const g = c.getContext("2d");
  const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, inner);
  grad.addColorStop(0.25, "rgba(255,200,90,0.45)");
  grad.addColorStop(1, "rgba(255,160,40,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}

function ringTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const g = c.getContext("2d");
  g.strokeStyle = "#ffffff";
  g.lineWidth = 5;
  g.beginPath(); g.arc(32, 32, 24, 0, 2 * Math.PI); g.stroke();
  return new THREE.CanvasTexture(c);
}

function stars(count = 1800, radius = 4000) {
  const pos = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const u = Math.random() * 2 - 1, th = Math.random() * 2 * Math.PI, s = Math.sqrt(1 - u * u);
    pos.set([radius * s * Math.cos(th), radius * u, radius * s * Math.sin(th)], i * 3);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  return new THREE.Points(geo, new THREE.PointsMaterial({ color: 0x9a978f, size: 1.2, sizeAttenuation: false }));
}

function circle(radius, color, { dashed = false, opacity = 1, segments = 256, dash = 0.06 } = {}) {
  const pts = [];
  for (let k = 0; k <= segments; k++) {
    const a = (k / segments) * 2 * Math.PI;
    pts.push(new THREE.Vector3(Math.cos(a), 0, Math.sin(a)));
  }
  const geo = new THREE.BufferGeometry().setFromPoints(pts);
  const mat = dashed
    ? new THREE.LineDashedMaterial({ color, dashSize: dash, gapSize: dash, transparent: true, opacity })
    : new THREE.LineBasicMaterial({ color, transparent: opacity < 1, opacity });
  const line = new THREE.Line(geo, mat);
  if (dashed) line.computeLineDistances();
  line.scale.setScalar(radius);
  return line;
}

function sphere(color, map = null, emissive = 0x000000) {
  return new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24),
    new THREE.MeshStandardMaterial({ color: map ? 0xffffff : color, map, roughness: 0.9, metalness: 0, emissive }));
}

function rock() {
  const geo = new THREE.IcosahedronGeometry(1, 3);
  const p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const v = new THREE.Vector3().fromBufferAttribute(p, i);
    v.multiplyScalar(0.75 + 0.45 * fbm(v.x * 1.7 + 9, v.y * 1.7, v.z * 1.7));
    p.setXYZ(i, v.x, v.y, v.z);
  }
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0x8f8a80, roughness: 1, flatShading: true }));
}

// A light beam: a thin glowing cylinder from a to b.
function beam(color = 0xffd27a) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 12, 1, true),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false }));
  m.setEnds = (a, b, radius) => {
    const mid = a.clone().add(b).multiplyScalar(0.5);
    const dir = b.clone().sub(a);
    m.position.copy(mid);
    m.scale.set(radius, dir.length(), radius);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
  };
  return m;
}

function trailLine(color, n = 400) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.9 }));
  line.frustumCulled = false;
  line.n = n;
  return line;
}

export class Stage {
  constructor(canvas, labelsEl, noteEl, data) {
    this.d = data;
    this.canvas = canvas;
    this.labelsEl = labelsEl;
    this.noteEl = noteEl;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.0005, 1e5);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.labels = { system: [], earth: [], mars: [] };
    this.scenes = { system: this.buildSystem(), earth: this.buildTowView("earth"), mars: this.buildTowView("mars") };
    this.poses = {
      system: { pos: new THREE.Vector3(0.8, 9.6, 8.2), target: new THREE.Vector3(0, 0, 0.4) },
      earth: { pos: new THREE.Vector3(200, 1000, 1260), target: new THREE.Vector3(200, 0, 160) },
      mars: { pos: new THREE.Vector3(120, 660, 820), target: new THREE.Vector3(120, 0, 110) },
    };
    this.view = "system";
    this.scale = "vis";
    this.t = 0;
    this.setView("system", true);
    this.setScale("vis");
    new ResizeObserver(() => this.resize()).observe(canvas.parentElement);
    this.resize();
  }

  label(view, text, at, cls = "") {
    const el = document.createElement("div");
    el.className = `lbl ${cls}`;
    this.labelsEl.appendChild(el);
    const item = { el, at, text, view };
    this.labels[view].push(item);
    return item;
  }

  buildSystem() {
    const d = this.d;
    const scene = new THREE.Scene();
    scene.add(stars());
    scene.add(new THREE.AmbientLight(0xffffff, 0.22));
    scene.add(new THREE.PointLight(0xfff2d8, 2.2, 0, 0));

    this.sun = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24), new THREE.MeshBasicMaterial({ color: 0xffd27a }));
    scene.add(this.sun);
    this.sunGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), blending: THREE.AdditiveBlending, depthWrite: false }));
    scene.add(this.sunGlow);

    const orbitColor = { earth: 0x2c5a8f, mars: 0x8a4a2c };
    for (const [name, pts] of Object.entries(d.journey.orbits)) {
      const geo = new THREE.BufferGeometry().setFromPoints(pts.map((p) => ecl(p)));
      scene.add(new THREE.Line(geo, new THREE.LineBasicMaterial({ color: orbitColor[name] ?? 0x4a4842 })));
    }
    scene.add(circle(2.7, 0x0ca30c, { dashed: true, dash: 0.05 }));
    scene.add(circle(3.64, 0xd95926, { dashed: true, dash: 0.05, opacity: 0.85 }));
    this.resonance = circle(3.278, 0xd03b3b, { dashed: true, dash: 0.02, opacity: 0.6 });
    scene.add(this.resonance);

    // The belt: an illustrative cloud between 2.1 and 3.3 AU (the run itself tracks 1,000 real orbits).
    const n = 5000, belt = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const r = 2.1 + 1.2 * Math.pow(Math.random(), 0.8), a = Math.random() * 2 * Math.PI;
      belt.set([r * Math.cos(a), (Math.random() - 0.5) * 0.12 * r, r * Math.sin(a)], i * 3);
    }
    const bg = new THREE.BufferGeometry();
    bg.setAttribute("position", new THREE.BufferAttribute(belt, 3));
    scene.add(new THREE.Points(bg, new THREE.PointsMaterial({ color: 0x7d786c, size: 1.4, sizeAttenuation: false })));

    this.bodies = {
      earth: sphere(0x3987e5, planetTexture("earth")),
      mars: sphere(0xc1440e, planetTexture("mars")),
      jupiter: sphere(0xc9a77c, planetTexture("jupiter")),
    };
    const ringTex = ringTexture();
    this.markers = {};
    for (const [k, m] of Object.entries(this.bodies)) {
      scene.add(m);
      const mk = new THREE.Sprite(new THREE.SpriteMaterial({ map: ringTex, color: k === "earth" ? 0x7fb3ff : k === "mars" ? 0xff9a6b : 0xe0c9a0, sizeAttenuation: false, depthWrite: false }));
      mk.scale.setScalar(0.03);
      scene.add(mk);
      this.markers[k] = mk;
    }
    this.nowOrbit = { earth: circle(1, 0x3987e5, { opacity: 0.55 }), mars: circle(1, 0xd95926, { opacity: 0.55 }) };
    scene.add(this.nowOrbit.earth, this.nowOrbit.mars);
    this.trails = { earth: trailLine(0x7fb3ff), mars: trailLine(0xff9a6b) };
    scene.add(this.trails.earth, this.trails.mars);

    this.label("system", "Sun", () => new THREE.Vector3(0, 0, 0));
    this.label("system", () => `Earth  ${valueAt(d, "earth_a", this.t).toFixed(3)} AU`, () => this.bodies.earth.position);
    this.label("system", () => `Mars  ${valueAt(d, "mars_a", this.t).toFixed(3)} AU`, () => this.bodies.mars.position);
    this.label("system", "Jupiter", () => this.bodies.jupiter.position);
    this.label("system", "Earth's target: 2.7 AU", () => new THREE.Vector3(2.7 * 0.707, 0, 2.7 * 0.707), "dim");
    this.label("system", "Mars parks: 3.64 AU", () => new THREE.Vector3(-3.64 * 0.6, 0, 3.64 * 0.8), "dim");
    this.label("system", "Jupiter's 2:1 resonance: 3.28 AU", () => new THREE.Vector3(-3.278 * 0.94, 0, -3.278 * 0.34), "dim");
    this.label("system", "Asteroid belt", () => new THREE.Vector3(0.5, 0, -2.6), "dim");
    return scene;
  }

  buildTowView(kind) {
    const d = this.d;
    const scene = new THREE.Scene();
    scene.add(stars());
    scene.add(new THREE.AmbientLight(0xffffff, 0.12));
    const sunLight = new THREE.DirectionalLight(0xfff2d8, 2.4);
    sunLight.position.set(0, 0, -1);
    scene.add(sunLight);
    const v = {};
    v.planet = sphere(0x3987e5, planetTexture(kind));
    v.planet.rotation.z = kind === "earth" ? 0.41 : 0.44;
    scene.add(v.planet);
    if (kind === "earth") {
      v.atmo = new THREE.Mesh(new THREE.SphereGeometry(1.04, 48, 24),
        new THREE.MeshBasicMaterial({ color: 0x6fb4ff, transparent: true, opacity: 0.16, depthWrite: false }));
      v.planet.add(v.atmo);
      v.moon = sphere(0xb9b5ab);
      scene.add(v.moon, circle(384.4, 0x6f6c64, { opacity: 0.8 }));
      v.clearance = circle(420, 0xfab219, { dashed: true, dash: 12, opacity: 0.5 });
      scene.add(v.clearance);
    } else {
      v.moonRings = [circle(9.376, 0x6f6c64), circle(23.463, 0x6f6c64)];
      scene.add(...v.moonRings);
    }
    v.hill = circle(1, 0x898781, { dashed: true, dash: 18, opacity: 0.6 });
    scene.add(v.hill);

    v.tow = new THREE.Group();
    v.rock = rock();
    v.mirror = new THREE.Mesh(new THREE.CircleGeometry(1, 48),
      new THREE.MeshStandardMaterial({ color: 0xe8e6df, metalness: 0.9, roughness: 0.15, side: THREE.DoubleSide, emissive: 0x2a2a28 }));
    v.cables = new THREE.LineSegments(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xa8a59c }));
    v.beamIn = beam();
    v.beamOut = beam(0xffe6b0);
    v.stations = new THREE.Group();
    for (let k = 0; k < 5; k++) {
      const s = new THREE.Mesh(new THREE.OctahedronGeometry(1), new THREE.MeshBasicMaterial({ color: 0xfab219 }));
      s.position.set((k - 2) * 14, 0, 0);
      s.scale.setScalar(4);
      v.stations.add(s);
    }
    v.tow.add(v.rock, v.mirror, v.cables, v.beamIn, v.beamOut, v.stations);
    scene.add(v.tow);

    const arrow = (color) => new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(), 120, color, 26, 14);
    v.pullOnPlanet = arrow(0x3987e5);
    v.pullOnRock = arrow(0xd95926);
    v.push = arrow(0xfab219);
    scene.add(v.pullOnPlanet, v.pullOnRock, v.push);
    v.state = {};
    v.kind = kind;

    const name = kind === "earth" ? "Earth" : "Mars";
    const towCfg = d.config.tows.find((t) => t.target === kind);
    this.label(kind, name, () => new THREE.Vector3(0, 0, 0));
    if (kind === "earth") {
      this.label(kind, "Moon", () => v.moon.position, "dim");
      this.label(kind, "No beam inside 420,000 km (beyond the Moon)", () => new THREE.Vector3(-420 * 0.71, 0, -420 * 0.71), "dim");
    } else {
      this.label(kind, "Phobos and Deimos orbit close in", () => new THREE.Vector3(-30, 0, 45), "dim");
    }
    this.label(kind, () => `Hill sphere ${(v.state.hill / 1e3).toFixed(0)},000 km`, () => new THREE.Vector3(0, 0, -v.state.hill / 1e3), "dim");
    this.label(kind, () => v.state.active ? `Tow asteroid, ${towCfg.asteroid_mass_kg.toExponential(2).replace("e+", "e")} kg, ${Math.round(v.state.dist).toLocaleString("en")} km` : `Tow finished (year ${Math.round(kind === "earth" ? d.milestones.earthArrives : d.milestones.marsParks).toLocaleString()}); asteroid sent away`,
      () => v.state.active ? v.rock.position : new THREE.Vector3(200, 0, 200));
    this.label(kind, () => v.state.active ? "Mirror on cables" : "", () => v.mirror.position, "dim below");
    this.label(kind, () => v.state.active ? "Light from beam stations (E1), far sunward" : "", () => v.stations.position, "dim");
    this.label(kind, () => v.state.active ? `Asteroid's pull on ${name}: ${v.state.force.toExponential(2).replace("e+", "e")} N` : "", () => v.state.tipPlanet, "force");
    this.label(kind, () => v.state.active ? `${name}'s pull on it: equal, opposite` : "", () => v.state.tipRock, "force to-left");
    this.label(kind, () => v.state.active ? "Light push holds it" : "", () => v.state.tipPush, "force to-left");
    (kind === "earth" ? (this.earthView = v) : (this.marsView = v));
    return scene;
  }

  setView(view, initial = false) {
    if (!initial) this.poses[this.view] = { pos: this.camera.position.clone(), target: this.controls.target.clone() };
    this.view = view;
    const p = this.poses[view];
    this.camera.position.copy(p.pos);
    this.controls.target.copy(p.target);
    this.camera.near = view === "system" ? 0.0005 : 0.05;
    this.camera.far = view === "system" ? 2e4 : 2e4;
    this.camera.updateProjectionMatrix();
    this.controls.update();
    for (const [k, list] of Object.entries(this.labels)) for (const l of list) l.el.style.display = k === view ? "" : "none";
    this.updateNote();
  }

  setScale(scale) {
    this.scale = scale;
    const vis = scale === "vis";
    const au = (k) => (vis ? VIS_AU[k] : RADIUS_KM[k] * KM_AU);
    this.sun.scale.setScalar(au("sun"));
    this.sunGlow.scale.setScalar(vis ? 0.9 : 0.12);
    for (const k of Object.keys(this.bodies)) {
      this.bodies[k].scale.setScalar(au(k));
      this.markers[k].visible = !vis;
    }
    for (const v of [this.earthView, this.marsView]) {
      const pr = (v.kind === "earth" ? RADIUS_KM.earth : RADIUS_KM.mars) / 1e3;
      v.planet.scale.setScalar(pr * (vis ? CLOSE_VIS.planet : 1));
      if (v.moon) v.moon.scale.setScalar((RADIUS_KM.moon / 1e3) * (vis ? CLOSE_VIS.moon : 1));
      const cfg = this.d.config.structures[`${v.kind}-tow`];
      const towCfg = this.d.config.tows.find((t) => t.target === v.kind);
      const rockKm = Math.cbrt((3 * towCfg.asteroid_mass_kg) / (4 * Math.PI * cfg.asteroid_density_kg_m3)) / 1e3;
      v.rockKm = rockKm;
      v.rock.scale.setScalar((rockKm / 1e3) * (vis ? CLOSE_VIS.rock : 1));
      v.mirrorR = (cfg.mirror_radius_km / 1e3) * (vis ? CLOSE_VIS.mirror : 1);
      v.mirror.scale.setScalar(v.mirrorR);
    }
    this.updateNote();
    this.update(this.t);
  }

  updateNote() {
    const vis = this.scale === "vis";
    let text;
    if (this.view === "system") {
      text = vis
        ? "Visualisation: the Sun is drawn 19× and the planets 260–1,800× their true size so they can be seen. Every distance and orbit is true. Between saved frames (10 years apart) each planet follows its orbit by Kepler's third law."
        : "True scale: every body at its real size. The planets are far smaller than a pixel here; the rings only mark where they are.";
    } else {
      const v = this.view === "earth" ? this.earthView : this.marsView;
      text = vis
        ? `Visualisation: the planet${v.moon ? " and the Moon" : ""} drawn ${CLOSE_VIS.planet}×, the asteroid ${CLOSE_VIS.rock}× (true radius ${Math.round(v.rockKm)} km) and its mirror ${CLOSE_VIS.mirror}× their true size. Distances are true. The view turns with the planet's orbit: the Sun is always up.`
        : "True scale: every body at its real size, distances true. The view turns with the planet's orbit: the Sun is always up.";
      if (v.moon) text += " The Moon's place on its orbit is illustrative.";
    }
    this.noteEl.textContent = text;
  }

  update(t) {
    this.t = t;
    const d = this.d;
    // Solar system
    for (const k of ["earth", "mars", "jupiter"]) {
      const p = ecl(positionAt(d.tracks[k], t));
      this.bodies[k].position.copy(p);
      this.markers[k].position.copy(p);
    }
    this.nowOrbit.earth.scale.setScalar(valueAt(d, "earth_a", t));
    this.nowOrbit.mars.scale.setScalar(valueAt(d, "mars_a", t));
    for (const k of ["earth", "mars"]) {
      const trk = d.tracks[k], line = this.trails[k];
      const period = Math.pow(valueAt(d, `${k}_a`, t), 1.5);
      const span = Math.min(t, 2.5 * period);
      const arr = line.geometry.attributes.position.array;
      for (let i = 0; i < line.n; i++) {
        const p = positionAt(trk, t - span + (span * i) / (line.n - 1));
        arr[i * 3] = p[0]; arr[i * 3 + 1] = p[2]; arr[i * 3 + 2] = -p[1];
      }
      line.geometry.attributes.position.needsUpdate = true;
    }
    this.resonance.visible = t < d.milestones.marsParks + 400;
    // Tow views
    this.updateTow(this.earthView, t);
    this.updateTow(this.marsView, t);
  }

  updateTow(v, t) {
    const d = this.d;
    const kind = v.kind;
    const active = towActive(d, t, kind);
    const a = valueAt(d, kind === "earth" ? "earth_a" : "mars_a", t);
    v.state.active = active;
    v.state.hill = HILL_KM_PER_AU[kind] * a;
    v.hill.scale.setScalar(v.state.hill / 1e3);
    v.tow.visible = active;
    for (const ar of [v.pullOnPlanet, v.pullOnRock, v.push]) ar.visible = active;
    if (!active) return;
    let rel;
    if (kind === "earth") rel = towLocalAt(d, t);
    else {
      const dist = valueAt(d, "mars_tow_km", t);
      rel = [dist * Math.SQRT1_2, dist * Math.SQRT1_2, 0];
    }
    const dist = Math.hypot(...rel);
    const towCfg = d.config.tows.find((x) => x.target === kind);
    v.state.dist = dist;
    v.state.force = (G * MASS[kind] * towCfg.asteroid_mass_kg) / (dist * 1e3) ** 2;
    const rockPos = loc(rel);
    const f = rockPos.clone().normalize();
    v.rock.position.copy(rockPos);
    const mirrorPos = rockPos.clone().add(f.clone().multiplyScalar(Math.max(v.mirrorR * 2.2, 18)));
    v.mirror.position.copy(mirrorPos);
    v.mirror.lookAt(mirrorPos.clone().add(f));
    // Cables from the rock to four points on the mirror's rim.
    const side = new THREE.Vector3(0, 1, 0).cross(f).normalize();
    const up = f.clone().cross(side).normalize();
    const pts = [];
    for (const [s, u] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      pts.push(rockPos.clone(), mirrorPos.clone().add(side.clone().multiplyScalar(s * v.mirrorR)).add(up.clone().multiplyScalar(u * v.mirrorR)));
    }
    v.cables.geometry.setFromPoints(pts);
    // Light arrives travelling away from the Sun (+z here) and leaves along in - 2(in.n)n: the push is along n.
    const inDir = new THREE.Vector3(0, 0, 1);
    const outDir = inDir.clone().sub(f.clone().multiplyScalar(2 * inDir.dot(f)));
    const L = kind === "earth" ? 1000 : 650;
    const src = mirrorPos.clone().sub(inDir.clone().multiplyScalar(L));
    const r = this.scale === "vis" ? 3.5 : 1.2;
    v.beamIn.setEnds(src, mirrorPos, r);
    v.beamOut.setEnds(mirrorPos, mirrorPos.clone().add(outDir.multiplyScalar(L)), r * 0.8);
    v.stations.position.copy(src);
    // Forces: the gravity pair, and the light push that balances Earth's pull on the asteroid.
    const len = kind === "earth" ? 150 : 110;
    v.pullOnPlanet.position.set(0, 0, 0);
    v.pullOnPlanet.setDirection(f);
    v.pullOnPlanet.setLength(len, len * 0.2, len * 0.11);
    v.pullOnRock.position.copy(rockPos);
    v.pullOnRock.setDirection(f.clone().negate());
    v.pullOnRock.setLength(len, len * 0.2, len * 0.11);
    v.push.position.copy(mirrorPos);
    v.push.setDirection(f);
    v.push.setLength(len, len * 0.2, len * 0.11);
    v.state.tipPlanet = f.clone().multiplyScalar(len * 0.7).add(new THREE.Vector3(0, 0, 40));
    v.state.tipRock = rockPos.clone().sub(f.clone().multiplyScalar(len * 0.8)).add(new THREE.Vector3(0, 0, -30));
    v.state.tipPush = mirrorPos.clone().add(f.clone().multiplyScalar(len));
  }

  resize() {
    const el = this.canvas.parentElement;
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  render(now) {
    const sec = now / 1000;
    const ev = this.earthView, mv = this.marsView;
    ev.planet.rotation.y = sec * 0.25;
    mv.planet.rotation.y = sec * 0.24;
    const moonA = sec * 0.3;
    ev.moon.position.set(384.4 * Math.cos(moonA), 0, 384.4 * Math.sin(moonA));
    if (ev.rock.visible) ev.rock.rotation.y = sec * 0.1;
    this.controls.update();
    this.renderer.render(this.scenes[this.view], this.camera);
    this.placeLabels();
  }

  placeLabels() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    const v = new THREE.Vector3();
    for (const l of this.labels[this.view]) {
      const text = typeof l.text === "function" ? l.text() : l.text;
      const at = l.at();
      if (!text || !at) { l.el.style.display = "none"; continue; }
      v.copy(at).project(this.camera);
      if (v.z > 1 || v.x < -1.2 || v.x > 1.2 || v.y < -1.2 || v.y > 1.2) { l.el.style.display = "none"; continue; }
      l.el.style.display = "";
      if (l.el.textContent !== text) l.el.textContent = text;
      l.el.style.left = `${((v.x + 1) / 2) * w}px`;
      l.el.style.top = `${((1 - v.y) / 2) * h}px`;
    }
  }
}
