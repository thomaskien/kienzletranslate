import {
  FrameCapture,
  FrameRingBuffer,
  encodePcm16Wav,
  mapPerformanceTimeToFrame,
  preRollSamples,
} from "./audio-core.js";
import { GenerationGate, languageDirection, secureUuid } from "./frontend-core.js";

const API = "/api.php?route=";
const MAX_RECORDING_SECONDS = 60;
const state = {
  csrf: "",
  languages: [],
  model: { state: "unloaded" },
  preRollMs: readPreRoll(),
  tts: localStorage.getItem("tts") !== "0",
  activePointer: null,
  activeSide: null,
  activeGeneration: null,
  activeUtteranceId: null,
  activeOrder: null,
  activeDirection: null,
  activeTts: false,
  holdTimer: null,
  gesture: null,
};
const gate = new GenerationGate();

const $ = (selector) => document.querySelector(selector);
const ui = {
  auth: $("#auth-view"), app: $("#app-view"), authForm: $("#login-form"),
  password: $("#password"), authError: $("#auth-error"), offline: $("#offline-view"),
  top: $("#top-side"), bottom: $("#bottom-side"), topText: $("#top-text"),
  bottomText: $("#bottom-text"), topLanguage: $("#top-language"),
  bottomLanguage: $("#bottom-language"), tts: $("#tts-toggle"),
  status: $("#status-message"), preRollButton: $("#pre-roll-button"),
  settingsButton: $("#settings-button"), settings: $("#settings-dialog"),
  preRoll: $("#pre-roll"), preRollValue: $("#pre-roll-value"),
  modelState: $("#model-state"), loadModel: $("#model-load"),
  unloadModel: $("#model-unload"), logout: $("#logout"),
  micDialog: $("#microphone-dialog"), micEnable: $("#enable-microphone"),
  micError: $("#microphone-error"), orientation: $("#orientation-hint"),
};

class AudioCapture {
  constructor() {
    this.context = null;
    this.stream = null;
    this.source = null;
    this.node = null;
    this.ring = null;
    this.active = null;
    this.captures = new Set();
    this.lastFrame = -1;
    this.waiters = [];
    this.playback = false;
    this.cleanFromFrame = 0;
    this.disposing = false;
  }

