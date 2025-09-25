/**
 * Componente Modal - Sistema de diálogo modal reutilizável.
 * Fornece funcionalidade modal consistente em toda a aplicação.
 */

export default class Modal {
    constructor(options = {}) {
        this.options = {
            size: options.size || 'medium', // small, medium, large
            closable: options.closable !== false,
            backdrop: options.backdrop !== false,
            animation: options.animation !== false,
            ...options
        };

        this.modal = null;
        this.isOpen = false;
        this.onClose = options.onClose || null;
        this.onOpen = options.onOpen || null;
    }

    /**
     * Criar estrutura HTML do modal
     * @returns {HTMLElement} Elemento modal
     */
    create() {
        const modal = document.createElement('div');
        modal.className = `modal ${this.options.animation ? 'modal-animated' : ''}`;
        modal.innerHTML = `
            <div class="modal-backdrop ${this.options.backdrop ? '' : 'modal-backdrop-transparent'}"></div>
            <div class="modal-content modal-${this.options.size}">
                ${this.options.closable ? '<button class="modal-close" data-action="close">&times;</button>' : ''}
                <div class="modal-header">
                    <h3 class="modal-title">${this.options.title || ''}</h3>
                </div>
                <div class="modal-body">
                    ${this.options.content || ''}
                </div>
                ${this.options.footer ? `<div class="modal-footer">${this.options.footer}</div>` : ''}
            </div>
        `;

        // Add event listeners
        this.setupEventListeners(modal);

        this.modal = modal;
        return modal;
    }

    /**
     * Configurar ouvintes de eventos para o modal
     * @param {HTMLElement} modal - Elemento modal
     */
    setupEventListeners(modal) {
        // Close button
        const closeBtn = modal.querySelector('[data-action="close"]');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // Backdrop click
        const backdrop = modal.querySelector('.modal-backdrop');
        if (backdrop && this.options.closable) {
            backdrop.addEventListener('click', () => this.close());
        }

        // Action buttons
        modal.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (action && action !== 'close') {
                this.handleAction(action, e.target);
            }
        });

        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (this.isOpen && e.key === 'Escape' && this.options.closable) {
                this.close();
            }
        });
    }

    /**
     * Lidar com ações de botão
     * @param {string} action - Nome da ação
     * @param {HTMLElement} button - Elemento botão
     */
    handleAction(action, button) {
        // Emit custom event
        const event = new CustomEvent('modal:action', {
            detail: { action, button, modal: this }
        });
        this.modal.dispatchEvent(event);

        // Default close action
        if (action === 'close') {
            this.close();
        }
    }

    /**
     * Abrir modal
     */
    open() {
        if (!this.modal) {
            this.create();
        }

        document.body.appendChild(this.modal);
        document.body.classList.add('modal-open');

        // Trigger animation
        setTimeout(() => {
            this.modal.classList.add('show');
            this.isOpen = true;

            if (this.onOpen) {
                this.onOpen(this);
            }
        }, 10);
    }

    /**
     * Fechar modal
     */
    close() {
        if (!this.modal || !this.isOpen) return;

        this.modal.classList.remove('show');
        document.body.classList.remove('modal-open');

        setTimeout(() => {
            if (this.modal.parentNode) {
                this.modal.parentNode.removeChild(this.modal);
            }
            this.isOpen = false;

            if (this.onClose) {
                this.onClose(this);
            }
        }, 300); // Match CSS transition duration
    }

    /**
     * Atualizar conteúdo do modal
     * @param {Object} options - Opções de conteúdo
     */
    update(options) {
        if (!this.modal) return;

        if (options.title) {
            const titleEl = this.modal.querySelector('.modal-title');
            if (titleEl) titleEl.textContent = options.title;
        }

        if (options.content) {
            const bodyEl = this.modal.querySelector('.modal-body');
            if (bodyEl) bodyEl.innerHTML = options.content;
        }

        if (options.footer) {
            let footerEl = this.modal.querySelector('.modal-footer');
            if (!footerEl) {
                footerEl = document.createElement('div');
                footerEl.className = 'modal-footer';
                this.modal.querySelector('.modal-content').appendChild(footerEl);
            }
            footerEl.innerHTML = options.footer;
        }
    }

    /**
     * Definir tamanho do modal
     * @param {string} size - Classe de tamanho (small, medium, large)
     */
    setSize(size) {
        if (!this.modal) return;

        const content = this.modal.querySelector('.modal-content');
        if (content) {
            content.className = content.className.replace(/modal-\w+/, `modal-${size}`);
        }
    }

    /**
     * Verificar se o modal está atualmente aberto
     * @returns {boolean} Status de abertura
     */
    isVisible() {
        return this.isOpen;
    }

    /**
     * Destruir modal e limpar
     */
    destroy() {
        if (this.modal) {
            this.close();
            this.modal = null;
        }
    }

    // ============ STATIC METHODS ============

    /**
     * Criar e mostrar um modal de alerta simples
     * @param {string} title - Título do modal
     * @param {string} message - Mensagem de alerta
     * @param {string} type - Tipo de alerta (info, success, warning, error)
     * @returns {Modal} Instância do modal
     */
    static alert(title, message, type = 'info') {
        const modal = new Modal({
            title,
            content: `<div class="alert alert-${type}">${message}</div>`,
            footer: '<button class="btn btn-primary" data-action="close">OK</button>',
            size: 'small'
        });

        modal.open();
        return modal;
    }

    /**
     * Criar e mostrar um modal de confirmação
     * @param {string} title - Título do modal
     * @param {string} message - Mensagem de confirmação
     * @param {Function} onConfirm - Callback de confirmação
     * @param {Function} onCancel - Callback de cancelamento
     * @returns {Modal} Instância do modal
     */
    static confirm(title, message, onConfirm, onCancel = null) {
        const modal = new Modal({
            title,
            content: `<p>${message}</p>`,
            footer: `
                <button class="btn btn-secondary" data-action="cancel">Cancelar</button>
                <button class="btn btn-primary" data-action="confirm">Confirmar</button>
            `,
            size: 'small',
            onClose: () => {
                if (onCancel) onCancel();
            }
        });

        modal.modal.addEventListener('modal:action', (e) => {
            if (e.detail.action === 'confirm' && onConfirm) {
                onConfirm();
            } else if (e.detail.action === 'cancel' && onCancel) {
                onCancel();
            }
        });

        modal.open();
        return modal;
    }

    /**
     * Criar e mostrar um modal de carregamento
     * @param {string} message - Mensagem de carregamento
     * @returns {Modal} Instância do modal
     */
    static loading(message = 'Carregando...') {
        const modal = new Modal({
            content: `
                <div class="loading-modal">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">${message}</div>
                </div>
            `,
            closable: false,
            backdrop: false,
            size: 'small'
        });

        modal.open();
        return modal;
    }
}