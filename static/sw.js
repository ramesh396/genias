const CACHE_NAME = "salapa-v2";
const OFFLINE_URL = "/offline/index.html";

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      cache.addAll(["/", OFFLINE_URL])
    )
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    fetch(event.request).catch(async () => {
      const cached = await caches.match(event.request);
      if (cached) return cached;

      return caches.match(OFFLINE_URL);
    })
  );
});