  async enable() {
    if (this.context && this.node && this.stream?.getAudioTracks().some((track) => track.readyState === "live")) {
      await this.context.resume();
      if (this.context.state !== "running") throw new Error("Der Audiokontext konnte nicht gestartet werden.");
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.AudioWorkletNode) {
      throw new Error("Dieser Browser unterstützt die benötigte Audioaufnahme nicht.");
    }
    await this.disposeBrokenAudio();
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        video: false,
      });
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.context = new AudioContextClass({ latencyHint: "interactive" });
      await this.context.audioWorklet.addModule("/assets/audio-worklet.js");
      this.ring = new FrameRingBuffer(Math.ceil(this.context.sampleRate * 3));
      this.source = this.context.createMediaStreamSource(this.stream);
      this.node = new AudioWorkletNode(this.context, "pcm-capture", {
        numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1],
      });
      const silent = this.context.createGain();
      silent.gain.value = 0;
      this.source.connect(this.node).connect(silent).connect(this.context.destination);
      this.node.port.onmessage = ({ data }) => {
        if (data?.type !== "pcm" || !(data.samples instanceof Float32Array)) return;
        const end = data.startFrame + data.samples.length;
        this.lastFrame = Math.max(this.lastFrame, end);
        if (!this.playback && end > this.cleanFromFrame) {
          const from = Math.max(data.startFrame, this.cleanFromFrame);
          this.ring.append(from, data.samples.subarray(from - data.startFrame));
        }
        for (const capture of this.captures) capture.ingest(data.startFrame, data.samples);
        this.resolveWaiters();
      };
      for (const track of this.stream.getAudioTracks()) {
        track.addEventListener("ended", () => this.onFailure?.("Der Mikrofonzugriff wurde beendet."), { once: true });
      }
      await this.context.resume();
      if (this.context.state !== "running") throw new Error("Der Audiokontext konnte nicht gestartet werden.");
      this.context.addEventListener("statechange", () => {
        if (!this.disposing && !document.hidden && this.context?.state !== "running") {
          this.onFailure?.("Audio wurde unterbrochen. Bitte Mikrofon erneut aktivieren.");
        }
      });
    } catch (error) {
      await this.disposeBrokenAudio();
      throw error;
    }
  }

  async disposeBrokenAudio() {
    this.disposing = true;
    this.node?.disconnect();
    this.source?.disconnect();
    for (const track of this.stream?.getTracks() || []) track.stop();
    if (this.context && this.context.state !== "closed") await this.context.close().catch(() => {});
    this.context = null;
    this.stream = null;
    this.source = null;
    this.node = null;
    this.ring = null;
    this.active = null;
    this.captures.clear();
    this.lastFrame = -1;
    this.cleanFromFrame = 0;
    this.disposing = false;
  }

  frameAt(eventTime) {
    return mapPerformanceTimeToFrame(eventTime, this.context, () => performance.now());
  }

  begin(eventTime, preRollMs) {
    if (!this.context || this.context.state !== "running" || this.active) {
      throw new Error("Das Mikrofon ist nicht bereit.");
    }
    const frame = Math.max(this.frameAt(eventTime), this.cleanFromFrame);
    const capture = new FrameCapture(this.ring, frame, preRollSamples(preRollMs, this.context.sampleRate));
    this.active = capture;
    this.captures.add(capture);
  }

  async end(eventTime) {
    if (!this.active) return null;
    const capture = this.active;
    this.active = null;
    const endFrame = this.frameAt(eventTime);
    if (endFrame - capture.windowStart > this.context.sampleRate * MAX_RECORDING_SECONDS) {
      capture.cancel();
      this.captures.delete(capture);
      throw new Error("Die Aufnahme wurde verworfen, weil sie länger als 60 Sekunden war.");
    }
    try {
      await this.waitForFrame(endFrame, 500);
    } catch (error) {
      capture.cancel();
      throw error;
    } finally {
      this.captures.delete(capture);
    }
    const samples = capture.finish(endFrame);
    if (!samples?.length) throw new Error("Die Aufnahme war leer. Bitte erneut versuchen.");
    if (samples.length > this.context.sampleRate * MAX_RECORDING_SECONDS) {
      throw new Error("Die Aufnahme wurde verworfen, weil sie länger als 60 Sekunden war.");
    }
    return { samples, sampleRate: this.context.sampleRate };
  }

  cancel({ clear = true } = {}) {
    for (const capture of this.captures) capture.cancel();
    this.captures.clear();
    this.active = null;
    if (clear) {
      this.ring?.clear();
      this.cleanFromFrame = Math.ceil((this.context?.currentTime || 0) * (this.context?.sampleRate || 48000));
    }
  }

  setPlayback(active) {
    this.playback = active;
    this.ring?.clear();
    // Ignore queued worklet messages from before playback stopped as well.
    this.cleanFromFrame = Math.ceil((this.context?.currentTime || 0) * (this.context?.sampleRate || 48000));
  }

  async suspend() {
    this.cancel();
    if (this.context?.state === "running") await this.context.suspend();
  }

  waitForFrame(frame, timeoutMs) {
    if (this.lastFrame >= frame) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const waiter = { frame, resolve, timer: 0 };
      waiter.timer = window.setTimeout(() => {
        this.waiters = this.waiters.filter((candidate) => candidate !== waiter);
        reject(new Error("Audioaufnahme unterbrochen. Bitte erneut versuchen."));
      }, timeoutMs);
      this.waiters.push(waiter);
    });
  }

  resolveWaiters() {
    for (const waiter of [...this.waiters]) {
      if (this.lastFrame < waiter.frame) continue;
      clearTimeout(waiter.timer);
      this.waiters = this.waiters.filter((candidate) => candidate !== waiter);
      waiter.resolve();
    }
  }
}

