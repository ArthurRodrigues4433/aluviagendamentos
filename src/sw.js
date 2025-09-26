// Service Worker Avançado para Aluvi PWA
const CACHE_NAME = 'aluvi-v2.0.0';
const STATIC_CACHE = 'aluvi-static-v2.0.0';
const DYNAMIC_CACHE = 'aluvi-dynamic-v2.0.0';
const API_CACHE = 'aluvi-api-v2.0.0';
const OFFLINE_DATA = 'aluvi-offline-data-v2.0.0';

// Arquivos para cache estático
const STATIC_ASSETS = [
  '/',
  '/frontend/config.js',
  '/frontend/app.js',
  '/frontend/assets/styles.css',
  '/manifest.json',
  '/frontend/pages/index.html',
  '/frontend/pages/login.html',
  '/frontend/pages/dashboard-cliente.html',
  '/frontend/pages/dashboard-dono.html',
  '/frontend/pages/appointments.html',
  '/frontend/pages/new-appointment.html',
  '/frontend/pages/profile.html',
  '/frontend/assets/icon-192x192.png',
  '/frontend/assets/icon-512x512.png',
  // Componentes
  '/frontend/components/appointment-card.js',
  '/frontend/components/calendar.js',
  '/frontend/components/form-validation.js',
  '/frontend/components/date-picker.js',
  // Serviços
  '/frontend/services/loyalty.js',
  '/frontend/services/notifications.js'
];

// URLs de API para cache inteligente
const API_CACHE_PATTERNS = [
  /\/api\/services\/public/,
  /\/api\/professionals\/public/,
  /\/api\/appointments\/available-slots/,
  /\/api\/appointments\/upcoming/
];

// Dados offline críticos
const OFFLINE_DATA_URLS = [
  '/api/services/public',
  '/api/professionals/public'
];

// IndexedDB para dados offline
class OfflineStorage {
  constructor() {
    this.dbName = 'AluviOfflineDB';
    this.version = 1;
    this.db = null;
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Store para agendamentos offline
        if (!db.objectStoreNames.contains('offlineAppointments')) {
          const appointmentsStore = db.createObjectStore('offlineAppointments', { keyPath: 'id' });
          appointmentsStore.createIndex('syncStatus', 'syncStatus', { unique: false });
          appointmentsStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Store para dados de cache
        if (!db.objectStoreNames.contains('cachedData')) {
          const cacheStore = db.createObjectStore('cachedData', { keyPath: 'url' });
          cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Store para ações pendentes
        if (!db.objectStoreNames.contains('pendingActions')) {
          const actionsStore = db.createObjectStore('pendingActions', { keyPath: 'id' });
          actionsStore.createIndex('type', 'type', { unique: false });
          actionsStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  async storeAppointment(appointment) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['offlineAppointments'], 'readwrite');
      const store = transaction.objectStore('offlineAppointments');

      const offlineAppointment = {
        ...appointment,
        id: `offline_${Date.now()}`,
        syncStatus: 'pending',
        timestamp: Date.now(),
        offline: true
      };

      const request = store.add(offlineAppointment);
      request.onsuccess = () => resolve(offlineAppointment);
      request.onerror = () => reject(request.error);
    });
  }

