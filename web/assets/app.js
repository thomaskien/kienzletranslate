import {
  FrameCapture,
  FrameRingBuffer,
  encodePcm16Wav,
  mapPerformanceTimeToFrame,
  preRollSamples,
} from "./audio-core.js";
import { GenerationGate, languageDirection, secureUuid } from "./frontend-core.js";
import {
  groupLanguages,
  MODEL_TO_BCP47,
  UI_LANGUAGES,
  interfaceChoice,
  isRtlLocale,
  languageFlag,
  nativeLanguageName,
  normalizeUiLocale,
  translate,
} from "./i18n.js";

const API = "/api.php?route=";
const MAX_RECORDING_SECONDS = 60;
const state = {
  csrf: "",
  languages: [],
  model: { state: "unloaded" },
  passwordRequired: true,
  uiLocale: normalizeUiLocale(localStorage.getItem("uiLanguage")),
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
  topLanguagePending: true,
  hasResult: false,
  status: { key: "", kind: "", parameters: {} },
};
const gate = new GenerationGate();

const $ = (selector) => document.querySelector(selector);
const ui = {
  auth: $("#auth-view"), app: $("#app-view"), authForm: $("#login-form"),
  password: $("#password"), authError: $("#auth-error"), offline: $("#offline-view"),
  offlineMessage: $("#offline-message"),
  top: $("#top-side"), bottom: $("#bottom-side"), topText: $("#top-text"),
  bottomText: $("#bottom-text"), topLanguage: $("#top-language"),
  topLanguageButton: $("#top-language-button"), topLanguageFlag: $("#top-language-flag"),
  topLanguageCaption: $("#top-language-caption"), topLanguagePicker: $("#top-language-picker"),
  topLanguageInlineGrid: $("#top-language-inline-grid"), topLanguageDialog: $("#top-language-dialog"),
  topLanguageDialogGrid: $("#top-language-dialog-grid"), closeTopLanguage: $("#close-top-language"),
  restartTopLanguage: $("#restart-top-language"),
  bottomLanguage: $("#bottom-language"), tts: $("#tts-toggle"),
  status: $("#status-message"), preRollButton: $("#pre-roll-button"),
  settingsButton: $("#settings-button"), settings: $("#settings-dialog"),
  preRoll: $("#pre-roll"), preRollValue: $("#pre-roll-value"),
  modelState: $("#model-state"), loadModel: $("#model-load"),
  unloadModel: $("#model-unload"), logout: $("#logout"),
  micDialog: $("#microphone-dialog"), micEnable: $("#enable-microphone"),
  micError: $("#microphone-error"), orientation: $("#orientation-hint"),
};

const SERVER_ERROR_KEYS = {
  login_failed: "loginFailed",
  authentication_required: "authenticationRequired",
  csrf: "sessionReload",
  origin: "accessDenied",
  size: "inputTooLarge",
  metadata: "invalidRecording",
  not_found: "notFound",
  https_required: "accessDenied",
};

function t(key, parameters = {}) {
  return translate(state.uiLocale, key, parameters);
}

function localizedError(key, parameters = {}) {
  const error = new Error(key);
  error.i18nKey = key;
  error.i18nParameters = parameters;
  return error;
}

function errorText(error) {
  return t(error?.i18nKey || "requestFailed", error?.i18nParameters || { status: "?" });
}