const audioCapture = new AudioCapture();
audioCapture.onFailure = (message) => {
  gate.next();
  stopPlayback();
  audioCapture.cancel();
  resetPressVisuals();
  setStatus(message, "error");
  if (!ui.micDialog.open) ui.micDialog.showModal();
  ui.micEnable.disabled = false;
};
let playbackSource = null;

function readPreRoll() {
  const raw = localStorage.getItem("preRollMs");
  if (raw === null) return 1000;
  const stored = Number(raw);
  return Number.isInteger(stored) && stored >= 0 && stored <= 3000 && stored % 250 === 0 ? stored : 1000;
}

function formatSeconds(milliseconds) {
  return `${(milliseconds / 1000).toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 2 })} s`;
}

async function request(route, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.mutating !== false && state.csrf) headers.set("X-CSRF-Token", state.csrf);
  if (options.json !== undefined) headers.set("Content-Type", "application/json");
  let response;
  try {
    response = await fetch(`${API}${route}`, {
      ...options, headers, credentials: "same-origin",
      body: options.json === undefined ? options.body : JSON.stringify(options.json),
      cache: "no-store",
    });
  } catch {
    throw new Error("Der lokale Server ist nicht erreichbar. Netzwerkverbindung prüfen.");
  }
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json().catch(() => ({})) : null;
  if (!response.ok) throw new Error(payload?.error || `Serverfehler (${response.status})`);
  return payload;
}

async function bootstrap() {
  try {
    const data = await request("bootstrap", { method: "GET", mutating: false });
    ui.offline.hidden = true;
    if (!data.authenticated) {
      showView("auth");
      return;
    }
    state.csrf = data.csrf;
    state.languages = Array.isArray(data.languages) ? data.languages : [];
    state.model = data.model || { state: "unloaded" };
    showApplication();
  } catch (error) {
    showView("offline");
    ui.offline.querySelector("p").textContent = error.message;
  }
}

function showView(name) {
  ui.auth.hidden = name !== "auth";
  ui.app.hidden = name !== "app";
  ui.offline.hidden = name !== "offline";
}

function showApplication() {
  showView("app");
  fillLanguages();
  ui.tts.setAttribute("aria-pressed", String(state.tts));
  ui.tts.classList.toggle("enabled", state.tts);
  ui.tts.title = state.tts ? "Sprachausgabe ausschalten" : "Sprachausgabe einschalten";
  updatePreRoll();
  updateModelState();
  if (["loading", "unloading"].includes(state.model.state)) setTimeout(refreshHealth, 1200);
  ui.micDialog.showModal();
}

function fillLanguages() {
  const makeOptions = (select) => {
    select.replaceChildren(...state.languages.map((language) => {
      const option = document.createElement("option");
      option.value = language.code;
      option.textContent = language.name;
      option.dataset.speechOutput = String(Boolean(language.speech_output));
      return option;
    }));
  };
  makeOptions(ui.topLanguage);
  makeOptions(ui.bottomLanguage);
  const codes = new Set(state.languages.map(({ code }) => code));
  const first = state.languages[0]?.code || "";
  const topFallback = codes.has("ukr") ? "ukr" : state.languages.find(({ code }) => code !== "deu")?.code || first;
  const bottomFallback = codes.has("deu") ? "deu" : first;
  ui.topLanguage.value = codes.has(localStorage.getItem("topLanguage")) ? localStorage.getItem("topLanguage") : topFallback;
  ui.bottomLanguage.value = codes.has(localStorage.getItem("bottomLanguage")) ? localStorage.getItem("bottomLanguage") : bottomFallback;
}

function setStatus(message = "", kind = "") {
  ui.status.textContent = message;
  ui.status.dataset.kind = kind;
}

function updatePreRoll() {
  ui.preRoll.value = String(state.preRollMs);
  ui.preRollValue.textContent = formatSeconds(state.preRollMs);
  ui.preRollButton.textContent = `↺ ${formatSeconds(state.preRollMs)}`;
}

