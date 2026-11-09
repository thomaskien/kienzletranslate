import { ADDITIONAL_MESSAGES } from "./locales.js";

export const DEFAULT_UI_LOCALE = "de";
// Stable order: the two original choices first, then the frequent-language group.
export const UI_LANGUAGES = [
  { locale: "de", code: "deu", flag: "🇩🇪", name: "Deutsch" },
  { locale: "en", code: "eng", flag: "🇬🇧", name: "English" },
  { locale: "tr", code: "tur", flag: "🇹🇷", name: "Türkçe" },
  { locale: "ar", code: "arb", flag: "🇸🇦", name: "العربية" },
  { locale: "ru", code: "rus", flag: "🇷🇺", name: "Русский" },
  { locale: "uk", code: "ukr", flag: "🇺🇦", name: "Українська" },
  { locale: "pl", code: "pol", flag: "🇵🇱", name: "Polski" },
  { locale: "ro", code: "ron", flag: "🇷🇴", name: "Română" },
  { locale: "it", code: "ita", flag: "🇮🇹", name: "Italiano" },
  { locale: "bg", code: "bul", flag: "🇧🇬", name: "Български" },
  { locale: "hr", code: "hrv", flag: "🇭🇷", name: "Hrvatski" },
  { locale: "bs", code: "bos", flag: "🇧🇦", name: "Bosanski" },
  { locale: "sr", code: "srp", flag: "🇷🇸", name: "Српски" },
  { locale: "ckb", code: "ckb", flag: "🇮🇶", name: "کوردی" },
  { locale: "fa", code: "pes", flag: "🇮🇷", name: "فارسی" },
  { locale: "el", code: "ell", flag: "🇬🇷", name: "Ελληνικά" },
  { locale: "fr", code: "fra", flag: "🇫🇷", name: "Français" },
  { locale: "es", code: "spa", flag: "🇪🇸", name: "Español" },
];
export const UI_LOCALES = UI_LANGUAGES.map(({ locale }) => locale);
export const isRtlLocale = (locale) => ["ar", "ckb", "fa"].includes(locale);

