<?php
declare(strict_types=1);

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store, private');
header("Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; worker-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
header('Referrer-Policy: no-referrer');
header('X-Content-Type-Options: nosniff');
?>
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
  <meta name="theme-color" content="#050706">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="kienzletranslate">
  <title>kienzletranslate</title>
  <link rel="manifest" href="/manifest.webmanifest">
  <link rel="icon" href="/assets/icon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/assets/icon-180.png">
  <link rel="stylesheet" href="/assets/styles.css">
  <script type="module" src="/assets/app.js"></script>
</head>
<body>
  <main id="auth-view" class="entry-view" hidden>
    <section class="entry-card" aria-labelledby="login-title">
      <div class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 64 64"><path d="M13 23h29l-8-8m17 26H22l8 8"/></svg>
      </div>
      <p class="eyebrow" data-i18n="authEyebrow">Lokaler Gesprächsübersetzer</p>
      <h1 id="login-title">kienzletranslate</h1>
      <p data-i18n="authIntro">Mit dem Server-Passwort anmelden. Bei einer neuen Installation zuerst die Einrichtung am Server abschließen.</p>
      <div class="locale-control">
        <p data-i18n="yourLanguage">Ihre Sprache</p>
        <div class="language-grid" data-interface-choices role="group" aria-label="Ihre Sprache" data-i18n-aria-label="yourLanguage" dir="ltr"></div>
      </div>
      <form id="login-form">
        <label for="password" data-i18n="password">Passwort</label>
        <input id="password" name="password" type="password" autocomplete="current-password" required autofocus>
        <button class="primary-button" type="submit" data-i18n="login">Anmelden</button>
        <p id="auth-error" class="form-error" role="alert"></p>
      </form>
      <a class="setup-link" href="/setup.php" data-i18n="setup">Ersteinrichtung öffnen</a>
    </section>
  </main>

  <main id="offline-view" class="entry-view" hidden>
    <section class="entry-card" aria-labelledby="offline-title">
      <p class="eyebrow" data-i18n="offlineEyebrow">Keine Verbindung</p>
      <h1 id="offline-title" data-i18n="offlineTitle">Lokaler Server nicht erreichbar</h1>
      <p id="offline-message" data-i18n="offlineBody">Bitte WLAN und Serveradresse prüfen. Gesprächsdaten werden nicht offline gespeichert.</p>
      <div class="locale-control">
        <p data-i18n="yourLanguage">Ihre Sprache</p>
        <div class="language-grid" data-interface-choices role="group" aria-label="Ihre Sprache" data-i18n-aria-label="yourLanguage" dir="ltr"></div>
      </div>
      <button id="retry-bootstrap" class="primary-button" type="button" data-i18n="retry">Erneut versuchen</button>
    </section>
  </main>

  <main id="app-view" class="translator" hidden>
    <section id="top-side" class="talk-side talk-side--top" aria-label="Obere Sprechfläche: zum Sprechen gedrückt halten" data-i18n-aria-label="topArea">
      <div class="talk-content talk-content--rotated">
        <div class="recording-symbol" aria-hidden="true">
          <span class="pulse pulse--one"></span><span class="pulse pulse--two"></span>
          <svg viewBox="0 0 64 64"><path d="M32 39a9 9 0 0 0 9-9V15a9 9 0 0 0-18 0v15a9 9 0 0 0 9 9Zm-16-9a16 16 0 0 0 32 0M32 46v9m-9 0h18"/></svg>
        </div>
        <p id="top-text" class="result-text" dir="auto">Oben gedrückt halten und sprechen</p>
      </div>
      <div id="top-language-picker" class="top-language-picker" hidden>
        <div id="top-language-inline-grid" class="model-language-scroll" role="group" aria-label="Sprache oben" data-i18n-aria-label="topLanguage"></div>
      </div>
    </section>

    <section id="bottom-side" class="talk-side talk-side--bottom" aria-label="Untere Sprechfläche: zum Sprechen gedrückt halten" data-i18n-aria-label="bottomArea">
      <div class="talk-content">
        <div class="recording-symbol" aria-hidden="true">
          <span class="pulse pulse--one"></span><span class="pulse pulse--two"></span>
          <svg viewBox="0 0 64 64"><path d="M32 39a9 9 0 0 0 9-9V15a9 9 0 0 0-18 0v15a9 9 0 0 0 9 9Zm-16-9a16 16 0 0 0 32 0M32 46v9m-9 0h18"/></svg>
        </div>
        <p id="bottom-text" class="result-text" dir="auto">Unten gedrückt halten und sprechen</p>
      </div>
    </section>

    <div class="control-deck" dir="ltr" aria-label="Sprachen und Sprachausgabe" data-i18n-aria-label="controls">
      <div class="language-control">
        <span class="sr-only" data-i18n="topLanguage">Sprache oben</span>
        <span aria-hidden="true">↑</span>
        <button id="top-language-button" class="language-picker-trigger" type="button" aria-label="Sprache oben" data-i18n-aria-label="topLanguage" aria-haspopup="dialog">
          <span id="top-language-flag" class="control-language-flag" aria-hidden="true"></span>
          <span id="top-language-caption" class="control-language-caption" dir="auto"></span>
          <span class="language-chevron" aria-hidden="true">⌄</span>
        </button>
        <select id="top-language" hidden aria-hidden="true" tabindex="-1"></select>
      </div>
      <div class="direction-symbol" aria-label="Übersetzung in beide Richtungen" data-i18n-aria-label="direction">
        <svg viewBox="0 0 64 64"><path d="M10 22h39l-9-9m14 29H15l9 9"/></svg>
      </div>
      <button id="tts-toggle" class="sound-toggle" type="button" aria-pressed="true" aria-label="Sprachausgabe umschalten" data-i18n-aria-label="ttsToggle">
        <svg viewBox="0 0 64 64" aria-hidden="true"><path d="M10 27v10h10l13 11V16L20 27H10Zm31-3a13 13 0 0 1 0 16m7-23a23 23 0 0 1 0 30"/></svg>
        <span class="mute-slash" aria-hidden="true"></span>
      </button>
      <label class="language-control">
        <span class="sr-only" data-i18n="bottomLanguage">Ihre Sprache</span>
        <select id="bottom-language" dir="auto" aria-label="Ihre Sprache" data-i18n-aria-label="bottomLanguage"></select>
        <span aria-hidden="true">↓</span>
      </label>
    </div>

    <div id="status-message" class="status-message" role="status" aria-live="polite"></div>
    <div class="lower-tools">
      <button id="pre-roll-button" class="utility-button" type="button" aria-label="Vorlauf einstellen" data-i18n-aria-label="preRollSetting">↺ 1,0 s</button>
      <div class="utility-group">
      <button id="restart-top-language" class="utility-button icon-button" type="button" aria-label="Sprachauswahl gegenüber neu starten" data-i18n-aria-label="restartLanguage">
        <svg viewBox="0 0 64 64" aria-hidden="true"><path d="M50 24A20 20 0 1 0 51 39M50 10v14H36"/></svg>
      </button>
      <button id="settings-button" class="utility-button icon-button" type="button" aria-label="Einstellungen" data-i18n-aria-label="settings">
        <svg viewBox="0 0 64 64" aria-hidden="true"><path d="M32 22a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm0-12 4 7 8-1 2 8 7 4-4 7 4 7-7 4-2 8-8-1-4 7-4-7-8 1-2-8-7-4 4-7-4-7 7-4 2-8 8 1 4-7Z"/></svg>
      </button>
      </div>
    </div>
  </main>

  <dialog id="microphone-dialog" class="modal welcome-modal" aria-labelledby="microphone-title">
    <div class="welcome-heading">
      <h2 id="microphone-title" data-i18n="micTitle">Bereit zum Gespräch</h2>
      <span class="app-version" dir="ltr">v1.4</span>
    </div>
    <p class="ptt-hint" data-i18n="micBody">Eigene Fläche gedrückt halten und sprechen. Zum Übersetzen loslassen.</p>
    <div class="locale-control">
      <p data-i18n="yourLanguage">Ihre Sprache</p>
      <div class="language-grid" data-interface-choices role="group" aria-label="Ihre Sprache" data-i18n-aria-label="yourLanguage" dir="ltr"></div>
    </div>
    <button id="enable-microphone" class="primary-button" type="button" data-i18n="micEnable">Mikrofon aktivieren</button>
    <p id="microphone-error" class="form-error" role="alert"></p>
  </dialog>

  <dialog id="top-language-dialog" class="modal top-language-dialog" aria-labelledby="top-language-title">
    <div class="language-dialog-heading">
      <h2 id="top-language-title" data-i18n="topLanguage">Sprache oben</h2>
      <button id="close-top-language" class="dialog-close-button" type="button" data-i18n-aria-label="close" aria-label="Schließen">×</button>
    </div>
    <div id="top-language-dialog-grid" class="model-language-scroll" role="group" aria-label="Sprache oben" data-i18n-aria-label="topLanguage"></div>
  </dialog>

  <dialog id="settings-dialog" class="modal settings-modal" aria-labelledby="settings-title">
    <form method="dialog">
      <p class="eyebrow" data-i18n="settingsEyebrow">Lokale Einstellungen</p>
      <h2 id="settings-title" data-i18n="settingsTitle">Gespräch</h2>
      <div class="locale-control">
        <p data-i18n="yourLanguage">Ihre Sprache</p>
        <div class="language-grid" data-interface-choices role="group" aria-label="Ihre Sprache" data-i18n-aria-label="yourLanguage" dir="ltr"></div>
      </div>
      <div class="setting-row">
        <label for="pre-roll" data-i18n="audioPreRoll">Audio-Vorlauf</label>
        <output id="pre-roll-value" for="pre-roll">1,0 s</output>
      </div>
      <input id="pre-roll" dir="ltr" type="range" min="0" max="3000" step="250" value="1000">
      <div class="range-labels" dir="ltr" aria-hidden="true"><span>0 s</span><span>3 s</span></div>
      <hr>
      <div class="setting-row"><span data-i18n="model">Seamless-Modell</span><strong id="model-state">unbekannt</strong></div>
      <div class="button-row">
        <button id="model-load" class="secondary-button" type="button" data-i18n="modelLoad">Modell laden</button>
        <button id="model-unload" class="secondary-button" type="button" data-i18n="modelUnload">Entladen</button>
      </div>
      <p class="settings-note" data-i18n="modelBusyNote">Entladen ist nicht möglich, solange Aufträge verarbeitet werden.</p>
      <div class="dialog-actions">
        <button id="logout" class="text-button" type="button">Abmelden</button>
        <button class="primary-button compact" value="close" data-i18n="apply">Übernehmen</button>
      </div>
    </form>
  </dialog>

  <aside id="orientation-hint" aria-hidden="true" data-i18n="orientation">Für das beste Gesprächserlebnis das iPad bitte hochkant drehen.</aside>
</body>
</html>