  async getPendingAppointments() {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['offlineAppointments'], 'readonly');
      const store = transaction.objectStore('offlineAppointments');
      const index = store.index('syncStatus');
      const request = index.getAll('pending');

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async markAppointmentSynced(appointmentId) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['offlineAppointments'], 'readwrite');
      const store = transaction.objectStore('offlineAppointments');
      const request = store.get(appointmentId);

      request.onsuccess = () => {
        const appointment = request.result;
        if (appointment) {
          appointment.syncStatus = 'synced';
          const updateRequest = store.put(appointment);
          updateRequest.onsuccess = () => resolve(appointment);
          updateRequest.onerror = () => reject(updateRequest.error);
        } else {
          resolve(null);
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  async storeCachedData(url, data) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['cachedData'], 'readwrite');
      const store = transaction.objectStore('cachedData');

      const cacheEntry = {
        url,
        data,
        timestamp: Date.now()
      };

      const request = store.put(cacheEntry);
      request.onsuccess = () => resolve(cacheEntry);
      request.onerror = () => reject(request.error);
    });
  }

  async getCachedData(url) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['cachedData'], 'readonly');
      const store = transaction.objectStore('cachedData');
      const request = store.get(url);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async storePendingAction(action) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['pendingActions'], 'readwrite');
      const store = transaction.objectStore('pendingActions');

      const pendingAction = {
        ...action,
        id: `action_${Date.now()}`,
        timestamp: Date.now(),
        status: 'pending'
      };

      const request = store.add(pendingAction);
      request.onsuccess = () => resolve(pendingAction);
      request.onerror = () => reject(request.error);
    });
  }

  async getPendingActions() {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['pendingActions'], 'readonly');
      const store = transaction.objectStore('pendingActions');
      const index = store.index('status');
      const request = index.getAll('pending');

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async clearOldData(maxAge = 24 * 60 * 60 * 1000) { // 24 horas
    if (!this.db) await this.init();

    const cutoffTime = Date.now() - maxAge;

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['cachedData'], 'readwrite');
      const store = transaction.objectStore('cachedData');
      const index = store.index('timestamp');
      const range = IDBKeyRange.upperBound(cutoffTime);
      const request = index.openCursor(range);

      let deletedCount = 0;

      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          cursor.delete();
          deletedCount++;
          cursor.continue();
        } else {
          resolve(deletedCount);
        }
      };

      request.onerror = () => reject(request.error);
    });
  }
}

// Instância global do storage offline
const offlineStorage = new OfflineStorage();

// Instalar Service Worker
self.addEventListener('install', (event) => {
  console.log('[SW] Instalando Service Worker...');

  event.waitUntil(
    Promise.all([
      // Cache de assets estáticos
      caches.open(STATIC_CACHE)
        .then((cache) => {
          console.log('[SW] Fazendo cache de assets estáticos...');
          return cache.addAll(STATIC_ASSETS);
        }),

      // Inicializar IndexedDB
      offlineStorage.init()
        .then(() => {
          console.log('[SW] IndexedDB inicializado');
        }),

      // Cache de dados offline críticos
      cacheOfflineData()
    ])
    .then(() => {
      console.log('[SW] Service Worker instalado com sucesso!');
      return self.skipWaiting();
    })
    .catch((error) => {
      console.error('[SW] Erro durante instalação:', error);
    })
  );
});

// Função para cache de dados offline críticos
async function cacheOfflineData() {
  console.log('[SW] Fazendo cache de dados offline críticos...');

  for (const url of OFFLINE_DATA_URLS) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        await offlineStorage.storeCachedData(url, await response.json());
        console.log(`[SW] Dados offline cached: ${url}`);
      }
    } catch (error) {
      console.warn(`[SW] Erro ao fazer cache de ${url}:`, error);
    }
  }
}

// Ativar Service Worker
self.addEventListener('activate', (event) => {
  console.log('[SW] Ativando Service Worker...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            console.log('[SW] Removendo cache antigo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Service Worker ativado!');
      return self.clients.claim();
    })
  );
});

// Interceptar requisições
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Estratégia Cache First para assets estáticos
  if (STATIC_ASSETS.some(asset => request.url.includes(asset))) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Estratégia Network First para APIs com fallback offline
  if (url.pathname.startsWith('/api/') || API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    event.respondWith(networkFirstWithOfflineFallback(request));
    return;
  }

  // Estratégia Stale While Revalidate para páginas HTML
  if (request.destination === 'document') {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Estratégia Cache First para outros recursos
  event.respondWith(cacheFirst(request));
});

