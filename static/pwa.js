/**
 * PWA service worker registration.
 *
 * Registers /sw.js if the browser supports Service Workers.
 * No-op on unsupported browsers.
 */
(function () {
  if (!("serviceWorker" in navigator)) {
    return;
  }
  window.addEventListener("load", function () {
    navigator.serviceWorker
      .register("/sw.js")
      .then(function (reg) {
        // Registration succeeded
        console.log("[pwa] ServiceWorker registered:", reg.scope);
      })
      .catch(function (err) {
        console.warn("[pwa] ServiceWorker registration failed:", err);
      });
  });
})();