export const MESSAGES = {
  de: {
    uiLanguage: "Oberflächensprache",
    yourLanguage: "Ihre Sprache",
    german: "Deutsch",
    english: "English",
    authEyebrow: "Lokaler Gesprächsübersetzer",
    authIntro: "Mit dem Server-Passwort anmelden.",
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
    bottomLanguage: "Ihre Sprache",
    direction: "Übersetzung in beide Richtungen",
    ttsToggle: "Sprachausgabe umschalten",
    ttsOn: "Sprachausgabe ausschalten",
    ttsOff: "Sprachausgabe einschalten",
    preRollSetting: "Vorlauf einstellen",
    settings: "Einstellungen",
    micEyebrow: "Push to Talk",
    micTitle: "Bereit zum Gespräch",
    micBody: "Eigene Fläche gedrückt halten und sprechen. Zum Übersetzen loslassen.",
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
    close: "Schließen",
    restartLanguage: "Sprachauswahl gegenüber neu starten",
    orientation: "Für mehr Platz das Gerät bitte hochkant drehen.",
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
    yourLanguage: "Your language",
    german: "Deutsch",
    english: "English",
    authEyebrow: "Local conversation translator",
    authIntro: "Sign in with the server password.",
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
    bottomLanguage: "Your language",
    direction: "Translation in both directions",
    ttsToggle: "Toggle speech output",
    ttsOn: "Turn off speech output",
    ttsOff: "Turn on speech output",
    preRollSetting: "Set pre-roll",
    settings: "Settings",
    micEyebrow: "Push to talk",
    micTitle: "Ready to talk",
    micBody: "Hold your area and speak. Release to translate.",
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
    close: "Close",
    restartLanguage: "Restart opposite-side language selection",
    orientation: "For more space, rotate your device to portrait.",
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
  ...ADDITIONAL_MESSAGES,
};

const RESOURCE_MESSAGES = {
  "de": [
    "Gegenüber gedrückt halten und mindestens fünf Sekunden sprechen.",
    "Sprache nicht sicher erkannt. Bitte eine Fahne auswählen.",
    "Grafikspeicher derzeit belegt. Bitte später erneut versuchen.",
    "Bitte das Modell in den Einstellungen laden."
  ],
  "en": [
    "Hold the opposite area and speak for at least five seconds.",
    "Language uncertain. Please select a flag.",
    "GPU memory is currently occupied. Please try again later.",
    "Please load the model in settings."
  ],
  "fr": [
    "Maintenez la zone en face et parlez au moins cinq secondes.",
    "Langue incertaine. Choisissez un drapeau.",
    "Mémoire GPU occupée. Réessayez plus tard.",
    "Chargez le modèle dans les réglages."
  ],
  "es": [
    "Mantenga pulsada la zona opuesta y hable al menos cinco segundos.",
    "Idioma incierto. Seleccione una bandera.",
    "Memoria de la GPU ocupada. Inténtelo más tarde.",
    "Cargue el modelo en los ajustes."
  ],
  "it": [
    "Tieni premuta l’area di fronte e parla per almeno cinque secondi.",
    "Lingua incerta. Seleziona una bandiera.",
    "Memoria GPU occupata. Riprova più tardi.",
    "Carica il modello nelle impostazioni."
  ],
  "tr": [
    "Karşı alana basılı tutup en az beş saniye konuşun.",
    "Dil kesin belirlenemedi. Bir bayrak seçin.",
    "GPU belleği şu anda dolu. Daha sonra tekrar deneyin.",
    "Modeli ayarlardan yükleyin."
  ],
  "ar": [
    "اضغط مطولًا على المنطقة المقابلة وتحدث لخمس ثوانٍ على الأقل.",
    "تعذر تحديد اللغة بثقة. اختر علمًا.",
    "ذاكرة معالج الرسومات مشغولة حاليًا. حاول لاحقًا.",
    "حمّل النموذج من الإعدادات."
  ],
  "ru": [
    "Удерживайте противоположную область и говорите не менее пяти секунд.",
    "Язык не определён уверенно. Выберите флаг.",
    "Память GPU занята. Попробуйте позже.",
    "Загрузите модель в настройках."
  ],
  "uk": [
    "Утримуйте протилежну ділянку й говоріть щонайменше п’ять секунд.",
    "Мову не визначено впевнено. Виберіть прапор.",
    "Пам’ять GPU зайнята. Спробуйте пізніше.",
    "Завантажте модель у налаштуваннях."
  ],
  "pl": [
    "Przytrzymaj obszar naprzeciwko i mów przez co najmniej pięć sekund.",
    "Nie rozpoznano pewnie języka. Wybierz flagę.",
    "Pamięć GPU jest zajęta. Spróbuj później.",
    "Załaduj model w ustawieniach."
  ],
  "ro": [
    "Țineți apăsată zona opusă și vorbiți cel puțin cinci secunde.",
    "Limba nu a fost identificată sigur. Alegeți un steag.",
    "Memoria GPU este ocupată. Încercați mai târziu.",
    "Încărcați modelul din setări."
  ],
  "bg": [
    "Задръжте срещуположната област и говорете поне пет секунди.",
    "Езикът не е разпознат сигурно. Изберете флаг.",
    "Паметта на GPU е заета. Опитайте по-късно.",
    "Заредете модела от настройките."
  ],
  "hr": [
    "Držite suprotno područje i govorite najmanje pet sekundi.",
    "Jezik nije pouzdano prepoznat. Odaberite zastavu.",
    "GPU memorija je zauzeta. Pokušajte kasnije.",
    "Učitajte model u postavkama."
  ],
  "bs": [
    "Držite suprotno područje i govorite najmanje pet sekundi.",
    "Jezik nije pouzdano prepoznat. Odaberite zastavu.",
    "GPU memorija je zauzeta. Pokušajte kasnije.",
    "Učitajte model u postavkama."
  ],
  "sr": [
    "Држите супротну област и говорите најмање пет секунди.",
    "Језик није поуздано препознат. Изаберите заставу.",
    "GPU меморија је заузета. Покушајте касније.",
    "Учитајте модел у подешавањима."
  ],
  "ckb": [
    "بەشی بەرامبەر ڕابگرە و لانیکەم پێنج چرکە قسە بکە.",
    "زمان بە دڵنیایی نەناسرا. ئاڵایەک هەڵبژێرە.",
    "بیرگەی GPU ئێستا پڕە. دواتر هەوڵ بدەرەوە.",
    "مۆدێلەکە لە ڕێکخستنەکان بار بکە."
  ],
  "fa": [
    "ناحیه روبه‌رو را نگه دارید و دست‌کم پنج ثانیه صحبت کنید.",
    "زبان با اطمینان شناسایی نشد. یک پرچم انتخاب کنید.",
    "حافظه پردازنده گرافیکی اشغال است. بعداً تلاش کنید.",
    "مدل را در تنظیمات بارگذاری کنید."
  ],
  "el": [
    "Κρατήστε πατημένη την απέναντι περιοχή και μιλήστε τουλάχιστον πέντε δευτερόλεπτα.",
    "Η γλώσσα δεν αναγνωρίστηκε με βεβαιότητα. Επιλέξτε σημαία.",
    "Η μνήμη GPU είναι κατειλημμένη. Δοκιμάστε αργότερα.",
    "Φορτώστε το μοντέλο από τις ρυθμίσεις."
  ]
};
for (const [locale, [automaticPrompt, automaticFailed, gpuMemoryBusy, modelNotReady]] of Object.entries(RESOURCE_MESSAGES)) {
  Object.assign(MESSAGES[locale], { automaticPrompt, automaticFailed, gpuMemoryBusy, modelNotReady });
}


export const COMMON_IN_GERMANY = UI_LANGUAGES.map(({ code }) => code);

const LANGUAGE_REGIONS = {
  afr: "ZA", amh: "ET", ary: "MA", arz: "EG", hye: "AM", asm: "IN", eus: "ES",
  bel: "BY", ben: "BD", mya: "MM", yue: "HK", cat: "ES", ceb: "PH", cmn: "CN",
  cmn_Hant: "TW", dan: "DK", est: "EE", fin: "FI", glg: "ES", lug: "UG", kat: "GE",
  guj: "IN", khk: "MN", heb: "IL", hin: "IN", isl: "IS", ibo: "NG", ind: "ID",
  gle: "IE", jpn: "JP", jav: "ID", kan: "IN", kaz: "KZ", khm: "KH", kor: "KR",
  kir: "KG", lao: "LA", lvs: "LV", lit: "LT", luo: "KE", mkd: "MK", mai: "IN",
  mal: "IN", mlt: "MT", mar: "IN", mni: "IN", npi: "NP", nld: "NL", fuv: "NG",
  azj: "AZ", uzn: "UZ", nob: "NO", nno: "NO", nya: "MW", ory: "IN", por: "PT",
  pan: "IN", swe: "SE", sna: "ZW", snd: "PK", slk: "SK", slv: "SI", som: "SO",
  pbt: "AF", swh: "TZ", tgl: "PH", tgk: "TJ", tam: "IN", tel: "IN", tha: "TH",
  ces: "CZ", hun: "HU", urd: "PK", vie: "VN", cym: "GB", gaz: "ET", yor: "NG", zul: "ZA",
};

export function languageFlag(code) {
  const common = UI_LANGUAGES.find((language) => language.code === code);
  if (common) return common.flag;
  const region = LANGUAGE_REGIONS[code];
  return region ? [...region].map((letter) => String.fromCodePoint(127397 + letter.charCodeAt(0))).join("") : "🌐";
}

export function interfaceChoice(locale) {
  return UI_LANGUAGES.find((language) => language.locale === normalizeUiLocale(locale));
}

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
  const explicitFallback = NAME_FALLBACKS[normalized]?.[language.code];
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
  return UI_LANGUAGES.find((item) => item.code === language.code)?.name || language.name || language.code;
}

export function nativeLanguageName(language) {
  const common = UI_LANGUAGES.find((item) => item.code === language.code);
  if (common) return common.name;
  const languageTag = MODEL_TO_BCP47[language.code];
  if (languageTag && typeof Intl.DisplayNames === "function") {
    try {
      const name = new Intl.DisplayNames([languageTag], { type: "language", fallback: "none" }).of(languageTag);
      if (name) return name;
    } catch {
      // Fall through to the readable server-supplied name.
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