function updateModelState() {
  const labels = { unloaded: "nicht geladen", loading: "wird geladen", ready: "bereit", unloading: "wird entladen", error: "Fehler" };
  ui.modelState.textContent = labels[state.model.state] || state.model.state || "unbekannt";
  ui.modelState.dataset.state = state.model.state;
  ui.loadModel.disabled = ["ready", "loading", "unloading"].includes(state.model.state);
  ui.unloadModel.disabled = state.model.state !== "ready";
  if (state.model.state === "error") setStatus(state.model.error || "Das Modell meldet einen Fehler.", "error");
  else if (["ready", "unloaded"].includes(state.model.state) && ui.status.dataset.kind === "busy") setStatus("");
}

function stopPlayback() {
  const interrupted = audioCapture.playback;
  if (playbackSource) {
    playbackSource.onended = null;
    playbackSource.stop();
    playbackSource.disconnect();
    playbackSource = null;
  }
  if (interrupted) audioCapture.setPlayback(false);
  return interrupted;
}

function startPress(event, side) {
  if (ui.settings.open || state.activePointer !== null || !event.isPrimary || event.button !== 0) return;
  event.preventDefault();
  const interruptedPlayback = stopPlayback();
  const effectivePreRoll = interruptedPlayback ? 0 : state.preRollMs;
  const generation = gate.next();
  const utteranceId = secureUuid();
  const direction = languageDirection(side, ui.topLanguage.value, ui.bottomLanguage.value);
  try {
    // Echo-tainted pre-roll is intentionally excluded when this press interrupts playback.
    audioCapture.begin(event.timeStamp, effectivePreRoll);
  } catch (error) {
    setStatus(error.message, "error");
    return;
  }
  state.activePointer = event.pointerId;
  state.gesture = { pointer: event.pointerId, y: event.clientY, lastY: event.clientY, scrolling: false,
    text: side === "top" ? ui.topText : ui.bottomText, side };
  state.activeSide = side;
  state.activeGeneration = generation;
  state.activeUtteranceId = utteranceId;
  state.activeOrder = Math.floor((performance.timeOrigin + performance.now()) * 1000);
  state.activeDirection = direction;
  state.activeTts = state.tts;
  event.currentTarget.setPointerCapture(event.pointerId);
  ui.app.dataset.active = side;
  setStatus("Aufnahme läuft …", "recording");
  const maximumHold = Math.max(0, MAX_RECORDING_SECONDS * 1000 - effectivePreRoll);
  state.holdTimer = window.setTimeout(() => abortPress("Die Aufnahme wurde nach 60 Sekunden verworfen."), maximumHold);
}

async function releasePress(event) {
  if (state.gesture?.pointer === event.pointerId && state.gesture.scrolling) {
    state.gesture = null;
    return;
  }
  if (event.pointerId !== state.activePointer) return;
  event.preventDefault();
  const side = state.activeSide;
  const generation = state.activeGeneration;
  const utteranceId = state.activeUtteranceId;
  const order = state.activeOrder;
  const direction = state.activeDirection;
  const tts = state.activeTts;
  resetPressVisuals();
  setStatus("Wird übertragen …", "busy");
  try {
    const recording = await audioCapture.end(event.timeStamp);
    if (!recording || !gate.accepts(generation)) return;
    const wav = encodePcm16Wav(recording.samples, recording.sampleRate);
    await submitUtterance(wav, side, generation, utteranceId, direction, tts, order);
  } catch (error) {
    if (gate.accepts(generation)) setStatus(error.message, "error");
  }
}

function cancelPress(event) {
  if (event?.pointerId === state.gesture?.pointer) state.gesture = null;
  if (event && event.pointerId !== state.activePointer) return;
  abortPress("Aufnahme abgebrochen.");
}

function abortPress(message) {
  if (state.activePointer === null) return;
  audioCapture.cancel();
  resetPressVisuals();
  setStatus(message, "error");
}

