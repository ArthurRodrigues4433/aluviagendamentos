/**
 * Gerenciador de Notificações - Sistema avançado de notificações.
 * Gerencia notificações toast, alertas e feedback do usuário.
 */

export default class NotificationManager {
    constructor(options = {}) {
        this.options = {
            containerId: options.containerId || 'notifications-container',
            position: options.position || 'top-right', // top-right, top-left, bottom-right, bottom-left
            maxNotifications: options.maxNotifications || 5,
            defaultDuration: options.defaultDuration || 5000,
            ...options
        };

        this.notifications = new Map();
        this.container = null;
        this.init();
    }

    /**
     * Inicializar sistema de notificações
     */
    init() {
        // Create container if it doesn't exist
        this.container = document.getElementById(this.options.containerId);
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = this.options.containerId;
            this.container.className = `notifications-container notifications-${this.options.position}`;
            document.body.appendChild(this.container);
        }

        // Add styles if not present
        this.addStyles();
    }

    /**
     * Adicionar estilos de notificação ao documento
     */
    addStyles() {
        if (document.getElementById('notification-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notifications-container {
                position: fixed;
                z-index: 10000;
                pointer-events: none;
                max-width: 400px;
            }

            .notifications-top-right {
                top: 20px;
                right: 20px;
            }

            .notifications-top-left {
                top: 20px;
                left: 20px;
            }

            .notifications-bottom-right {
                bottom: 20px;
                right: 20px;
            }

            .notifications-bottom-left {
                bottom: 20px;
                left: 20px;
            }

            .notification {
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin-bottom: 10px;
                padding: 16px;
                pointer-events: auto;
                transform: translateX(100%);
                transition: transform 0.3s ease, opacity 0.3s ease;
                opacity: 0;
                border-left: 4px solid;
                cursor: pointer;
            }

            .notification.show {
                transform: translateX(0);
                opacity: 1;
            }

            .notification.success { border-left-color: #28a745; }
            .notification.error { border-left-color: #dc3545; }
            .notification.warning { border-left-color: #ffc107; }
            .notification.info { border-left-color: #17a2b8; }

            .notification-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }

            .notification-title {
                font-weight: 600;
                color: #333;
                margin: 0;
                font-size: 14px;
            }

            .notification-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #999;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .notification-close:hover {
                color: #666;
            }

            .notification-message {
                color: #666;
                font-size: 14px;
                line-height: 1.4;
                margin: 0;
            }

            .notification-actions {
                margin-top: 12px;
                display: flex;
                gap: 8px;
            }

            .notification-actions button {
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
                transition: background-color 0.2s;
            }

            .notification-actions .btn-success {
                background: #28a745;
                color: white;
            }

            .notification-actions .btn-success:hover {
                background: #218838;
            }

            .notification-actions .btn-danger {
                background: #dc3545;
                color: white;
            }

            .notification-actions .btn-danger:hover {
                background: #c82333;
            }

            .notification-actions .btn-primary {
                background: #007bff;
                color: white;
            }

            .notification-actions .btn-primary:hover {
                background: #0056b3;
            }

            .notification-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: rgba(255,255,255,0.3);
                border-radius: 0 0 8px 8px;
                animation: progress linear;
            }

            @keyframes progress {
                from { width: 100%; }
                to { width: 0%; }
            }
        `;
        document.head.appendChild(styles);
    }

    /**
     * Mostrar notificação
     * @param {string} title - Título da notificação
     * @param {string} message - Mensagem da notificação
     * @param {string} type - Tipo de notificação (success, error, warning, info)
     * @param {Array} actions - Botões de ação
     * @param {number} duration - Duração de auto-ocultação em ms
     * @returns {string} ID da notificação
     */
    show(title, message, type = 'info', actions = null, duration = null) {
        const id = this.generateId();

        // Remove old notifications if at limit
        if (this.notifications.size >= this.options.maxNotifications) {
            const oldestId = this.notifications.keys().next().value;
            this.remove(oldestId);
        }

        const notification = this.createNotification(id, title, message, type, actions);
        this.container.appendChild(notification);

        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Auto-hide if duration specified
        const hideDuration = duration !== null ? duration : this.options.defaultDuration;
        if (hideDuration > 0) {
            const timeoutId = setTimeout(() => {
                this.remove(id);
            }, hideDuration);

            // Store notification data
            this.notifications.set(id, {
                element: notification,
                timeoutId,
                type,
                created: Date.now()
            });
        } else {
            this.notifications.set(id, {
                element: notification,
                type,
                created: Date.now()
            });
        }

        return id;
    }

    /**
     * Criar elemento de notificação
     * @param {string} id - ID da notificação
     * @param {string} title - Título
     * @param {string} message - Mensagem
     * @param {string} type - Tipo
     * @param {Array} actions - Ações
     * @returns {HTMLElement} Elemento de notificação
     */
    createNotification(id, title, message, type, actions) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.dataset.id = id;

        let actionsHtml = '';
        if (actions && actions.length > 0) {
            actionsHtml = `
                <div class="notification-actions">
                    ${actions.map(action => `
                        <button class="btn-${action.type || 'primary'}"
                                onclick="NotificationManager.handleAction('${id}', '${action.callback}')">
                            ${action.label}
                        </button>
                    `).join('')}
                </div>
            `;
        }

        notification.innerHTML = `
            <div class="notification-header">
                <h4 class="notification-title">${title}</h4>
                <button class="notification-close" onclick="NotificationManager.remove('${id}')">&times;</button>
            </div>
            <div class="notification-message">${message}</div>
            ${actionsHtml}
        `;

        return notification;
    }

    /**
     * Remover notificação
     * @param {string} id - ID da notificação
     */
    remove(id) {
        const notificationData = this.notifications.get(id);
        if (!notificationData) return;

        const { element, timeoutId } = notificationData;

        // Clear timeout
        if (timeoutId) {
            clearTimeout(timeoutId);
        }

        // Animate out
        element.classList.remove('show');

        // Remove after animation
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            this.notifications.delete(id);
        }, 300);
    }

    /**
     * Lidar com clique no botão de ação
     * @param {string} notificationId - ID da notificação
     * @param {string} callback - Nome da função callback
     */
    handleAction(notificationId, callback) {
        // Execute callback if it's a function
        if (typeof window[callback] === 'function') {
            window[callback]();
        }

        // Remove notification
        this.remove(notificationId);
    }

    /**
     * Clear all notifications
     */
    clearAll() {
        for (const id of this.notifications.keys()) {
            this.remove(id);
        }
    }

    /**
     * Gerar ID único de notificação
     * @returns {string} ID único
     */
    generateId() {
        return 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // ============ MÉTODOS DE CONVENIÊNCIA ============

    /**
     * Mostrar notificação de sucesso
     * @param {string} title - Título
     * @param {string} message - Mensagem
     * @param {number} duration - Duração
     * @returns {string} ID da notificação
     */
    success(title, message, duration = null) {
        return this.show(title, message, 'success', null, duration);
    }

    /**
     * Mostrar notificação de erro
     * @param {string} title - Título
     * @param {string} message - Mensagem
     * @param {number} duration - Duração
     * @returns {string} ID da notificação
     */
    error(title, message, duration = null) {
        return this.show(title, message, 'error', null, duration);
    }

    /**
     * Mostrar notificação de aviso
     * @param {string} title - Título
     * @param {string} message - Mensagem
     * @param {number} duration - Duração
     * @returns {string} ID da notificação
     */
    warning(title, message, duration = null) {
        return this.show(title, message, 'warning', null, duration);
    }

    /**
     * Mostrar notificação de informação
     * @param {string} title - Título
     * @param {string} message - Mensagem
     * @param {number} duration - Duração
     * @returns {string} ID da notificação
     */
    info(title, message, duration = null) {
        return this.show(title, message, 'info', null, duration);
    }

    /**
     * Mostrar notificação de confirmação com ações
     * @param {string} title - Título
     * @param {string} message - Mensagem
     * @param {Function} onConfirm - Callback de confirmação
     * @param {Function} onCancel - Callback de cancelamento
     * @returns {string} ID da notificação
     */
    confirm(title, message, onConfirm, onCancel = null) {
        const actions = [
            {
                label: 'Cancelar',
                type: 'secondary',
                callback: onCancel ? `(${onCancel})()` : `NotificationManager.remove('${this.generateId()}')`
            },
            {
                label: 'Confirmar',
                type: 'primary',
                callback: `(${onConfirm})()`
            }
        ];

        return this.show(title, message, 'warning', actions, 0); // No auto-hide
    }
}

// Global instance
const notificationManager = new NotificationManager();

// Make available globally
window.NotificationManager = notificationManager;

export { notificationManager as default };