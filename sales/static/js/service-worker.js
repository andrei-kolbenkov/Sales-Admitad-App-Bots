const CACHE_NAME = 'my-pwa-cache-v1';
const OFFLINE_URL = '/offline/';

// Установка Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                // Кэшируем офлайн-страницу
                return cache.add(OFFLINE_URL);
            })
    );
});

// Активация Service Worker
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('Удаляем старый кэш:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
});

// Перехват сетевых запросов
self.addEventListener('fetch', (event) => {
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => {
                return caches.match(OFFLINE_URL)
                    .then((response) => {
                        if (response) {
                            return response;
                        }
                        // Если офлайн-страница не найдена, вернуть пустой ответ
                        return new Response('Офлайн-режим', {
                            headers: { 'Content-Type': 'text/plain' }
                        });
                    });
            })
        );
    } else {
        event.respondWith(
            caches.match(event.request).then((response) => {
                return response || fetch(event.request);
            })
        );
    }
});