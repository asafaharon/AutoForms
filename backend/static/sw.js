// Service Worker for AutoForms PWA
const CACHE_NAME = 'autoforms-v1.0.0';
const STATIC_CACHE_NAME = 'autoforms-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'autoforms-dynamic-v1.0.0';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/login',
  '/register',
  '/demo-generator',
  '/home',
  '/static/manifest.json',
  '/static/js/websocket-client.js',
  '/static/css/app.css',
  'https://cdn.tailwindcss.com',
  'https://unpkg.com/htmx.org@1.9.2',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap',
  'https://fonts.googleapis.com/css2?family=Alef&display=swap'
];

// API endpoints to cache
const CACHEABLE_APIS = [
  '/api/forms',
  '/api/dashboard',
  '/api/performance-stats'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('SW: Installing service worker...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(cache => {
        console.log('SW: Caching static assets...');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('SW: Static assets cached');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('SW: Error caching static assets:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('SW: Activating service worker...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName !== CACHE_NAME) {
              console.log('SW: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('SW: Service worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension requests
  if (url.protocol === 'chrome-extension:') {
    return;
  }
  
  // Handle different types of requests
  if (isStaticAsset(request)) {
    event.respondWith(cacheFirst(request));
  } else if (isApiRequest(request)) {
    event.respondWith(networkFirst(request));
  } else if (isNavigationRequest(request)) {
    event.respondWith(staleWhileRevalidate(request));
  } else {
    event.respondWith(networkFirst(request));
  }
});

// Check if request is for static assets
function isStaticAsset(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/static/') ||
         url.pathname.endsWith('.js') ||
         url.pathname.endsWith('.css') ||
         url.pathname.endsWith('.png') ||
         url.pathname.endsWith('.jpg') ||
         url.pathname.endsWith('.ico') ||
         url.hostname === 'cdn.tailwindcss.com' ||
         url.hostname === 'unpkg.com' ||
         url.hostname === 'fonts.googleapis.com' ||
         url.hostname === 'fonts.gstatic.com';
}

// Check if request is for API
function isApiRequest(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/api/') ||
         CACHEABLE_APIS.some(endpoint => url.pathname.startsWith(endpoint));
}

// Check if request is navigation
function isNavigationRequest(request) {
  return request.mode === 'navigate' ||
         (request.method === 'GET' && request.headers.get('accept').includes('text/html'));
}

// Cache first strategy - for static assets
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('SW: Cache first error:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Network first strategy - for API requests
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('SW: Network failed, trying cache:', error);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (isNavigationRequest(request)) {
      return caches.match('/offline.html') || 
             new Response('Offline', { status: 503 });
    }
    
    return new Response('Network Error', { status: 503 });
  }
}

// Stale while revalidate strategy - for pages
async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  const networkRequest = fetch(request).then(response => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(error => {
    console.log('SW: Network error in stale-while-revalidate:', error);
    return cachedResponse || new Response('Offline', { status: 503 });
  });
  
  return cachedResponse || networkRequest;
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  console.log('SW: Background sync triggered:', event.tag);
  
  if (event.tag === 'form-submission') {
    event.waitUntil(syncFormSubmissions());
  } else if (event.tag === 'form-generation') {
    event.waitUntil(syncFormGeneration());
  }
});

// Sync form submissions when back online
async function syncFormSubmissions() {
  try {
    const submissions = await getStoredSubmissions();
    for (const submission of submissions) {
      try {
        await fetch(submission.url, {
          method: 'POST',
          body: submission.data
        });
        await removeStoredSubmission(submission.id);
        console.log('SW: Synced form submission:', submission.id);
      } catch (error) {
        console.error('SW: Failed to sync submission:', error);
      }
    }
  } catch (error) {
    console.error('SW: Error syncing form submissions:', error);
  }
}

// Sync form generation when back online
async function syncFormGeneration() {
  try {
    const generations = await getStoredGenerations();
    for (const generation of generations) {
      try {
        const response = await fetch('/api/generate', {
          method: 'POST',
          body: generation.data
        });
        const result = await response.text();
        
        // Notify client about completed generation
        self.registration.showNotification('Form Generated', {
          body: 'Your form has been generated successfully!',
          icon: '/static/icons/icon-72x72.png',
          tag: 'form-generated'
        });
        
        await removeStoredGeneration(generation.id);
        console.log('SW: Synced form generation:', generation.id);
      } catch (error) {
        console.error('SW: Failed to sync generation:', error);
      }
    }
  } catch (error) {
    console.error('SW: Error syncing form generation:', error);
  }
}

// Push notification handling
self.addEventListener('push', event => {
  console.log('SW: Push notification received:', event);
  
  let notificationData = {};
  if (event.data) {
    notificationData = event.data.json();
  }
  
  const options = {
    body: notificationData.body || 'New notification from AutoForms',
    icon: '/static/icons/icon-72x72.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: notificationData.data || {},
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/static/icons/action-view.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/static/icons/action-dismiss.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(
      notificationData.title || 'AutoForms',
      options
    )
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  console.log('SW: Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'view') {
    const url = event.notification.data.url || '/';
    event.waitUntil(
      clients.openWindow(url)
    );
  } else if (event.action === 'dismiss') {
    // Just close the notification
    return;
  } else {
    // Default action - open app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Message handling from client
self.addEventListener('message', event => {
  console.log('SW: Message received:', event.data);
  
  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data.type === 'CACHE_CLEAR') {
    clearCaches();
  } else if (event.data.type === 'CACHE_STATS') {
    getCacheStats().then(stats => {
      event.ports[0].postMessage(stats);
    });
  }
});

// Clear all caches
async function clearCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(
    cacheNames.map(cacheName => caches.delete(cacheName))
  );
  console.log('SW: All caches cleared');
}

// Get cache statistics
async function getCacheStats() {
  const cacheNames = await caches.keys();
  const stats = {};
  
  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    stats[cacheName] = {
      count: keys.length,
      urls: keys.map(key => key.url)
    };
  }
  
  return stats;
}

// IndexedDB helpers for offline storage
async function getStoredSubmissions() {
  // Implementation depends on your IndexedDB setup
  return [];
}

async function removeStoredSubmission(id) {
  // Implementation depends on your IndexedDB setup
}

async function getStoredGenerations() {
  // Implementation depends on your IndexedDB setup
  return [];
}

async function removeStoredGeneration(id) {
  // Implementation depends on your IndexedDB setup
}

console.log('SW: Service worker script loaded');