// Estratégia Network First com fallback offline inteligente
async function networkFirstWithOfflineFallback(request) {
  const url = new URL(request.url);

  try {
    // Tentar rede primeiro
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache da resposta bem-sucedida
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());

      // Também armazenar no IndexedDB para dados críticos
      if (OFFLINE_DATA_URLS.some(offlineUrl => url.pathname.includes(offlineUrl))) {
        try {
          const data = await networkResponse.clone().json();
          await offlineStorage.storeCachedData(url.pathname, data);
        } catch (error) {
          console.warn('[SW] Erro ao armazenar dados offline:', error);
        }
      }

      return networkResponse;
    }

    throw new Error(`Resposta não-ok: ${networkResponse.status}`);

  } catch (error) {
    console.log('[SW] Rede indisponível, tentando offline fallback...');

    // Tentar cache primeiro
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Retornando resposta do cache');
      return cachedResponse;
    }

    // Tentar IndexedDB para dados críticos
    try {
      const offlineData = await offlineStorage.getCachedData(url.pathname);
      if (offlineData) {
        console.log('[SW] Retornando dados offline do IndexedDB');
        return new Response(JSON.stringify({
          ...offlineData.data,
          offline: true,
          cached: true,
          timestamp: offlineData.timestamp
        }), {
          headers: { 'Content-Type': 'application/json' }
        });
      }
    } catch (dbError) {
      console.warn('[SW] Erro ao buscar dados offline:', dbError);
    }

    // Fallback específico por tipo de API
    if (url.pathname.includes('/services/public')) {
      return new Response(JSON.stringify({
        success: false,
        message: 'Você está offline. Alguns serviços podem não estar disponíveis.',
        offline: true,
        data: []
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (url.pathname.includes('/appointments/available-slots')) {
      return new Response(JSON.stringify({
        success: false,
        message: 'Verificação de horários indisponível offline.',
        offline: true,
        available: false
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Para outras APIs, informar que está offline
    return new Response(JSON.stringify({
      success: false,
      message: 'Você está offline. Esta funcionalidade requer conexão com a internet.',
      offline: true
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Estratégia Cache First
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.error('[SW] Erro na estratégia Cache First:', error);
    // Fallback para offline
    if (request.destination === 'document') {
      const cache = await caches.open(STATIC_CACHE);
      return cache.match('/frontend/pages/index.html');
    }
    throw error;
  }
}

// Estratégia Network First
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Rede indisponível, tentando cache...');

    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Fallback para dados offline
    if (request.url.includes('/api/services/public')) {
      return new Response(JSON.stringify({
        success: false,
        message: 'Você está offline. Dados carregados do cache.',
        offline: true,
        data: [] // Dados vazios como fallback
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    throw error;
  }
}

// Estratégia Stale While Revalidate
async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cachedResponse = await cache.match(request);

  const fetchPromise = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  });

  return cachedResponse || fetchPromise;
}

// Sincronização em background avançada
self.addEventListener('sync', (event) => {
  console.log('[SW] Evento de sincronização:', event.tag);

  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }

  if (event.tag === 'sync-appointments') {
    event.waitUntil(syncPendingAppointments());
  }

  if (event.tag === 'sync-actions') {
    event.waitUntil(syncPendingActions());
  }
});

// Sincronização de agendamentos pendentes
async function syncPendingAppointments() {
  console.log('[SW] Sincronizando agendamentos pendentes...');

  try {
    const pendingAppointments = await offlineStorage.getPendingAppointments();

    if (pendingAppointments.length === 0) {
      console.log('[SW] Nenhum agendamento pendente para sincronizar');
      return;
    }

    console.log(`[SW] Sincronizando ${pendingAppointments.length} agendamentos...`);

    for (const appointment of pendingAppointments) {
      try {
        // Tentar enviar para o servidor
        const response = await fetch('/api/appointments', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${appointment.token}`
          },
          body: JSON.stringify(appointment)
        });

        if (response.ok) {
          // Marcar como sincronizado
          await offlineStorage.markAppointmentSynced(appointment.id);
          console.log(`[SW] Agendamento ${appointment.id} sincronizado com sucesso`);
        } else {
          console.warn(`[SW] Falha ao sincronizar agendamento ${appointment.id}:`, response.status);
        }
      } catch (error) {
        console.error(`[SW] Erro ao sincronizar agendamento ${appointment.id}:`, error);
      }
    }

    // Notificar o cliente sobre a sincronização
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'sync-completed',
        data: { appointmentsSynced: pendingAppointments.length }
      });
    });

  } catch (error) {
    console.error('[SW] Erro na sincronização de agendamentos:', error);
  }
}

// Sincronização de ações pendentes
async function syncPendingActions() {
  console.log('[SW] Sincronizando ações pendentes...');

  try {
    const pendingActions = await offlineStorage.getPendingActions();

    if (pendingActions.length === 0) {
      console.log('[SW] Nenhuma ação pendente para sincronizar');
      return;
    }

    console.log(`[SW] Sincronizando ${pendingActions.length} ações...`);

    for (const action of pendingActions) {
      try {
        const response = await fetch(action.url, {
          method: action.method || 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...action.headers
          },
          body: JSON.stringify(action.data)
        });

        if (response.ok) {
          // Remover ação da fila
          await removePendingAction(action.id);
          console.log(`[SW] Ação ${action.id} executada com sucesso`);
        } else {
          console.warn(`[SW] Falha ao executar ação ${action.id}:`, response.status);
        }
      } catch (error) {
        console.error(`[SW] Erro ao executar ação ${action.id}:`, error);
      }
    }

  } catch (error) {
    console.error('[SW] Erro na sincronização de ações:', error);
  }
}

// Função auxiliar para remover ação pendente
async function removePendingAction(actionId) {
  // Implementar remoção do IndexedDB
  console.log(`[SW] Removendo ação pendente ${actionId}`);
}

// Sincronização geral em background
async function doBackgroundSync() {
  console.log('[SW] Executando sincronização geral em background...');

  try {
    // Sincronizar agendamentos
    await syncPendingAppointments();

    // Sincronizar ações
    await syncPendingActions();

    // Limpar dados antigos
    const deletedCount = await offlineStorage.clearOldData();
    if (deletedCount > 0) {
      console.log(`[SW] ${deletedCount} entradas de cache antigas removidas`);
    }

    // Atualizar cache de dados críticos
    await cacheOfflineData();

    console.log('[SW] Sincronização em background concluída!');
  } catch (error) {
    console.error('[SW] Erro na sincronização em background:', error);
  }
}

// Push notifications com funcionalidades avançadas
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification recebida:', event);

  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || data.message,
      icon: data.icon || '/frontend/assets/icon-192x192.png',
      badge: '/frontend/assets/icon-96x96.png',
      vibrate: data.vibrate || [200, 100, 200],
      data: data.data || {},
      tag: data.tag || 'aluvi-notification',
      requireInteraction: data.requireInteraction || false,
      silent: data.silent || false,
      actions: data.actions || [
        {
          action: 'view',
          title: 'Ver',
          icon: '/frontend/assets/icon-96x96.png'
        },
        {
          action: 'dismiss',
          title: 'Fechar'
        }
      ]
    };

    // Adicionar timestamp se for temporal
    if (data.timestamp) {
      options.timestamp = data.timestamp;
    }

    // Adicionar imagem se fornecida
    if (data.image) {
      options.image = data.image;
    }

    event.waitUntil(
      self.registration.showNotification(data.title || 'Aluvi', options)
    );
  }
});

// Click em notificações
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notificação clicada:', event);

  event.notification.close();

  if (event.action === 'view') {
    const urlToOpen = event.notification.data.url || '/';

    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((windowClients) => {
          // Verificar se já existe uma janela aberta
          for (let client of windowClients) {
            if (client.url === urlToOpen && 'focus' in client) {
              return client.focus();
            }
          }

          // Abrir nova janela
          if (clients.openWindow) {
            return clients.openWindow(urlToOpen);
          }
        })
    );
  }
});

// Sincronização em background (placeholder)
async function doBackgroundSync() {
  console.log('[SW] Executando sincronização em background...');

  try {
    // Aqui seria implementada a lógica de sincronização
    // Por exemplo: enviar dados pendentes, atualizar cache, etc.

    console.log('[SW] Sincronização em background concluída!');
  } catch (error) {
    console.error('[SW] Erro na sincronização em background:', error);
  }
}

// Comunicação avançada com o cliente
self.addEventListener('message', (event) => {
  const { type, data } = event.data || {};

  switch (type) {
    case 'STORE_OFFLINE_APPOINTMENT':
      handleStoreOfflineAppointment(data, event);
      break;

    case 'GET_OFFLINE_DATA':
      handleGetOfflineData(data, event);
      break;

    case 'SYNC_NOW':
      handleSyncNow(event);
      break;

    case 'CLEAN_CACHE':
      cleanOldCache();
      break;

    case 'GET_CACHE_STATS':
      handleGetCacheStats(event);
      break;

    case 'PERFORMANCE_DATA':
      handlePerformanceData(data);
      break;

    case 'UPDATE_USER_TOKEN':
      handleUpdateUserToken(data);
      break;

    default:
      console.log('[SW] Mensagem desconhecida recebida:', event.data);
  }
});

// Armazenar agendamento offline
async function handleStoreOfflineAppointment(data, event) {
  try {
    const appointment = await offlineStorage.storeAppointment(data);
    event.ports[0].postMessage({
      success: true,
      appointment: appointment
    });
  } catch (error) {
    event.ports[0].postMessage({
      success: false,
      error: error.message
    });
  }
}

// Obter dados offline
async function handleGetOfflineData(data, event) {
  try {
    const result = {};

    if (data.includeAppointments) {
      result.appointments = await offlineStorage.getPendingAppointments();
    }

    if (data.includeCache) {
      // Obter estatísticas de cache
      const cacheNames = await caches.keys();
      result.cacheStats = {};

      for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        result.cacheStats[cacheName] = keys.length;
      }
    }

    event.ports[0].postMessage({
      success: true,
      data: result
    });
  } catch (error) {
    event.ports[0].postMessage({
      success: false,
      error: error.message
    });
  }
}

// Forçar sincronização
async function handleSyncNow(event) {
  try {
    await doBackgroundSync();
    event.ports[0].postMessage({
      success: true,
      message: 'Sincronização concluída'
    });
  } catch (error) {
    event.ports[0].postMessage({
      success: false,
      error: error.message
    });
  }
}

// Obter estatísticas de cache
async function handleGetCacheStats(event) {
  try {
    const stats = {
      caches: {},
      indexedDB: {}
    };

    // Estatísticas de Cache API
    const cacheNames = await caches.keys();
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const keys = await cache.keys();
      stats.caches[cacheName] = {
        entries: keys.length,
        size: 'unknown' // Cache API não fornece tamanho
      };
    }

    // Estatísticas de IndexedDB
    if (offlineStorage.db) {
      // Simplificado - em produção poderia calcular tamanhos reais
      stats.indexedDB = {
        appointments: await offlineStorage.getPendingAppointments().then(a => a.length),
        cachedData: 'unknown',
        pendingActions: await offlineStorage.getPendingActions().then(a => a.length)
      };
    }

    event.ports[0].postMessage({
      success: true,
      stats: stats
    });
  } catch (error) {
    event.ports[0].postMessage({
      success: false,
      error: error.message
    });
  }
}

// Dados de performance
function handlePerformanceData(data) {
  console.log('[SW] Dados de performance:', data);
  // Em produção, enviaria para analytics
}

// Atualizar token do usuário
function handleUpdateUserToken(data) {
  console.log('[SW] Token do usuário atualizado');
  // Armazenar token para sincronização
}

// Limpeza periódica de cache
async function cleanOldCache() {
  console.log('[SW] Limpando cache antigo...');

  try {
    // Limpar Cache API
    const cache = await caches.open(DYNAMIC_CACHE);
    const keys = await cache.keys();
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    let deletedFromCache = 0;

    for (const request of keys) {
      const response = await cache.match(request);
      if (response) {
        const date = response.headers.get('date');
        if (date && new Date(date).getTime() < oneHourAgo) {
          await cache.delete(request);
          deletedFromCache++;
        }
      }
    }

    // Limpar IndexedDB
    const deletedFromDB = await offlineStorage.clearOldData();

    console.log(`[SW] Limpeza concluída: ${deletedFromCache} do cache, ${deletedFromDB} do IndexedDB`);

    // Notificar cliente
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'cache-cleaned',
        data: { cacheDeleted: deletedFromCache, dbDeleted: deletedFromDB }
      });
    });

  } catch (error) {
    console.error('[SW] Erro na limpeza de cache:', error);
  }
}

// Monitoramento de conectividade
let isOnline = true;

self.addEventListener('online', () => {
  console.log('[SW] Conexão restaurada');
  isOnline = true;

  // Notificar cliente
  self.clients.matchAll().then(clients => {
    clients.forEach(client => {
      client.postMessage({
        type: 'connection-restored'
      });
    });
  });

  // Tentar sincronização automática
  doBackgroundSync();
});

self.addEventListener('offline', () => {
  console.log('[SW] Conexão perdida');
  isOnline = false;

  // Notificar cliente
  self.clients.matchAll().then(clients => {
    clients.forEach(client => {
      client.postMessage({
        type: 'connection-lost'
      });
    });
  });
});

// Verificar conectividade periodicamente
setInterval(() => {
  if (isOnline && !navigator.onLine) {
    self.dispatchEvent(new Event('offline'));
  } else if (!isOnline && navigator.onLine) {
    self.dispatchEvent(new Event('online'));
  }
}, 30000); // A cada 30 segundos