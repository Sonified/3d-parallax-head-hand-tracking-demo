/*! coi-serviceworker v0.1.7 - Guido Zuidhof, licensed under MIT */
// This service worker adds Cross-Origin-Opener-Policy and Cross-Origin-Embedder-Policy
// headers to enable crossOriginIsolated state, which is required for WebGPU in workers.
if (typeof window === 'undefined') {
  self.addEventListener("install", () => self.skipWaiting());
  self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

  self.addEventListener("fetch", (e) => {
    if (e.request.cache === "only-if-cached" && e.request.mode !== "same-origin") return;

    e.respondWith(
      fetch(e.request).then((res) => {
        if (res.status === 0) return res;

        const headers = new Headers(res.headers);
        headers.set("Cross-Origin-Embedder-Policy", "credentialless");
        headers.set("Cross-Origin-Opener-Policy", "same-origin");

        return new Response(res.body, {
          status: res.status,
          statusText: res.statusText,
          headers,
        });
      }).catch((err) => console.error(err))
    );
  });
} else {
  // Main thread: register the service worker
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register(new URL("coi-serviceworker.js", import.meta.url || location.href)).then(
      (registration) => {
        if (registration.active && !navigator.serviceWorker.controller) {
          // Service worker is active but not controlling this page yet - reload
          window.location.reload();
        }
      },
      (err) => console.error("COI service worker registration failed:", err)
    );
  }
}
