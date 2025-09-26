// Sistema de Notificações em Tempo Real
class NotificationManager {
    constructor() {
        this.eventSource = null;
        this.notifications = [];
        this.unreadCount = 0;
        this.listeners = new Map();
        this.permission = 'default';
        this.isConnected = false;

        this.init();
    }

    // Inicializar sistema de notificações
    async init() {
        console.log('[Notifications] Inicializando sistema de notificações...');

        // Verificar suporte a notificações
        if (!this.isSupported()) {
            console.warn('[Notifications] Notificações não suportadas neste navegador');
            return;
        }

        // Solicitar permissão
        this.permission = await this.requestPermission();

        // Conectar ao servidor
        this.connect();

        // Configurar event listeners
        this.setupEventListeners();

        console.log('[Notifications] Sistema inicializado');
    }

    // Verificar suporte
    isSupported() {
        return 'Notification' in window && 'EventSource' in window;
    }

    // Solicitar permissão para notificações
    async requestPermission() {
        try {
            const permission = await Notification.requestPermission();
            console.log('[Notifications] Permissão:', permission);
            return permission;
        } catch (error) {
            console.error('[Notifications] Erro ao solicitar permissão:', error);
            return 'denied';
        }
    }

    // Conectar ao servidor via SSE
    connect() {
        if (this.eventSource) {
            this.disconnect();
        }

        try {
            const user = AuthGuard.getCurrentUser();
            if (!user) {
                console.log('[Notifications] Usuário não autenticado, pulando conexão');
                return;
            }

            const url = `${CONFIG.API_BASE_URL}/notifications/stream?user_id=${user.id}&token=${AuthGuard.getToken()}`;
            this.eventSource = new EventSource(url);

            // Evento de conexão aberta
            this.eventSource.onopen = () => {
                console.log('[Notifications] Conectado ao servidor de notificações');
                this.isConnected = true;
                this.emit('connected');
            };

            // Evento de notificação recebida
            this.eventSource.onmessage = (event) => {
                try {
                    const notification = JSON.parse(event.data);
                    this.handleNotification(notification);
                } catch (error) {
                    console.error('[Notifications] Erro ao processar notificação:', error);
                }
            };

            // Tipos específicos de eventos
            this.eventSource.addEventListener('appointment_reminder', (event) => {
                const data = JSON.parse(event.data);
                this.handleAppointmentReminder(data);
            });

            this.eventSource.addEventListener('appointment_confirmed', (event) => {
                const data = JSON.parse(event.data);
                this.handleAppointmentConfirmed(data);
            });

            this.eventSource.addEventListener('loyalty_points', (event) => {
                const data = JSON.parse(event.data);
                this.handleLoyaltyPoints(data);
            });

            this.eventSource.addEventListener('system_message', (event) => {
                const data = JSON.parse(event.data);
                this.handleSystemMessage(data);
            });

            // Evento de erro
            this.eventSource.onerror = (error) => {
                console.error('[Notifications] Erro na conexão SSE:', error);
                this.isConnected = false;
                this.emit('disconnected');

                // Tentar reconectar após 5 segundos
                setTimeout(() => {
                    if (!this.isConnected) {
                        console.log('[Notifications] Tentando reconectar...');
                        this.connect();
                    }
                }, 5000);
            };

        } catch (error) {
            console.error('[Notifications] Erro ao conectar:', error);
        }
    }

