/* Service worker: precache the whole education app so it works offline once installed.
   Cache-first with ignoreSearch so ?v=N cache-bust query strings still hit the cache. */
const CACHE = 'mentor-guides-v4';
const ASSETS = [
  'index.html', 'styles.css', 'app.js', 'data.js', 'uses.js',
  'mentor-guides.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png',
  'mentors/guide.css', 'mentors/guide.js',
  'mentors/ttrades.html', 'mentors/daye.html', 'mentors/dayement.html', 'mentors/gxt.html', 'mentors/ict.html', 'mentors/dexter.html', 'mentors/xyj.html',
  'mentors/data/ttrades.js', 'mentors/data/daye.js', 'mentors/data/dayement.js', 'mentors/data/gxt.js', 'mentors/data/ict.js', 'mentors/data/dexter.js', 'mentors/data/xyj.js'
];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(r =>
      r || fetch(e.request).then(resp => {
        const cp = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, cp));
        return resp;
      }).catch(() => caches.match('index.html'))
    )
  );
});
