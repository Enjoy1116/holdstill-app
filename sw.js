// Framey offline support: use the network when it's there, fall back to the saved copy when it isn't.
const CACHE = "framey-v21";
const CORE = ["./", "index.html", "app.js?v=20", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png", "tutorial.jpg",
  "https://cdnjs.cloudflare.com/ajax/libs/react/18.3.1/umd/react.production.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.3.1/umd/react-dom.production.min.js"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => Promise.all(CORE.map((u) => c.add(u).catch(() => {})))).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => { e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", (e) => {
  const r = e.request;
  if (r.method !== "GET" || !/^https?:/.test(r.url)) return;
  if (/\.mp4(\?|$)/.test(r.url)) return; // the tutorial video streams straight from the web
  e.respondWith(fetch(r).then((res) => { if (res && (res.ok || res.type === "opaque")) { const cp = res.clone(); caches.open(CACHE).then((c) => c.put(r, cp)); } return res; })
    .catch(() => caches.match(r, { ignoreSearch: r.mode === "navigate" }).then((m) => m || caches.match("index.html"))));
});