function setFormError(element, error = null) {
  element.dataset.errorKey = error?.i18nKey || "";
  element.dataset.errorParameters = JSON.stringify(error?.i18nParameters || {});
  element.textContent = error ? errorText(error) : "";
}

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
      if (this.context.state !== "running") throw localizedError("audioContextStart");
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.AudioWorkletNode) {
      throw localizedError("audioUnsupported");
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
        track.addEventListener("ended", () => this.onFailure?.(localizedError("micAccessEnded")), { once: true });
      }
      await this.context.resume();
      if (this.context.state !== "running") throw localizedError("audioContextStart");
      this.context.addEventListener("statechange", () => {
        if (!this.disposing && !document.hidden && this.context?.state !== "running") {
          this.onFailure?.(localizedError("audioInterrupted"));
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
      throw localizedError("micNotReady");
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
      throw localizedError("recordingTooLong");
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
    if (!samples?.length) throw localizedError("emptyRecording");
    if (samples.length > this.context.sampleRate * MAX_RECORDING_SECONDS) {
      throw localizedError("recordingTooLong");
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
        reject(localizedError("recordingInterrupted"));
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
audioCapture.onFailure = (error) => {
  gate.next();
  stopPlayback();
  audioCapture.cancel();
  resetPressVisuals();
  setStatus(error?.i18nKey || "audioInterrupted", "error", error?.i18nParameters);
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
  return `${(milliseconds / 1000).toLocaleString(state.uiLocale, { minimumFractionDigits: 1, maximumFractionDigits: 2 })} s`;
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
    throw localizedError("networkUnavailable");
  }
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json().catch(() => ({})) : null;
  if (!response.ok) {
    const key = SERVER_ERROR_KEYS[payload?.code] || "serverError";
    throw localizedError(key, { status: response.status });
  }
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
    state.passwordRequired = data.password_required !== false;
    showApplication();
  } catch (error) {
    showView("offline");
    ui.offlineMessage.dataset.i18n = error.i18nKey || "networkUnavailable";
    ui.offlineMessage.textContent = errorText(error);
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
  state.topLanguagePending = true;
  ui.topLanguagePicker.hidden = true;
  ui.top.classList.remove("language-picker-open");
  ui.tts.setAttribute("aria-pressed", String(state.tts));
  ui.tts.classList.toggle("enabled", state.tts);
  updateTtsLabel();
  updatePreRoll();
  updateModelState();
  updateLogoutLabel();
  scheduleFit();
  if (["loading", "unloading"].includes(state.model.state)) setTimeout(refreshHealth, 1200);
  ui.micEnable.disabled = false;
  ui.micDialog.showModal();
}

function fillLanguages() {
  const previousTop = ui.topLanguage.value || localStorage.getItem("topLanguage");
  const previousBottom = ui.bottomLanguage.value || localStorage.getItem("bottomLanguage");
  const groups = groupLanguages(state.languages, state.uiLocale);
  const makeOptions = (select) => {
    const makeGroup = (label, languages) => {
      const group = document.createElement("optgroup");
      group.label = label;
      group.replaceChildren(...languages.map((language) => {
        const option = document.createElement("option");
        option.value = language.code;
        option.textContent = `${languageFlag(language.code)} ${language.displayName}`;
        option.dataset.speechOutput = String(Boolean(language.speech_output));
        return option;
      }));
      return group;
    };
    select.replaceChildren(
      makeGroup(t("commonGermany"), groups.common),
      makeGroup(t("otherLanguages"), groups.other),
    );
  };
  makeOptions(ui.topLanguage);
  makeOptions(ui.bottomLanguage);
  const codes = new Set(state.languages.map(({ code }) => code));
  const first = state.languages[0]?.code || "";
  const topFallback = codes.has("ukr") ? "ukr" : state.languages.find(({ code }) => code !== "deu")?.code || first;
  const bottomFallback = codes.has("deu") ? "deu" : first;
  ui.topLanguage.value = codes.has(previousTop) ? previousTop : topFallback;
  ui.bottomLanguage.value = codes.has(previousBottom) ? previousBottom : bottomFallback;
  renderTopLanguageChoices(ui.topLanguageInlineGrid, groups);
  renderTopLanguageChoices(ui.topLanguageDialogGrid, groups);
  updateTopLanguageSelection();
}

function renderTopLanguageChoices(container, groups) {
  const makeGroup = (label, languages) => {
    const section = document.createElement("section");
    section.className = "model-language-group";
    const heading = document.createElement("h3");
    heading.textContent = label;
    const grid = document.createElement("div");
    grid.className = "model-language-grid";
    grid.replaceChildren(...languages.map((language) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "model-language-choice";
      button.dataset.topLanguage = language.code;
      button.setAttribute("aria-label", nativeLanguageName(language));
      button.setAttribute("aria-pressed", String(language.code === ui.topLanguage.value));
      const flag = document.createElement("span");
      flag.className = "model-language-flag";
      flag.setAttribute("aria-hidden", "true");
      flag.textContent = languageFlag(language.code);
      const name = document.createElement("span");
      name.className = "model-language-name";
      name.dir = "auto";
      name.lang = MODEL_TO_BCP47[language.code] || "";
      name.textContent = nativeLanguageName(language);
      button.append(flag, name);
      button.addEventListener("click", () => selectTopLanguage(language.code));
      return button;
    }));
    section.append(heading, grid);
    return section;
  };
  container.replaceChildren(
    makeGroup(t("commonGermany"), groups.common),
    makeGroup(t("otherLanguages"), groups.other),
  );
}

function updateTopLanguageSelection() {
  const language = state.languages.find(({ code }) => code === ui.topLanguage.value);
  if (!language) return;
  const name = nativeLanguageName(language);
  ui.topLanguageFlag.textContent = languageFlag(language.code);
  ui.topLanguageCaption.textContent = name;
  ui.topLanguageCaption.lang = MODEL_TO_BCP47[language.code] || "";
  for (const button of document.querySelectorAll("[data-top-language]")) {
    button.setAttribute("aria-pressed", String(button.dataset.topLanguage === language.code));
  }
}

let topLanguageDialogOpener = null;

function selectTopLanguage(code) {
  if (!state.languages.some((language) => language.code === code)) return;
  const wasPending = state.topLanguagePending;
  const changed = ui.topLanguage.value !== code;
  ui.topLanguage.value = code;
  localStorage.setItem("topLanguage", code);
  updateTopLanguageSelection();

  if (!wasPending && changed) {
    gate.next();
    stopPlayback();
    state.hasResult = false;
    ui.topText.textContent = t("topPrompt");
    ui.bottomText.textContent = t("bottomPrompt");
    setStatus("");
    scheduleFit();
  }

  state.topLanguagePending = false;
  const inlineWasOpen = !ui.topLanguagePicker.hidden;
  ui.topLanguagePicker.hidden = true;
  ui.top.classList.remove("language-picker-open");

  if (ui.topLanguageDialog.open) {
    ui.topLanguageDialog.close();
  } else if (inlineWasOpen) {
    ui.restartTopLanguage.focus({ preventScroll: true });
  }
}

function setStatus(key = "", kind = "", parameters = {}) {
  state.status = { key, kind, parameters: parameters || {} };
  ui.status.textContent = key ? t(key, parameters) : "";
  ui.status.dataset.kind = kind;
}

function updateTtsLabel() {
  ui.tts.title = t(state.tts ? "ttsOn" : "ttsOff");
}

function updateLogoutLabel() {
  ui.logout.textContent = t(state.passwordRequired ? "logout" : "resetSession");
}

function applyLocale(locale) {
  state.uiLocale = normalizeUiLocale(locale);
  localStorage.setItem("uiLanguage", state.uiLocale);
  document.documentElement.lang = state.uiLocale;
  // Keep conversation geometry stable; only dialogs and text follow RTL reading.
  for (const element of document.querySelectorAll(".modal, .entry-card")) {
    element.dir = isRtlLocale(state.uiLocale) ? "rtl" : "ltr";
  }
  for (const element of document.querySelectorAll("[data-i18n]")) {
    element.textContent = t(element.dataset.i18n);
  }
  for (const element of document.querySelectorAll("[data-i18n-aria-label]")) {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  }
  for (const button of document.querySelectorAll("[data-interface-locale]")) {
    button.setAttribute("aria-pressed", String(button.dataset.interfaceLocale === state.uiLocale));
  }
  if (!state.hasResult) {
    ui.topText.textContent = t("topPrompt");
    ui.bottomText.textContent = t("bottomPrompt");
  }
  if (state.languages.length) fillLanguages();
  updateTtsLabel();
  updateLogoutLabel();
  updatePreRoll();
  updateModelState();
  if (state.status.key) setStatus(state.status.key, state.status.kind, state.status.parameters);
  for (const element of [ui.authError, ui.micError]) {
    if (element.dataset.errorKey) {
      element.textContent = t(element.dataset.errorKey, JSON.parse(element.dataset.errorParameters || "{}"));
    }
  }
  scheduleFit();
}

let fitFrame = 0;
let fitTransitionTimer = 0;

function fitConversationText(element) {
  const content = element.closest(".talk-content");
  if (!content || content.clientWidth === 0 || content.clientHeight === 0) return;
  element.style.fontSize = "";
  element.style.width = "";
  element.style.maxHeight = "";
  const contentStyle = getComputedStyle(content);
  const availableWidth = Math.max(0, content.clientWidth - parseFloat(contentStyle.paddingLeft) - parseFloat(contentStyle.paddingRight));
  let availableHeight = Math.max(0, content.clientHeight - parseFloat(contentStyle.paddingTop) - parseFloat(contentStyle.paddingBottom));
  const icon = content.querySelector(".recording-symbol");
  if (icon && getComputedStyle(icon).display !== "none") {
    const iconStyle = getComputedStyle(icon);
    availableHeight -= icon.getBoundingClientRect().height + parseFloat(iconStyle.marginTop) + parseFloat(iconStyle.marginBottom);
  }
  availableHeight = Math.max(0, availableHeight);
  const maximumFontSize = parseFloat(getComputedStyle(element).fontSize) || 16;
  element.style.width = `${availableWidth}px`;
  element.style.maxHeight = `${availableHeight}px`;

  const fits = (fontSize) => {
    element.style.fontSize = `${fontSize}px`;
    return element.scrollWidth <= element.clientWidth && element.scrollHeight <= element.clientHeight;
  };
  if (fits(maximumFontSize)) return;
  let lower = 0;
  let upper = maximumFontSize;
  for (let step = 0; step < 18; step += 1) {
    const middle = (lower + upper) / 2;
    if (fits(middle)) lower = middle;
    else upper = middle;
  }
  fits(lower);
}

function fitConversationTexts() {
  fitConversationText(ui.topText);
  fitConversationText(ui.bottomText);
}

function scheduleFit({ afterTransition = false } = {}) {
  cancelAnimationFrame(fitFrame);
  fitFrame = requestAnimationFrame(() => {
    fitFrame = requestAnimationFrame(fitConversationTexts);
  });
  if (afterTransition) {
    clearTimeout(fitTransitionTimer);
    fitTransitionTimer = window.setTimeout(fitConversationTexts, 180);
  }
}

function updatePreRoll() {
  ui.preRoll.value = String(state.preRollMs);
  ui.preRollValue.textContent = formatSeconds(state.preRollMs);
  ui.preRollButton.textContent = `↺ ${formatSeconds(state.preRollMs)}`;
}

function updateModelState() {
  const labels = { unloaded: "modelUnloaded", loading: "modelLoadingState", ready: "modelReadyState", unloading: "modelUnloadingState", error: "modelErrorState" };
  ui.modelState.textContent = t(labels[state.model.state] || "modelUnknown");
  ui.modelState.dataset.state = state.model.state;
  ui.loadModel.disabled = ["ready", "loading", "unloading"].includes(state.model.state);
  ui.unloadModel.disabled = state.model.state !== "ready";
  if (state.model.state === "error") setStatus("modelError", "error");
  else if (["ready", "unloaded"].includes(state.model.state)
    && ui.status.dataset.kind === "busy"
    && !["modelLoading", "modelUnloading"].includes(state.status.key)) setStatus("");
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
  if (!ui.topLanguagePicker.hidden || ui.topLanguageDialog.open
    || ui.settings.open || state.activePointer !== null || !event.isPrimary || event.button !== 0) return;
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
    setStatus(error.i18nKey || "micNotReady", "error", error.i18nParameters);
    return;
  }
  state.activePointer = event.pointerId;
  state.activeSide = side;
  state.activeGeneration = generation;
  state.activeUtteranceId = utteranceId;
  state.activeOrder = Math.floor((performance.timeOrigin + performance.now()) * 1000);
  state.activeDirection = direction;
  state.activeTts = state.tts;
  event.currentTarget.setPointerCapture(event.pointerId);
  ui.app.dataset.active = side;
  setStatus("recording", "recording");
  scheduleFit({ afterTransition: true });
  const maximumHold = Math.max(0, MAX_RECORDING_SECONDS * 1000 - effectivePreRoll);
  state.holdTimer = window.setTimeout(() => abortPress("recordingTimedOut"), maximumHold);
}

async function releasePress(event) {
  if (event.pointerId !== state.activePointer) return;
  event.preventDefault();
  const side = state.activeSide;
  const generation = state.activeGeneration;
  const utteranceId = state.activeUtteranceId;
  const order = state.activeOrder;
  const direction = state.activeDirection;
  const tts = state.activeTts;
  resetPressVisuals();
  setStatus("uploading", "busy");
  try {
    const recording = await audioCapture.end(event.timeStamp);
    if (!recording || !gate.accepts(generation)) return;
    const wav = encodePcm16Wav(recording.samples, recording.sampleRate);
    await submitUtterance(wav, side, generation, utteranceId, direction, tts, order);
  } catch (error) {
    if (gate.accepts(generation)) setStatus(error.i18nKey || "requestFailed", "error", error.i18nParameters || { status: "?" });
  }
}

function cancelPress(event) {
  if (event && event.pointerId !== state.activePointer) return;
  abortPress("recordingCancelled");
}

function abortPress(messageKey) {
  if (state.activePointer === null) return;
  audioCapture.cancel();
  resetPressVisuals();
  if (messageKey) setStatus(messageKey, "error");
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
  scheduleFit({ afterTransition: true });
}

async function submitUtterance(wav, side, generation, id, direction, tts, order) {
  const params = new URLSearchParams({
    utterance_id: id, speaker_side: side, source_lang: direction.source,
    target_lang: direction.target, tts: tts ? "1" : "0", generation: String(order),
  });
  await request(`utterances&${params}`, {
    method: "POST", body: wav, headers: { "Content-Type": "audio/wav" },
  });
  if (gate.accepts(generation)) setStatus("processing", "busy");
  await pollUtterance(id, side, generation);
}

async function pollUtterance(id, side, generation) {
  for (;;) {
    if (!gate.accepts(generation)) return;
    const result = await request(`utterances/${encodeURIComponent(id)}`, { method: "GET", mutating: false });
    if (!gate.accepts(generation)) return;
    if (result.status === "complete") {
      showResult(result, side);
      if (result.text_only_reason) setStatus("textOnly", "notice");
      else setStatus("");
      if (state.tts && result.audio_available) await playResult(id, generation);
      return;
    }
    if (result.status === "error") throw localizedError("translationFailed");
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
  state.hasResult = true;
  scheduleFit();
}

async function playResult(id, generation) {
  const response = await fetch(`${API}audio/${encodeURIComponent(id)}`, { credentials: "same-origin", cache: "no-store" });
  if (!response.ok || !gate.accepts(generation)) return;
  const data = await response.arrayBuffer();
  if (!gate.accepts(generation)) return;
  if (audioCapture.context?.state !== "running") {
    setStatus("playbackNeedsMic", "notice");
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
  setStatus(action === "load" ? "modelLoading" : "modelUnloading", "busy");
  try {
    await request(`model/${action}`, { method: "POST" });
    await refreshHealth();
  } catch (error) {
    setStatus(error.i18nKey || "requestFailed", "error", error.i18nParameters || { status: "?" });
  }
}

async function refreshHealth() {
  try {
    state.model = await request("health", { method: "GET", mutating: false });
    updateModelState();
    if (["loading", "unloading"].includes(state.model.state)) setTimeout(refreshHealth, 1200);
    else if (["modelLoading", "modelUnloading"].includes(state.status.key)) {
      const key = state.model.state === "ready" ? "modelReady" : state.model.state === "unloaded" ? "modelUnloadedNotice" : "modelError";
      setStatus(key, state.model.state === "error" ? "error" : "notice");
    }
  } catch (error) {
    setStatus(error.i18nKey || "requestFailed", "error", error.i18nParameters || { status: "?" });
  }
}

ui.authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setFormError(ui.authError);
  try {
    await request("login", { method: "POST", json: { password: ui.password.value } });
    ui.password.value = "";
    await bootstrap();
  } catch (error) {
    setFormError(ui.authError, error);
  }
});

$("#retry-bootstrap").addEventListener("click", () => bootstrap());
ui.micDialog.addEventListener("cancel", (event) => event.preventDefault());

for (const [element, side] of [[ui.top, "top"], [ui.bottom, "bottom"]]) {
  element.addEventListener("pointerdown", (event) => startPress(event, side));
  element.addEventListener("pointerup", releasePress);
  element.addEventListener("pointercancel", cancelPress);
  element.addEventListener("lostpointercapture", (event) => {
    if (state.activePointer === event.pointerId) cancelPress(event);
  });
  element.addEventListener("contextmenu", (event) => {
    if (ui.topLanguagePicker.hidden && !ui.topLanguageDialog.open) event.preventDefault();
  });
}

ui.topLanguageButton.addEventListener("click", () => {
  if (state.activePointer !== null || ui.topLanguageDialog.open) return;
  topLanguageDialogOpener = ui.topLanguageButton;
  ui.topLanguageDialog.showModal();
});
ui.closeTopLanguage.addEventListener("click", () => ui.topLanguageDialog.close());
ui.restartTopLanguage.addEventListener("click", () => {
  if (state.activePointer !== null || ui.settings.open || ui.micDialog.open) return;
  if (ui.topLanguageDialog.open) ui.topLanguageDialog.close();
  stopPlayback();
  // Reopen only the opposite-side choice, retaining microphone and own preferences.
  ui.topLanguagePicker.hidden = false;
  ui.top.classList.add("language-picker-open");
  ui.topLanguageInlineGrid.scrollTop = 0;
  ui.topLanguageInlineGrid.querySelector("button")?.focus({ preventScroll: true });
});
ui.topLanguageDialog.addEventListener("close", () => {
  topLanguageDialogOpener?.focus();
  topLanguageDialogOpener = null;
});

ui.micEnable.addEventListener("click", async () => {
  ui.micEnable.disabled = true;
  setFormError(ui.micError);
  try {
    await audioCapture.enable();
    ui.micDialog.close();
    if (state.topLanguagePending) {
      ui.topLanguagePicker.hidden = false;
      ui.top.classList.add("language-picker-open");
      ui.topLanguageInlineGrid.scrollTop = 0;
      ui.topLanguageInlineGrid.querySelector("button")?.focus({ preventScroll: true });
      setStatus("");
    } else {
      setStatus("micReady", "notice");
      setTimeout(() => { if (state.status.key === "micReady") setStatus(""); }, 1800);
    }
  } catch (error) {
    setFormError(ui.micError, error?.i18nKey ? error : localizedError("micEnableFailed"));
    ui.micEnable.disabled = false;
  }
});

ui.tts.addEventListener("click", () => {
  state.tts = !state.tts;
  localStorage.setItem("tts", state.tts ? "1" : "0");
  ui.tts.setAttribute("aria-pressed", String(state.tts));
  ui.tts.classList.toggle("enabled", state.tts);
  updateTtsLabel();
  if (!state.tts) stopPlayback();
});

ui.bottomLanguage.addEventListener("change", () => {
  localStorage.setItem("bottomLanguage", ui.bottomLanguage.value);
});

for (const container of document.querySelectorAll("[data-interface-choices]")) {
  for (const language of UI_LANGUAGES) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "language-choice";
    button.dataset.interfaceLocale = language.locale;
    button.setAttribute("aria-label", language.name);
    button.lang = language.locale;
    const flag = document.createElement("span");
    flag.className = "language-flag";
    flag.setAttribute("aria-hidden", "true");
    flag.textContent = language.flag;
    const name = document.createElement("span");
    name.className = "language-name";
    name.dir = "auto";
    name.textContent = language.name;
    button.append(flag, name);
    container.append(button);
    button.addEventListener("click", () => {
      const choice = interfaceChoice(language.locale);
      // Persist before bootstrap too (password/offline screen); never change the top language.
      localStorage.setItem("bottomLanguage", choice.code);
      if (state.languages.some(({ code }) => code === choice.code)) ui.bottomLanguage.value = choice.code;
      applyLocale(choice.locale);
    });
  }
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
    if (state.activePointer !== null) abortPress("appSwitchCancelled");
    stopPlayback();
    audioCapture.suspend().catch(() => {});
  } else if (audioCapture.context?.state === "suspended") {
    setStatus("resumeMic", "notice");
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
  abortPress("networkInterrupted");
  audioCapture.cancel();
  stopPlayback();
  setStatus("noNetwork", "error");
});

window.addEventListener("resize", scheduleFit);
window.addEventListener("orientationchange", () => scheduleFit({ afterTransition: true }));
if ("ResizeObserver" in window) {
  const conversationResizeObserver = new ResizeObserver(() => scheduleFit());
  conversationResizeObserver.observe(ui.top);
  conversationResizeObserver.observe(ui.bottom);
}

if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
applyLocale(state.uiLocale);
bootstrap();
