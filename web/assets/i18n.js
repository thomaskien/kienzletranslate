export const DEFAULT_UI_LOCALE = "de";
export const UI_LOCALES = ["de", "en"];

export const MESSAGES = {
  de: {
    uiLanguage: "Oberflächensprache",
    german: "Deutsch",
    english: "English",
    authEyebrow: "Lokaler Gesprächsübersetzer",
    authIntro: "Mit dem Server-Passwort anmelden. Bei einer neuen Installation zuerst die Einrichtung am Server abschließen.",
    password: "Passwort",
    login: "Anmelden",
    setup: "Ersteinrichtung öffnen",
    offlineEyebrow: "Keine Verbindung",
    offlineTitle: "Lokaler Server nicht erreichbar",
    offlineBody: "Bitte WLAN und Serveradresse prüfen. Gesprächsdaten werden nicht offline gespeichert.",
    retry: "Erneut versuchen",
    topPrompt: "Oben gedrückt halten und sprechen",
    bottomPrompt: "Unten gedrückt halten und sprechen",
    topArea: "Obere Sprechfläche: zum Sprechen gedrückt halten",
    bottomArea: "Untere Sprechfläche: zum Sprechen gedrückt halten",
    controls: "Sprachen und Sprachausgabe",
    topLanguage: "Sprache oben",
    bottomLanguage: "Sprache unten",
    direction: "Übersetzung in beide Richtungen",
    ttsToggle: "Sprachausgabe umschalten",
    ttsOn: "Sprachausgabe ausschalten",
    ttsOff: "Sprachausgabe einschalten",
    preRollSetting: "Vorlauf einstellen",
    settings: "Einstellungen",
    micEyebrow: "Einmalige Freigabe",
    micTitle: "Mikrofon aktivieren",
    micBody: "Das Mikrofon bleibt im Vordergrund geöffnet. Maximal drei Sekunden Ton liegen nur lokal im flüchtigen Vorlaufpuffer. Erst beim Loslassen einer Sprechfläche wird genau die Aufnahme an Ihren lokalen Server gesendet.",
    micEnable: "Mikrofon aktivieren",
    settingsEyebrow: "Lokale Einstellungen",
    settingsTitle: "Gespräch",
    audioPreRoll: "Audio-Vorlauf",
    model: "Seamless-Modell",
    modelLoad: "Modell laden",
    modelUnload: "Entladen",
    modelBusyNote: "Entladen ist nicht möglich, solange Aufträge verarbeitet werden.",
    logout: "Abmelden",
    resetSession: "Sitzung zurücksetzen",
    apply: "Übernehmen",
    orientation: "Für das beste Gesprächserlebnis das iPad bitte hochkant drehen.",
    commonGermany: "Häufig in Deutschland",
    otherLanguages: "Weitere Sprachen",
    modelUnloaded: "nicht geladen",
    modelLoadingState: "wird geladen",
    modelReadyState: "bereit",
    modelUnloadingState: "wird entladen",
    modelErrorState: "Fehler",
    modelUnknown: "unbekannt",
    audioContextStart: "Der Audiokontext konnte nicht gestartet werden.",
    audioUnsupported: "Dieser Browser unterstützt die benötigte Audioaufnahme nicht.",
    micAccessEnded: "Der Mikrofonzugriff wurde beendet.",
    audioInterrupted: "Audio wurde unterbrochen. Bitte Mikrofon erneut aktivieren.",
    micNotReady: "Das Mikrofon ist nicht bereit.",
    recordingTooLong: "Die Aufnahme wurde verworfen, weil sie länger als 60 Sekunden war.",
    emptyRecording: "Die Aufnahme war leer. Bitte erneut versuchen.",
    recordingInterrupted: "Audioaufnahme unterbrochen. Bitte erneut versuchen.",
    networkUnavailable: "Der lokale Server ist nicht erreichbar. Netzwerkverbindung prüfen.",
    serverError: "Serverfehler ({status})",
    loginFailed: "Zugangspasswort stimmt nicht.",
    authenticationRequired: "Bitte anmelden.",
    sessionReload: "Sitzung bitte neu laden.",
    accessDenied: "Zugriff abgewiesen.",
    inputTooLarge: "Eingabe oder Aufnahme ist zu groß.",
    invalidRecording: "Ungültige Aufnahmedaten.",
    notFound: "Nicht gefunden.",
    requestFailed: "Die Anfrage ist fehlgeschlagen.",
    micEnableFailed: "Das Mikrofon konnte nicht aktiviert werden. Bitte die Browserfreigabe prüfen.",
    recording: "Aufnahme läuft …",
    recordingTimedOut: "Die Aufnahme wurde nach 60 Sekunden verworfen.",
    uploading: "Wird übertragen …",
    processing: "Verarbeitung läuft …",
    textOnly: "Nur Text: Sprachausgabe ist für dieses Ergebnis nicht verfügbar.",
    translationFailed: "Die Übersetzung ist fehlgeschlagen.",
    playbackNeedsMic: "Bitte Mikrofon aktivieren, um Audio wiederzugeben.",
    modelLoading: "Modell wird geladen …",
    modelUnloading: "Modell wird entladen …",
    modelReady: "Modell bereit.",
    modelUnloadedNotice: "Modell entladen.",
    modelError: "Das Modell meldet einen Fehler.",
    recordingCancelled: "Aufnahme abgebrochen.",
    micReady: "Mikrofon bereit.",
    appSwitchCancelled: "Aufnahme wegen App-Wechsel abgebrochen.",
    resumeMic: "Zum Fortfahren Mikrofon erneut aktivieren.",
    networkInterrupted: "Netzwerk unterbrochen. Aufnahme verworfen.",
    noNetwork: "Keine Netzwerkverbindung zum Server.",
  },
  en: {
    uiLanguage: "Interface language",
    german: "Deutsch",
    english: "English",
    authEyebrow: "Local conversation translator",
    authIntro: "Sign in with the server password. For a new installation, finish setup on the server first.",
    password: "Password",
    login: "Sign in",
    setup: "Open initial setup",
    offlineEyebrow: "No connection",
    offlineTitle: "Local server unavailable",
    offlineBody: "Check Wi-Fi and the server address. Conversation data is not stored offline.",
    retry: "Try again",
    topPrompt: "Hold the top area and speak",
    bottomPrompt: "Hold the bottom area and speak",
    topArea: "Top speaking area: hold to speak",
    bottomArea: "Bottom speaking area: hold to speak",
    controls: "Languages and speech output",
    topLanguage: "Top language",
    bottomLanguage: "Bottom language",
    direction: "Translation in both directions",
    ttsToggle: "Toggle speech output",
    ttsOn: "Turn off speech output",
    ttsOff: "Turn on speech output",
    preRollSetting: "Set pre-roll",
    settings: "Settings",
    micEyebrow: "One-time permission",
    micTitle: "Enable microphone",
    micBody: "The microphone remains open while the app is in the foreground. Up to three seconds of audio stay only in the temporary local pre-roll buffer. The recording is sent to your local server only when you release a speaking area.",
    micEnable: "Enable microphone",
    settingsEyebrow: "Local settings",
    settingsTitle: "Conversation",
    audioPreRoll: "Audio pre-roll",
    model: "Seamless model",
    modelLoad: "Load model",
    modelUnload: "Unload",
    modelBusyNote: "The model cannot be unloaded while jobs are being processed.",
    logout: "Sign out",
    resetSession: "Reset session",
    apply: "Apply",
    orientation: "For the best conversation experience, rotate the iPad to portrait orientation.",
    commonGermany: "Common in Germany",
    otherLanguages: "Other languages",
    modelUnloaded: "not loaded",
    modelLoadingState: "loading",
    modelReadyState: "ready",
    modelUnloadingState: "unloading",
    modelErrorState: "Error",
    modelUnknown: "unknown",
    audioContextStart: "The audio context could not be started.",
    audioUnsupported: "This browser does not support the required audio recording features.",
    micAccessEnded: "Microphone access ended.",
    audioInterrupted: "Audio was interrupted. Enable the microphone again.",
    micNotReady: "The microphone is not ready.",
    recordingTooLong: "The recording was discarded because it exceeded 60 seconds.",
    emptyRecording: "The recording was empty. Please try again.",
    recordingInterrupted: "Audio recording was interrupted. Please try again.",
    networkUnavailable: "The local server is unavailable. Check the network connection.",
    serverError: "Server error ({status})",
    loginFailed: "The server password is incorrect.",
    authenticationRequired: "Please sign in.",
    sessionReload: "Please reload the session.",
    accessDenied: "Access denied.",
    inputTooLarge: "The input or recording is too large.",
    invalidRecording: "Invalid recording data.",
    notFound: "Not found.",
    requestFailed: "The request failed.",
    micEnableFailed: "The microphone could not be enabled. Check the browser permission.",
    recording: "Recording …",
    recordingTimedOut: "The recording was discarded after 60 seconds.",
    uploading: "Uploading …",
    processing: "Processing …",
    textOnly: "Text only: speech output is not available for this result.",
    translationFailed: "Translation failed.",
    playbackNeedsMic: "Enable the microphone to play audio.",
    modelLoading: "Loading model …",
    modelUnloading: "Unloading model …",
    modelReady: "Model ready.",
    modelUnloadedNotice: "Model unloaded.",
    modelError: "The model reported an error.",
    recordingCancelled: "Recording cancelled.",
    micReady: "Microphone ready.",
    appSwitchCancelled: "Recording cancelled because the app was switched.",
    resumeMic: "Enable the microphone again to continue.",
    networkInterrupted: "Network interrupted. Recording discarded.",
    noNetwork: "No network connection to the server.",
  },
};