function resetPressVisuals() {
  clearTimeout(state.holdTimer);
  state.holdTimer = null;
  state.activePointer = null;
  state.activeSide = null;
  state.activeGeneration = null;
  state.activeUtteranceId = null;
  state.activeDirection = null;
  state.activeTts = false;
  delete ui.app.dataset.active;
}

async function submitUtterance(wav, side, generation, id, direction, tts, order) {
  const params = new URLSearchParams({
    utterance_id: id, speaker_side: side, source_lang: direction.source,
    target_lang: direction.target, tts: tts ? "1" : "0", generation: String(order),
  });
  await request(`utterances&${params}`, {
    method: "POST", body: wav, headers: { "Content-Type": "audio/wav" },
  });
  if (gate.accepts(generation)) setStatus("Verarbeitung läuft …", "busy");
  await pollUtterance(id, side, generation);
}

async function pollUtterance(id, side, generation) {
  for (;;) {
    if (!gate.accepts(generation)) return;
    const result = await request(`utterances/${encodeURIComponent(id)}`, { method: "GET", mutating: false });
    if (!gate.accepts(generation)) return;
    if (result.status === "complete") {
      showResult(result, side);
      if (result.text_only_reason) setStatus(`Nur Text: ${result.text_only_reason}`, "notice");
      else setStatus("");
      if (state.tts && result.audio_available) await playResult(id, generation);
      return;
    }
    if (result.status === "error") throw new Error(result.error || "Die Übersetzung ist fehlgeschlagen.");
    await new Promise((resolve) => setTimeout(resolve, 750));
  }
}

function showResult(result, side) {
  const original = result.original_text || "";
  const translated = result.translated_text || "";
  if (side === "top") {
    ui.topText.textContent = original;
    ui.bottomText.textContent = translated;
  } else {
    ui.bottomText.textContent = original;
    ui.topText.textContent = translated;
  }
}

async function playResult(id, generation) {
  const response = await fetch(`${API}audio/${encodeURIComponent(id)}`, { credentials: "same-origin", cache: "no-store" });
  if (!response.ok || !gate.accepts(generation)) return;
  const data = await response.arrayBuffer();
  if (!gate.accepts(generation)) return;
  if (audioCapture.context?.state !== "running") {
    setStatus("Bitte Mikrofon aktivieren, um Audio wiederzugeben.", "notice");
    return;
  }
  // Use the AudioContext unlocked by the microphone activation touch. A new
  // HTMLAudioElement after an asynchronous request would be blocked by iPadOS.
  const decoded = await audioCapture.context.decodeAudioData(data);
  if (!gate.accepts(generation)) return;
  stopPlayback();
  const source = audioCapture.context.createBufferSource();
  source.buffer = decoded;
  source.connect(audioCapture.context.destination);
  playbackSource = source;
  audioCapture.setPlayback(true);
  source.onended = () => {
    if (playbackSource !== source) return;
    playbackSource = null;
    source.disconnect();
    audioCapture.setPlayback(false);
  };
  source.start();
}

async function changeModel(action) {
  setStatus(action === "load" ? "Modell wird geladen …" : "Modell wird entladen …", "busy");
  try {
    await request(`model/${action}`, { method: "POST" });
    await refreshHealth();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function refreshHealth() {
  try {
    state.model = await request("health", { method: "GET", mutating: false });
    updateModelState();
    if (["loading", "unloading"].includes(state.model.state)) setTimeout(refreshHealth, 1200);
    else if (ui.status.textContent.startsWith("Modell wird")) {
      setStatus(state.model.state === "ready" ? "Modell bereit." : state.model.state === "unloaded" ? "Modell entladen." : (state.model.error || "Modellfehler."), state.model.state === "error" ? "error" : "notice");
    }
  } catch (error) {
    setStatus(error.message, "error");
  }
}

ui.authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  ui.authError.textContent = "";
  try {
    await request("login", { method: "POST", json: { password: ui.password.value } });
    ui.password.value = "";
    await bootstrap();
  } catch (error) {
    ui.authError.textContent = error.message;
  }
});

$("#retry-bootstrap").addEventListener("click", () => bootstrap());
ui.micDialog.addEventListener("cancel", (event) => event.preventDefault());

