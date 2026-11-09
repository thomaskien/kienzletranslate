# kienzletranslate — implementation contract

The conversation's later decisions override the original handover: PHP webapp
and Python model service on the same Linux server (10.0.83.140), two normal
language selectors, no automatic language identification in v1. Use only
facebook/seamless-m4t-v2-large. No cloud calls after authorized model download.

## Browser ↔ PHP

Buildless ES modules and PHP 8.2+. All browser API calls use `/api.php?route=…`.
JSON errors: `{error: "safe message", code: "stable_code"}`.
Fetch uses same-origin credentials. Mutating calls require `X-CSRF-Token`
returned by bootstrap (except login). Binary recordings are mono PCM16 WAV,
native sample rate, in a raw `audio/wav` request body (no multipart/temp files).

- GET `bootstrap`: `{authenticated, password_required, csrf, session_id, languages, model, version}`.
  With password protection off (default), bootstrap creates an isolated signed
  browser session automatically. Anonymous cookies cannot authenticate after
  password protection is enabled. Existing protected installs retain their setting.
  languages: `[{code, name, speech_output}]`; model: `{state, error?}`.
- POST `login`: JSON `{password}` → `{ok:true}`; call bootstrap again.
- POST `logout`: clears authentication and session RAM.
- GET `health`: `{state:"unloaded|loading|ready|unloading|error", busy, queued}`.
- POST `model/load` or `model/unload`: explicit lifecycle; unload returns 409
  while processing or queued; load also happens lazily on first request.
- POST `utterances&utterance_id=<UUID>&speaker_side=top|bottom&source_lang=…&target_lang=…&tts=0|1&generation=…`:
  raw WAV → HTTP 202 `{id, status:"queued"}`.
- GET `utterances/<UUID>` → `{id,status:"queued|processing|complete|error",
  original_text?,translated_text?,source_lang?,target_lang?,audio_available?,
  text_only_reason?,error?,metrics?}`.
- GET `audio/<UUID>`: WAV from RAM; access restricted to authenticated session.
- DELETE `session`: drops session data and pending work.

Client generates a new UUID / generation on EVERY new touch and discards stale
responses. The sortable generation timestamp also prevents an older upload arriving
after a newer one from replacing its server result. A previous job may finish but
may not replace a newer display.
Do not block a new recording while polling. Bound all uploads (16 MiB), recording
duration (60 s including pre-roll), queues, session count, and result retention.
Audio/transcripts only in RAM; no service-worker caching of APIs, no PHP disk
sessions, no payload logs. API and auth responses use Cache-Control: no-store.

## UI

Reference PNG is style only. Top TEXT rotates 180 degrees; all controls remain
upright. Two selects (top default Ukrainian, bottom German), center speaker toggle
and translation arrows, small pre-roll/settings controls on doctor side. PTT green
only while holding; ~45% active / 55% opposite, neutral 50/50. Black immediately
on release. Visible busy/error state without permanent footer. Existing results
stay until a valid complete newer pair replaces them. Accessible contrast and
large touch controls; no external fonts/CDNs/framework builds.

Continuous local AudioWorklet PCM ring buffer (max 3 s), pre-roll 0–3000 ms in
250 ms steps, default 1000. No audio upload until release. Cancel/hidden stops
and discards recording, clears old buffer. Multi-touch never starts another block.
New press stops playback and excludes playback echo from pre-roll. Stop/discard
overlong capture with explanation. Only preferences in localStorage.

## Server and installer

Python FastAPI/Uvicorn on loopback TCP port 8765 by default, bearer authenticated.
Single Uvicorn worker, one resident full SeamlessM4Tv2Model, a serial inference
queue. ASR + S2TT, or ASR + S2ST with intermediate text from same model. FP16
CUDA primary; ffmpeg or scipy resampling is allowed. No extra trained model.

Native Debian/Ubuntu: nginx + php-fpm + systemd + isolated Python venv. First
installer question DE/EN, then full model-license notice requiring exact word
AKZEPTIEREN / ACCEPT; abort before changes otherwise. Ask IP, optional DNS name,
HTTP/HTTPS/model ports, optional password protection (default off), path; updates
preserve config and local CA.
Private CA generates leaf with exact IP/DNS SAN. HTTP setup page repeats license
word acknowledgement before public CA download and explains iPad profile install
plus full trust. Never serve private keys. Real application uses HTTPS.

Other GPU services may be stopped for deployment/tests, keeping autostart settings
unchanged; leave stopped afterwards (explicit user decision). No automatic GPU
coexistence management in v1. No destructive edits to unrelated server services.

## Compact acceptance

Test deterministic ringbuffer/cancellation/race cases, API auth/isolation and job
lifecycle, installer inputs/confirmation/update preservation. One real GPU
load→translate→unload→VRAM check→reload→translate cycle with a few nonpersonal
samples, including audio on/off and text-only fallback. One desktop UI inspection
and one short real iPad acceptance session. Repeat only affected checks after fixes.
