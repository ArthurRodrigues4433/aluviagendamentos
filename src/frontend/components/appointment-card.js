// Componente AppointmentCard - Card reutilizável para agendamentos
class AppointmentCard {
    constructor(options = {}) {
        this.options = {
            showActions: true,
            showStatus: true,
            compact: false,
            clickable: true,
            onClick: null,
            onCancel: null,
            onEdit: null,
            ...options
        };

        this.element = null;
        this.appointment = null;
    }

    // Renderizar card com dados do agendamento
    render(appointment) {
        this.appointment = appointment;

        const card = document.createElement('div');
        card.className = `appointment-card ${this.getStatusClass()} ${this.options.compact ? 'compact' : ''}`;

        if (this.options.clickable && this.options.onClick) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => this.options.onClick(appointment));
        }

        card.innerHTML = this.getCardHTML();
        this.element = card;

        // Adicionar event listeners para ações
        this.attachEventListeners();

        return card;
    }

    // HTML do card
    getCardHTML() {
        const date = new Date(this.appointment.data_hora);
        const isPast = date < new Date();
        const isToday = date.toDateString() === new Date().toDateString();

        return `
            <div class="appointment-header">
                <div class="appointment-date">
                    <div class="date-day">${date.getDate()}</div>
                    <div class="date-month">${date.toLocaleDateString('pt-BR', { month: 'short' })}</div>
                </div>
                <div class="appointment-info">
                    <h3>${this.appointment.servico?.nome || 'Serviço'}</h3>
                    <p class="appointment-professional">
                        ${this.appointment.profissional ? `com ${this.appointment.profissional.nome}` : 'Profissional não definido'}
                    </p>
                    <p class="appointment-time">
                        ${date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                        ${isToday ? '<span class="badge badge-info">Hoje</span>' : ''}
                        ${isPast ? '<span class="badge badge-secondary">Passado</span>' : ''}
                    </p>
                </div>
            </div>
            <div class="appointment-footer">
                ${this.options.showStatus ? `
                    <div class="appointment-status">
                        <span class="badge ${this.getStatusBadgeClass()}">${this.getStatusText()}</span>
                    </div>
                ` : ''}
                <div class="appointment-price">
                    ${Formatter.currency(this.appointment.valor)}
                </div>
            </div>
            ${this.options.showActions && this.canShowActions() ? this.getActionsHTML() : ''}
        `;
    }

    // HTML das ações
    getActionsHTML() {
        const actions = [];

        if (this.canCancel()) {
            actions.push(`<button class="btn btn-sm btn-outline cancel-btn" data-action="cancel">Cancelar</button>`);
        }

        if (this.canEdit()) {
            actions.push(`<button class="btn btn-sm btn-outline edit-btn" data-action="edit">Editar</button>`);
        }

        if (this.canConfirm()) {
            actions.push(`<button class="btn btn-sm btn-success confirm-btn" data-action="confirm">Confirmar</button>`);
        }

        if (actions.length > 0) {
            return `<div class="appointment-actions">${actions.join('')}</div>`;
        }

        return '';
    }

    // Verificar se pode mostrar ações
    canShowActions() {
        return this.canCancel() || this.canEdit() || this.canConfirm();
    }

    // Verificar se pode cancelar
    canCancel() {
        return ['agendado', 'confirmado'].includes(this.appointment.status);
    }

    // Verificar se pode editar
    canEdit() {
        return this.appointment.status === 'agendado';
    }

    // Verificar se pode confirmar
    canConfirm() {
        return this.appointment.status === 'agendado';
    }

    // Classe CSS baseada no status
    getStatusClass() {
        const date = new Date(this.appointment.data_hora);
        const isPast = date < new Date();
        const isToday = date.toDateString() === new Date().toDateString();

        let classes = [];
        if (isPast) classes.push('past');
        if (isToday) classes.push('today');

        return classes.join(' ');
    }

    // Classe do badge de status
    getStatusBadgeClass() {
        const statusClasses = {
            'agendado': 'badge-warning',
            'confirmado': 'badge-success',
            'concluido': 'badge-success',
            'cancelado': 'badge-danger',
            'nao_compareceu': 'badge-danger'
        };

        return statusClasses[this.appointment.status] || 'badge-secondary';
    }

    // Texto do status
    getStatusText() {
        const statusTexts = {
            'agendado': 'Agendado',
            'confirmado': 'Confirmado',
            'concluido': 'Concluído',
            'cancelado': 'Cancelado',
            'nao_compareceu': 'Não Compareceu'
        };

        return statusTexts[this.appointment.status] || this.appointment.status;
    }

    // Anexar event listeners
    attachEventListeners() {
        if (!this.element) return;

        // Cancelar
        const cancelBtn = this.element.querySelector('.cancel-btn');
        if (cancelBtn && this.options.onCancel) {
            cancelBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.options.onCancel(this.appointment);
            });
        }

        // Editar
        const editBtn = this.element.querySelector('.edit-btn');
        if (editBtn && this.options.onEdit) {
            editBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.options.onEdit(this.appointment);
            });
        }

        // Confirmar
        const confirmBtn = this.element.querySelector('.confirm-btn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleConfirm();
            });
        }
    }

    // Lidar com confirmação
    async handleConfirm() {
        if (!confirm('Deseja confirmar este agendamento?')) return;

        try {
            await api.updateAppointmentStatus(this.appointment.id, 'confirmado');
            UI.showSuccess('Agendamento confirmado com sucesso!');

            // Atualizar status local
            this.appointment.status = 'confirmado';

            // Re-renderizar card
            if (this.element && this.element.parentNode) {
                const newCard = this.render(this.appointment);
                this.element.parentNode.replaceChild(newCard, this.element);
            }

        } catch (error) {
            console.error('[AppointmentCard] Erro ao confirmar:', error);
            UI.showError('Erro ao confirmar agendamento');
        }
    }

    // Atualizar dados do agendamento
    update(appointment) {
        this.appointment = appointment;
        if (this.element) {
            const newCard = this.render(appointment);
            this.element.parentNode.replaceChild(newCard, this.element);
        }
    }

    // Destruir componente
    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
        this.appointment = null;
    }
}

// Função utilitária para criar múltiplos cards
AppointmentCard.renderMultiple = function(appointments, container, options = {}) {
    if (!container) return [];

    container.innerHTML = '';

    const cards = appointments.map(appointment => {
        const card = new AppointmentCard(options);
        const element = card.render(appointment);
        container.appendChild(element);
        return card;
    });

    return cards;
};

// Exportar para uso global
window.AppointmentCard = AppointmentCard;