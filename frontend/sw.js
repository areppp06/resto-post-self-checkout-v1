// Takeway Self-Checkout Kiosk - Progressive Web App Service Worker
const CACHE_NAME = 'takeway-kiosk-v1';

const STATIC_PRECACHE = [
  '/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/apple-touch-icon.png',
  '/static/icons/favicon-32.png'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_PRECACHE).catch((err) => {
        console.warn('[SW] Pre-cache warning:', err);
      });
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((k) => {
          if (k !== CACHE_NAME) {
            console.log('[SW] Clearing old cache:', k);
            return caches.delete(k);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // 1. NEVER intercept non-GET requests (POST /api/pay, etc.)
  if (req.method !== 'GET') {
    return;
  }

  // 2. NEVER intercept or cache API calls, admin endpoints, or dynamic data
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin')) {
    return;
  }

  // 3. NEVER intercept external payment gateways, webhooks, or third-party auth
  if (url.origin !== self.location.origin) {
    // Let browser handle external links (CHIP, Curlec, Razorpay, etc.) directly
    return;
  }

  // 4. NEVER cache payment flow, redirects, or session-specific URLs
  if (
    url.pathname.includes('/pay') ||
    url.pathname.includes('/payment/') ||
    url.searchParams.has('session') ||
    url.searchParams.has('intent_id') ||
    url.searchParams.has('payment') ||
    url.searchParams.has('edit') ||
    url.searchParams.has('retake')
  ) {
    // Network only for payment callbacks & success receipts to ensure live verification
    return;
  }

  // 5. Static Assets (icons, manifest): Cache-first with network fallback
  if (url.pathname.startsWith('/static/icons/') || url.pathname === '/manifest.json') {
    event.respondWith(
      caches.match(req).then((cached) => {
        return cached || fetch(req).then((res) => {
          if (res && res.status === 200) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, clone));
          }
          return res;
        });
      })
    );
    return;
  }

  // 6. Main Navigation & HTML Pages: Network-First (ensures fresh menu & prices, fallback to cache if offline)
  if (req.mode === 'navigate' || req.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(req)
        .then((networkRes) => {
          if (networkRes && networkRes.status === 200) {
            const clone = networkRes.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, clone));
          }
          return networkRes;
        })
        .catch(() => {
          return caches.match(req).then((cached) => {
            return cached || caches.match('/?source=pwa');
          });
        })
    );
    return;
  }
});
