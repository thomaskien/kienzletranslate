const CACHE_NAME = "kienzle-frontend-v1.8.0-1";
const PUBLIC_ASSETS = [
  "/assets/app.js",
  "/assets/audio-core.js",
  "/assets/audio-worklet.js",
  "/assets/frontend-core.js",
  "/assets/i18n.js",
  "/assets/locales.js",
  "/assets/icon.svg",
  "/assets/styles.css",
];
const ALLOWED = new Set(PUBLIC_ASSETS);

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(PUBLIC_ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith("kienzle-frontend-") && key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin || !ALLOWED.has(url.pathname)) return;
  event.respondWith(fetch(event.request).then((response) => {
    if (response.ok) { const copy = response.clone(); event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy))); }
    return response;
  }).catch(() => caches.match(event.request)));
});