export const COMMON_IN_GERMANY = [
  "deu", "eng", "tur", "arb", "rus", "ukr", "pol", "ron", "ita",
  "bul", "hrv", "bos", "srp", "ckb", "pes", "ell", "fra", "spa",
];

export const MODEL_TO_BCP47 = {
  afr: "af", amh: "am", arb: "ar", ary: "ar-MA", arz: "ar-EG", hye: "hy",
  asm: "as", eus: "eu", bel: "be", ben: "bn", bos: "bs", bul: "bg", mya: "my",
  yue: "yue", cat: "ca", ceb: "ceb", cmn_Hant: "zh-Hant", cmn: "zh-Hans",
  deu: "de", dan: "da", eng: "en", est: "et", fin: "fi", fra: "fr", glg: "gl",
  lug: "lg", kat: "ka", ell: "el", guj: "gu", khk: "mn", heb: "he", hin: "hi",
  isl: "is", ibo: "ig", ind: "id", gle: "ga", ita: "it", jpn: "ja", jav: "jv",
  kan: "kn", kaz: "kk", khm: "km", kor: "ko", hrv: "hr", ckb: "ckb", kir: "ky",
  lao: "lo", lvs: "lv", lit: "lt", luo: "luo", mkd: "mk", mai: "mai", mal: "ml",
  mlt: "mt", mar: "mr", mni: "mni", npi: "ne", nld: "nl", fuv: "fuv", azj: "az",
  uzn: "uz", nob: "nb", nno: "nn", nya: "ny", ory: "or", pes: "fa", pol: "pl",
  por: "pt", pan: "pa", ron: "ro", rus: "ru", swe: "sv", srp: "sr", sna: "sn",
  snd: "sd", slk: "sk", slv: "sl", som: "so", pbt: "ps", spa: "es", swh: "sw",
  tgl: "fil", tgk: "tg", tam: "ta", tel: "te", tha: "th", ces: "cs", tur: "tr",
  ukr: "uk", hun: "hu", urd: "ur", vie: "vi", cym: "cy", gaz: "om", yor: "yo",
  zul: "zu",
};

