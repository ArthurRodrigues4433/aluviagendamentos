/**
 * Utilitários de UI - Funções auxiliares de interface do usuário.
 * Gerencia estados de carregamento, alertas e feedback do usuário.
 */

export default class UiUtils {
    /**
     * Mostrar indicador de carregamento em um elemento
     * @param {HTMLElement} element - Elemento onde mostrar carregamento
     */
    static showLoading(element) {
        if (element) {
            element.innerHTML = '<div class="loading">Carregando...</div>';
        }
    }

    /**
     * Mostrar mensagem de sucesso temporariamente
     * @param {string} message - Mensagem a exibir
     * @param {HTMLElement} container - Container onde inserir (padrão: body)
     */
    static showSuccess(message, container = null) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success';
        alert.textContent = message;

        if (container) {
            container.prepend(alert);
        } else {
            document.body.prepend(alert);
        }

        setTimeout(() => alert.remove(), 5000);
    }

    /**
     * Mostrar mensagem de erro temporariamente
     * @param {string} message - Mensagem de erro
     * @param {HTMLElement} container - Container onde inserir
     */
    static showError(message, container = null) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-error';
        alert.textContent = message;

        if (container) {
            container.prepend(alert);
        } else {
            document.body.prepend(alert);
        }

        setTimeout(() => alert.remove(), 5000);
    }

    /**
     * Mostrar mensagem informativa em elemento específico ou via alert
     * @param {string} message - Mensagem a exibir
     * @param {string} targetId - ID do elemento alvo (opcional)
     */
    static showInfo(message, targetId = null) {
        if (targetId) {
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.innerHTML = `<div class="alert alert-info">${message}</div>`;
                return;
            }
        }
        alert(message);
    }

    /**
     * Remover todas as mensagens de alerta da página
     */
    static clearAlerts() {
        document.querySelectorAll('.alert').forEach(alert => alert.remove());
    }

    /**
     * Criar um diálogo modal
     * @param {string} title - Título do modal
     * @param {string} content - HTML do conteúdo do modal
     * @param {Array} buttons - Array de objetos de botão {text, class, callback}
     * @returns {HTMLElement} Elemento modal
     */
    static createModal(title, content, buttons = []) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                ${buttons.length > 0 ? `
                    <div class="modal-footer">
                        ${buttons.map(btn => `
                            <button class="btn ${btn.class || 'btn-secondary'}"
                                    onclick="${btn.callback}">${btn.text}</button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        return modal;
    }

    /**
     * Mostrar diálogo de confirmação
     * @param {string} message - Mensagem de confirmação
     * @param {Function} onConfirm - Callback para confirmação
     * @param {Function} onCancel - Callback para cancelamento
     */
    static showConfirm(message, onConfirm, onCancel = null) {
        const modal = this.createModal(
            'Confirmação',
            `<p>${message}</p>`,
            [
                {
                    text: 'Cancelar',
                    class: 'btn-secondary',
                    callback: onCancel ? `(${onCancel})()` : 'this.closest(".modal").remove()'
                },
                {
                    text: 'Confirmar',
                    class: 'btn-primary',
                    callback: `(${onConfirm})(); this.closest(".modal").remove()`
                }
            ]
        );

        document.body.appendChild(modal);
        modal.classList.add('show');
    }

    /**
     * Criar um input de formulário com label
     * @param {string} label - Label do input
     * @param {string} type - Tipo do input
     * @param {string} name - Nome do input
     * @param {Object} options - Opções adicionais {required, value, placeholder, etc}
     * @returns {string} String HTML
     */
    static createFormInput(label, type, name, options = {}) {
        const required = options.required ? 'required' : '';
        const value = options.value || '';
        const placeholder = options.placeholder || '';

        return `
            <div class="form-group">
                <label class="form-label">${label}</label>
                <input type="${type}" name="${name}" class="form-control"
                       value="${value}" placeholder="${placeholder}" ${required}>
            </div>
        `;
    }

    /**
     * Criar um dropdown select
     * @param {string} label - Label do select
     * @param {string} name - Nome do select
     * @param {Array} options - Array de objetos {value, text}
     * @param {Object} selectOptions - Opções adicionais do select
     * @returns {string} String HTML
     */
    static createSelect(label, name, options, selectOptions = {}) {
        const required = selectOptions.required ? 'required' : '';
        const value = selectOptions.value || '';

        const optionHtml = options.map(opt =>
            `<option value="${opt.value}" ${opt.value === value ? 'selected' : ''}>${opt.text}</option>`
        ).join('');

        return `
            <div class="form-group">
                <label class="form-label">${label}</label>
                <select name="${name}" class="form-control form-select" ${required}>
                    ${optionHtml}
                </select>
            </div>
        `;
    }

    /**
     * Habilitar/desabilitar elementos de formulário
     * @param {HTMLElement} form - Elemento form
     * @param {boolean} enabled - Se deve habilitar ou desabilitar
     */
    static setFormEnabled(form, enabled) {
        const elements = form.querySelectorAll('input, select, textarea, button');
        elements.forEach(element => {
            element.disabled = !enabled;
            element.style.opacity = enabled ? '1' : '0.5';
        });
    }

    /**
     * Mostrar/ocultar overlay de carregamento no elemento
     * @param {HTMLElement} element - Elemento a sobrepor
     * @param {boolean} show - Se deve mostrar ou ocultar
     * @param {string} message - Mensagem de carregamento
     */
    static showLoadingOverlay(element, show, message = 'Carregando...') {
        let overlay = element.querySelector('.loading-overlay');

        if (show) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.className = 'loading-overlay';
                overlay.innerHTML = `
                    <div class="loading-content">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">${message}</div>
                    </div>
                `;
                overlay.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10;
                    border-radius: 0.25rem;
                `;
                element.style.position = 'relative';
                element.appendChild(overlay);
            }
            overlay.style.display = 'flex';
        } else if (overlay) {
            overlay.style.display = 'none';
        }
    }

    /**
     * Animar elemento com efeito de fade
     * @param {HTMLElement} element - Elemento a animar
     * @param {string} direction - 'in' ou 'out'
     */
    static fade(element, direction) {
        if (direction === 'in') {
            element.style.opacity = '0';
            element.style.display = 'block';
            element.style.transition = 'opacity 0.3s ease';

            setTimeout(() => {
                element.style.opacity = '1';
            }, 10);
        } else if (direction === 'out') {
            element.style.transition = 'opacity 0.3s ease';
            element.style.opacity = '0';

            setTimeout(() => {
                element.style.display = 'none';
            }, 300);
        }
    }
}