for (const [element, side] of [[ui.top, "top"], [ui.bottom, "bottom"]]) {
  element.addEventListener("pointerdown", (event) => startPress(event, side));
  element.addEventListener("pointermove", (event) => {
    const gesture = state.gesture;
    if (!gesture || gesture.pointer !== event.pointerId) return;
    if (!gesture.scrolling && gesture.text.scrollHeight > gesture.text.clientHeight + 4 && Math.abs(event.clientY - gesture.y) > 14) {
      gesture.scrolling = true;
      abortPress("");
    }
    if (gesture.scrolling) {
      event.preventDefault();
      gesture.text.scrollTop += (event.clientY - gesture.lastY) * (side === "top" ? 1 : -1);
    }
    gesture.lastY = event.clientY;
  });
  element.addEventListener("pointerup", releasePress);
  element.addEventListener("pointercancel", cancelPress);
  element.addEventListener("lostpointercapture", (event) => {
    if (state.activePointer === event.pointerId) cancelPress(event);
  });
  element.addEventListener("contextmenu", (event) => event.preventDefault());
}

ui.micEnable.addEventListener("click", async () => {
  ui.micEnable.disabled = true;
  ui.micError.textContent = "";
  try {
    await audioCapture.enable();
    ui.micDialog.close();
    setStatus("Mikrofon bereit.", "notice");
    setTimeout(() => { if (ui.status.textContent === "Mikrofon bereit.") setStatus(""); }, 1800);
  } catch (error) {
    ui.micError.textContent = error.message;
    ui.micEnable.disabled = false;
  }
});

ui.tts.addEventListener("click", () => {
  state.tts = !state.tts;
  localStorage.setItem("tts", state.tts ? "1" : "0");
  ui.tts.setAttribute("aria-pressed", String(state.tts));
  ui.tts.classList.toggle("enabled", state.tts);
  ui.tts.title = state.tts ? "Sprachausgabe ausschalten" : "Sprachausgabe einschalten";
  if (!state.tts) stopPlayback();
});

for (const select of [ui.topLanguage, ui.bottomLanguage]) {
  select.addEventListener("change", () => {
    localStorage.setItem(select === ui.topLanguage ? "topLanguage" : "bottomLanguage", select.value);
  });
}

function openSettings() { ui.settings.showModal(); refreshHealth(); }
ui.preRollButton.addEventListener("click", openSettings);
ui.settingsButton.addEventListener("click", openSettings);
ui.preRoll.addEventListener("input", () => { ui.preRollValue.textContent = formatSeconds(Number(ui.preRoll.value)); });
ui.settings.addEventListener("close", () => {
  state.preRollMs = Number(ui.preRoll.value);
  localStorage.setItem("preRollMs", String(state.preRollMs));
  updatePreRoll();
});
ui.loadModel.addEventListener("click", () => changeModel("load"));
ui.unloadModel.addEventListener("click", () => changeModel("unload"));
ui.logout.addEventListener("click", async () => {
  stopPlayback();
  audioCapture.cancel();
  try { await request("logout", { method: "POST" }); } finally { location.reload(); }
});

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    gate.next();
    if (state.activePointer !== null) abortPress("Aufnahme wegen App-Wechsel abgebrochen.");
    stopPlayback();
    audioCapture.suspend().catch(() => {});
  } else if (audioCapture.context?.state === "suspended") {
    setStatus("Zum Fortfahren Mikrofon erneut aktivieren.", "notice");
    ui.micDialog.showModal();
    ui.micEnable.disabled = false;
  }
});

window.addEventListener("pagehide", () => {
  gate.next();
  audioCapture.cancel();
  stopPlayback();
});

window.addEventListener("offline", () => {
  gate.next();
  abortPress("Netzwerk unterbrochen. Aufnahme verworfen.");
  audioCapture.cancel();
  stopPlayback();
  setStatus("Keine Netzwerkverbindung zum Server.", "error");
});

if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
bootstrap();