    // Desconectar
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.isConnected = false;
            this.emit('disconnected');
        }
    }

    // Lidar com notificação genérica
    handleNotification(notification) {
        console.log('[Notifications] Notificação recebida:', notification);

        // Adicionar à lista
        this.notifications.unshift({
            ...notification,
            id: Date.now(),
            timestamp: new Date(),
            read: false
        });

        this.unreadCount++;

        // Emitir evento
        this.emit('notification', notification);

        // Mostrar notificação push se permitida
        if (this.permission === 'granted') {
            this.showPushNotification(notification);
        }

        // Atualizar UI
        this.updateUI();
    }

    // Lidar com lembrete de agendamento
    handleAppointmentReminder(data) {
        const notification = {
            type: 'appointment_reminder',
            title: 'Lembrete de Agendamento',
            message: `Você tem um agendamento em ${this.formatTime(data.appointment_time)}`,
            icon: '⏰',
            data: data,
            priority: 'high'
        };

        this.handleNotification(notification);
    }

    // Lidar com confirmação de agendamento
    handleAppointmentConfirmed(data) {
        const notification = {
            type: 'appointment_confirmed',
            title: 'Agendamento Confirmado',
            message: `Seu agendamento foi confirmado para ${this.formatDateTime(data.appointment_datetime)}`,
            icon: '✅',
            data: data,
            priority: 'normal'
        };

        this.handleNotification(notification);
    }

    // Lidar com pontos de fidelidade
    handleLoyaltyPoints(data) {
        const notification = {
            type: 'loyalty_points',
            title: 'Pontos de Fidelidade',
            message: `Você ganhou ${data.points} pontos! Total: ${data.total_points}`,
            icon: '🎁',
            data: data,
            priority: 'normal'
        };

        this.handleNotification(notification);
    }

    // Lidar com mensagens do sistema
    handleSystemMessage(data) {
        const notification = {
            type: 'system_message',
            title: data.title || 'Mensagem do Sistema',
            message: data.message,
            icon: 'ℹ️',
            data: data,
            priority: data.priority || 'low'
        };

        this.handleNotification(notification);
    }

    // Mostrar notificação push
    showPushNotification(notification) {
        const options = {
            body: notification.message,
            icon: notification.icon || '/frontend/assets/icon-192x192.png',
            badge: '/frontend/assets/icon-96x96.png',
            tag: notification.type,
            requireInteraction: notification.priority === 'high',
            silent: notification.priority === 'low',
            data: notification.data || {},
            actions: [
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
        if (notification.data && notification.data.appointment_datetime) {
            options.timestamp = new Date(notification.data.appointment_datetime).getTime();
        }

        try {
            const pushNotification = new Notification(notification.title, options);

            // Auto-close após 5 segundos para notificações normais
            if (notification.priority !== 'high') {
                setTimeout(() => {
                    pushNotification.close();
                }, 5000);
            }

            // Event listeners
            pushNotification.onclick = () => {
                this.handleNotificationClick(notification);
                pushNotification.close();
            };

        } catch (error) {
            console.error('[Notifications] Erro ao mostrar push notification:', error);
        }
    }

    // Lidar com clique na notificação
    handleNotificationClick(notification) {
        // Focar na janela
        window.focus();

        // Navegar baseado no tipo de notificação
        switch (notification.type) {
            case 'appointment_reminder':
            case 'appointment_confirmed':
                window.location.href = 'appointments.html';
                break;
            case 'loyalty_points':
                window.location.href = 'profile.html';
                break;
            default:
                // Manter na página atual
                break;
        }
    }

    // Configurar event listeners
    setupEventListeners() {
        // Clique em notificações push
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data && event.data.type === 'notification_click') {
                    this.handleNotificationClick(event.data.notification);
                }
            });
        }

        // Visibilidade da página
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('[Notifications] Página ocultada');
            } else {
                console.log('[Notifications] Página visível');
                // Marcar notificações como lidas quando voltar
                this.markAllAsRead();
            }
        });
    }

    // Sistema de eventos
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('[Notifications] Erro no callback:', error);
                }
            });
        }
    }

    // Gerenciamento de notificações
    getNotifications(limit = 50) {
        return this.notifications.slice(0, limit);
    }

    getUnreadCount() {
        return this.unreadCount;
    }

    markAsRead(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification && !notification.read) {
            notification.read = true;
            this.unreadCount = Math.max(0, this.unreadCount - 1);
            this.updateUI();
        }
    }

    markAllAsRead() {
        let marked = 0;
        this.notifications.forEach(notification => {
            if (!notification.read) {
                notification.read = true;
                marked++;
            }
        });
        this.unreadCount = Math.max(0, this.unreadCount - marked);
        this.updateUI();
    }

    clearNotifications() {
        this.notifications = [];
        this.unreadCount = 0;
        this.updateUI();
    }

    // Utilitários de formatação
    formatTime(timeStr) {
        try {
            const [hours, minutes] = timeStr.split(':');
            const date = new Date();
            date.setHours(hours, minutes);
            return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        } catch (error) {
            return timeStr;
        }
    }

    formatDateTime(dateTimeStr) {
        try {
            const date = new Date(dateTimeStr);
            return date.toLocaleString('pt-BR', {
                weekday: 'short',
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateTimeStr;
        }
    }

    // Atualizar UI (método para ser sobrescrito)
    updateUI() {
        // Este método pode ser sobrescrito para atualizar a UI específica
        console.log(`[Notifications] ${this.unreadCount} notificações não lidas`);
    }

    // Enviar notificação de teste
    sendTestNotification() {
        const testNotification = {
            type: 'system_message',
            title: 'Teste de Notificação',
            message: 'Esta é uma notificação de teste do sistema Aluvi!',
            icon: '🧪',
            priority: 'normal'
        };

        this.handleNotification(testNotification);
    }
}

// Classe para gerenciar notificações na UI
class NotificationUI {
    constructor(container) {
        this.container = container;
        this.manager = new NotificationManager();
        this.notificationsList = null;
        this.unreadBadge = null;

        this.init();
    }

    init() {
        this.createUI();
        this.setupEventListeners();
        this.updateUI();
    }

    createUI() {
        // Container principal
        this.container.innerHTML = `
            <div class="notification-center">
                <div class="notification-header">
                    <h3>Notificações</h3>
                    <div class="notification-actions">
                        <button class="btn btn-sm btn-outline mark-all-read">Marcar todas como lidas</button>
                        <button class="btn btn-sm btn-outline clear-all">Limpar todas</button>
                    </div>
                </div>
                <div class="notification-list">
                    <div class="notification-empty">
                        <div class="empty-icon">🔔</div>
                        <div class="empty-text">Nenhuma notificação</div>
                        <div class="empty-subtext">Você será notificado sobre atualizações importantes</div>
                    </div>
                </div>
                <div class="notification-footer">
                    <div class="connection-status">
                        <span class="status-indicator"></span>
                        <span class="status-text">Conectado</span>
                    </div>
                </div>
            </div>
        `;

        this.notificationsList = this.container.querySelector('.notification-list');
        this.unreadBadge = this.createUnreadBadge();
    }

    createUnreadBadge() {
        const badge = document.createElement('div');
        badge.className = 'notification-badge';
        badge.style.display = 'none';
        document.body.appendChild(badge);
        return badge;
    }

    setupEventListeners() {
        // Botões de ação
        this.container.querySelector('.mark-all-read').addEventListener('click', () => {
            this.manager.markAllAsRead();
        });

        this.container.querySelector('.clear-all').addEventListener('click', () => {
            if (confirm('Tem certeza que deseja limpar todas as notificações?')) {
                this.manager.clearNotifications();
            }
        });

        // Eventos do manager
        this.manager.on('notification', (notification) => {
            this.addNotification(notification);
        });

        this.manager.on('connected', () => {
            this.updateConnectionStatus(true);
        });

        this.manager.on('disconnected', () => {
            this.updateConnectionStatus(false);
        });
    }

    addNotification(notification) {
        const notificationElement = this.createNotificationElement(notification);
        const emptyState = this.notificationsList.querySelector('.notification-empty');

        if (emptyState) {
            emptyState.remove();
        }

        this.notificationsList.insertBefore(notificationElement, this.notificationsList.firstChild);
        this.updateUI();
    }

    createNotificationElement(notification) {
        const element = document.createElement('div');
        element.className = `notification-item ${notification.read ? 'read' : 'unread'}`;
        element.dataset.id = notification.id;

        element.innerHTML = `
            <div class="notification-icon">${notification.icon || '📢'}</div>
            <div class="notification-content">
                <div class="notification-title">${notification.title}</div>
                <div class="notification-message">${notification.message}</div>
                <div class="notification-time">${this.formatTimeAgo(notification.timestamp)}</div>
            </div>
            <div class="notification-actions">
                ${!notification.read ? '<button class="mark-read">✓</button>' : ''}
                <button class="delete-notification">×</button>
            </div>
        `;

        // Event listeners
        if (!notification.read) {
            element.querySelector('.mark-read').addEventListener('click', () => {
                this.manager.markAsRead(notification.id);
                element.classList.add('read');
                element.classList.remove('unread');
                element.querySelector('.mark-read').remove();
            });
        }

        element.querySelector('.delete-notification').addEventListener('click', () => {
            element.remove();
            // Remover da lista do manager
            const index = this.manager.notifications.findIndex(n => n.id === notification.id);
            if (index > -1) {
                this.manager.notifications.splice(index, 1);
                this.updateUI();
            }
        });

        // Marcar como lida ao clicar
        element.addEventListener('click', () => {
            if (!notification.read) {
                this.manager.markAsRead(notification.id);
                element.classList.add('read');
                element.classList.remove('unread');
                const markReadBtn = element.querySelector('.mark-read');
                if (markReadBtn) markReadBtn.remove();
            }
        });

        return element;
    }

    updateUI() {
        const unreadCount = this.manager.getUnreadCount();

        // Atualizar badge
        if (unreadCount > 0) {
            this.unreadBadge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            this.unreadBadge.style.display = 'block';
        } else {
            this.unreadBadge.style.display = 'none';
        }

        // Mostrar/esconder estado vazio
        const hasNotifications = this.manager.notifications.length > 0;
        const emptyState = this.notificationsList.querySelector('.notification-empty');

        if (!hasNotifications && !emptyState) {
            this.notificationsList.innerHTML = `
                <div class="notification-empty">
                    <div class="empty-icon">🔔</div>
                    <div class="empty-text">Nenhuma notificação</div>
                    <div class="empty-subtext">Você será notificado sobre atualizações importantes</div>
                </div>
            `;
        }
    }

    updateConnectionStatus(connected) {
        const statusIndicator = this.container.querySelector('.status-indicator');
        const statusText = this.container.querySelector('.status-text');

        if (connected) {
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = 'Conectado';
        } else {
            statusIndicator.className = 'status-indicator disconnected';
            statusText.textContent = 'Desconectado';
        }
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Agora';
        if (minutes < 60) return `${minutes}min atrás`;
        if (hours < 24) return `${hours}h atrás`;
        if (days < 7) return `${days}d atrás`;

        return date.toLocaleDateString('pt-BR');
    }

    // Mostrar/ocultar centro de notificações
    toggle() {
        const isVisible = this.container.style.display !== 'none';
        this.container.style.display = isVisible ? 'none' : 'block';

        if (!isVisible) {
            // Marcar como lidas quando abrir
            setTimeout(() => this.manager.markAllAsRead(), 1000);
        }
    }
}

// Exportar para uso global
window.NotificationManager = NotificationManager;
window.NotificationUI = NotificationUI;