const NAME_FALLBACKS = {
  de: {
    arb: "Arabisch (Hocharabisch)", ary: "Arabisch (Marokko)", arz: "Arabisch (Ägypten)",
    cmn: "Chinesisch (vereinfacht)", cmn_Hant: "Chinesisch (traditionell)",
    ckb: "Kurdisch (Sorani)", khk: "Mongolisch (Halh)", pes: "Persisch",
    pbt: "Paschtu (Süd)", yue: "Kantonesisch", fuv: "Fulfulde (Nigeria)",
  },
  en: {
    arb: "Arabic (Modern Standard)", ary: "Arabic (Morocco)", arz: "Arabic (Egypt)",
    cmn: "Chinese (Simplified)", cmn_Hant: "Chinese (Traditional)",
    ckb: "Kurdish (Sorani)", khk: "Mongolian (Halh)", pes: "Persian",
    pbt: "Pashto (Southern)", yue: "Cantonese", fuv: "Fulfulde (Nigeria)",
  },
};

export function normalizeUiLocale(value) {
  return UI_LOCALES.includes(value) ? value : DEFAULT_UI_LOCALE;
}

export function translate(locale, key, parameters = {}) {
  const template = MESSAGES[normalizeUiLocale(locale)][key] ?? MESSAGES.de[key] ?? key;
  return template.replace(/\{(\w+)\}/g, (_, name) => String(parameters[name] ?? ""));
}

export function languageDisplayName(language, locale) {
  const normalized = normalizeUiLocale(locale);
  const explicitFallback = NAME_FALLBACKS[normalized][language.code];
  if (explicitFallback) return explicitFallback;
  const languageTag = MODEL_TO_BCP47[language.code];
  if (languageTag && typeof Intl.DisplayNames === "function") {
    try {
      const name = new Intl.DisplayNames([normalized], { type: "language", fallback: "none" }).of(languageTag);
      if (name) return name;
    } catch {
      // Fall through to the readable server-supplied name for uncommon codes.
    }
  }
  return language.name || language.code;
}

export function groupLanguages(languages, locale) {
  const normalized = normalizeUiLocale(locale);
  const commonCodes = new Set(COMMON_IN_GERMANY);
  const collator = new Intl.Collator(normalized, { sensitivity: "base" });
  const groups = { common: [], other: [] };
  for (const language of languages) {
    const item = { ...language, displayName: languageDisplayName(language, normalized) };
    groups[commonCodes.has(language.code) ? "common" : "other"].push(item);
  }
  const compare = (left, right) => collator.compare(left.displayName, right.displayName) || left.code.localeCompare(right.code);
  groups.common.sort(compare);
  groups.other.sort(compare);
  return groups;
}
