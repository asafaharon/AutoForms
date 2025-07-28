"""
Client-side caching utilities and templates
"""
from typing import Dict, Any


def generate_cache_headers(max_age: int = 3600, must_revalidate: bool = False) -> Dict[str, str]:
    """Generate HTTP cache headers"""
    headers = {
        "Cache-Control": f"public, max-age={max_age}",
        "Vary": "Accept-Encoding, Authorization"
    }
    
    if must_revalidate:
        headers["Cache-Control"] += ", must-revalidate"
    
    return headers


def generate_etag(content: str) -> str:
    """Generate ETag for content"""
    import hashlib
    return hashlib.md5(content.encode()).hexdigest()


def get_client_cache_script() -> str:
    """Generate JavaScript for client-side caching"""
    return """
    <!-- Client-side caching utilities -->
    <script>
    class AutoFormsCache {
        constructor() {
            this.cache = new Map();
            this.maxSize = 100;
            this.defaultTTL = 5 * 60 * 1000; // 5 minutes
            this.storageKey = 'autoforms_cache';
            this.loadFromStorage();
        }
        
        set(key, value, ttl = this.defaultTTL) {
            const expiry = Date.now() + ttl;
            const entry = { value, expiry };
            
            // Remove oldest entries if cache is full
            if (this.cache.size >= this.maxSize) {
                const oldestKey = this.cache.keys().next().value;
                this.cache.delete(oldestKey);
            }
            
            this.cache.set(key, entry);
            this.saveToStorage();
            console.log(`💾 Cached: ${key}`);
        }
        
        get(key) {
            const entry = this.cache.get(key);
            if (!entry) return null;
            
            if (Date.now() > entry.expiry) {
                this.cache.delete(key);
                this.saveToStorage();
                console.log(`⏰ Cache expired: ${key}`);
                return null;
            }
            
            console.log(`🎯 Cache hit: ${key}`);
            return entry.value;
        }
        
        delete(key) {
            this.cache.delete(key);
            this.saveToStorage();
        }
        
        clear() {
            this.cache.clear();
            localStorage.removeItem(this.storageKey);
            console.log('🧹 Cache cleared');
        }
        
        saveToStorage() {
            try {
                const serialized = JSON.stringify(Array.from(this.cache.entries()));
                localStorage.setItem(this.storageKey, serialized);
            } catch (e) {
                console.warn('Failed to save cache to storage:', e);
            }
        }
        
        loadFromStorage() {
            try {
                const stored = localStorage.getItem(this.storageKey);
                if (stored) {
                    const entries = JSON.parse(stored);
                    this.cache = new Map(entries);
                    // Remove expired entries
                    const now = Date.now();
                    for (const [key, entry] of this.cache) {
                        if (now > entry.expiry) {
                            this.cache.delete(key);
                        }
                    }
                }
            } catch (e) {
                console.warn('Failed to load cache from storage:', e);
                this.cache = new Map();
            }
        }
        
        getStats() {
            const total = this.cache.size;
            const expired = Array.from(this.cache.values())
                .filter(entry => Date.now() > entry.expiry).length;
            
            return {
                total,
                active: total - expired,
                expired,
                maxSize: this.maxSize
            };
        }
    }
    
    // Initialize global cache instance
    window.autoformsCache = new AutoFormsCache();
    
    // Cache-aware fetch function
    async function cachedFetch(url, options = {}) {
        const cacheKey = `fetch_${url}_${JSON.stringify(options)}`;
        
        // Check cache first for GET requests
        if (!options.method || options.method === 'GET') {
            const cached = window.autoformsCache.get(cacheKey);
            if (cached) {
                return new Response(cached.body, {
                    status: cached.status,
                    headers: cached.headers
                });
            }
        }
        
        // Make actual request
        const response = await fetch(url, options);
        
        // Cache successful GET responses
        if (response.ok && (!options.method || options.method === 'GET')) {
            const clonedResponse = response.clone();
            const body = await clonedResponse.text();
            const headers = Object.fromEntries(response.headers.entries());
            
            window.autoformsCache.set(cacheKey, {
                body,
                status: response.status,
                headers
            });
        }
        
        return response;
    }
    
    // Form generation cache
    class FormGenerationCache {
        constructor() {
            this.cache = window.autoformsCache;
        }
        
        async generateForm(prompt, useCache = true) {
            const cacheKey = `form_generation_${prompt}`;
            
            if (useCache) {
                const cached = this.cache.get(cacheKey);
                if (cached) {
                    return cached;
                }
            }
            
            try {
                const response = await fetch('/api/demo-generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({ prompt })
                });
                
                if (response.ok) {
                    const result = await response.text();
                    this.cache.set(cacheKey, result, 10 * 60 * 1000); // 10 minutes
                    return result;
                }
                
                throw new Error('Form generation failed');
            } catch (error) {
                console.error('Form generation error:', error);
                throw error;
            }
        }
        
        clearFormCache() {
            // Clear all form generation cache entries
            for (const key of this.cache.cache.keys()) {
                if (key.startsWith('form_generation_')) {
                    this.cache.delete(key);
                }
            }
        }
    }
    
    // Initialize form generation cache
    window.formCache = new FormGenerationCache();
    
    // Preload common resources
    function preloadCommonResources() {
        const commonUrls = [
            '/api/dashboard',
            '/api/forms'
        ];
        
        commonUrls.forEach(url => {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = url;
            document.head.appendChild(link);
        });
    }
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        preloadCommonResources();
        
        // Add cache stats to debug info
        if (window.location.search.includes('debug=true')) {
            const stats = window.autoformsCache.getStats();
            console.log('Cache stats:', stats);
        }
    });
    
    // Service Worker registration for advanced caching
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('SW registered:', registration))
            .catch(error => console.log('SW registration failed:', error));
    }
    </script>
    """


def get_service_worker_script() -> str:
    """Generate Service Worker for advanced caching"""
    return """
    // Service Worker for AutoForms caching
    const CACHE_NAME = 'autoforms-v1';
    const urlsToCache = [
        '/',
        '/static/css/main.css',
        '/static/js/main.js',
        '/login',
        '/register',
        '/demo-generator',
        'https://cdn.tailwindcss.com',
        'https://unpkg.com/htmx.org@1.9.2',
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap'
    ];
    
    self.addEventListener('install', event => {
        event.waitUntil(
            caches.open(CACHE_NAME)
                .then(cache => cache.addAll(urlsToCache))
        );
    });
    
    self.addEventListener('fetch', event => {
        event.respondWith(
            caches.match(event.request)
                .then(response => {
                    // Return cached version or fetch from network
                    return response || fetch(event.request);
                })
        );
    });
    
    self.addEventListener('activate', event => {
        event.waitUntil(
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME) {
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
        );
    });
    """