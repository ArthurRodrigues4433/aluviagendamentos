/**
 * Exemplos de Integração - Dashboard Real-Time Update System
 *
 * Este arquivo contém exemplos práticos de como integrar o sistema
 * de atualização em tempo real com diferentes operações CRUD.
 *
 * Copie e adapte estes exemplos para suas necessidades específicas.
 */

// ==========================================
// EXEMPLO 1: Integração com Operações de Mensalidade
// ==========================================

/**
 * Exemplo de como integrar atualização em tempo real
 * com operações de gerenciamento de mensalidade
 */
class SubscriptionManager {
    constructor() {
        this.realtime = window.DashboardRealtime;
    }

    /**
     * Atualizar status de mensalidade com refresh automático
     */
    async updateSubscription(salonId, paymentStatus, dueDate) {
        try {
            // Usar wrapper para operação com refresh automático
            const result = await this.realtime.performDataOperation(async () => {
                return await api.request(`/salons/admin/${salonId}/subscription`, {
                    method: 'PUT',
                    body: JSON.stringify({
                        mensalidade_pago: paymentStatus,
                        data_vencimento: dueDate
                    })
                });
            }, {
                refreshSalonId: salonId // Atualizar apenas este salão
            });

            if (result.success) {
                UI.showSuccess('Mensalidade atualizada com sucesso!');
                closeSubscriptionModal();
            } else {
                UI.showError(result.error || 'Erro ao atualizar mensalidade');
            }

        } catch (error) {
            console.error('Erro ao atualizar mensalidade:', error);
            UI.showError('Erro ao atualizar mensalidade');
        }
    }

    /**
     * Atualizar apenas estatísticas específicas
     */
    async refreshOnlyStats() {
        await this.realtime.refreshStats();
    }

    /**
     * Atualizar apenas tabela de mensalidades
     */
    async refreshOnlySubscriptions() {
        await this.realtime.refreshSubscriptionsList();
    }
}

// ==========================================
// EXEMPLO 2: Integração com CRUD de Salões
// ==========================================

/**
 * Exemplo de integração com operações de salão
 */
class SalonManager {
    constructor() {
        this.realtime = window.DashboardRealtime;
    }

    /**
     * Criar novo salão com refresh completo
     */
    async createSalon(salonData) {
        try {
            const result = await this.realtime.performDataOperation(async () => {
                return await api.request('/salons/admin/create', {
                    method: 'POST',
                    body: JSON.stringify(salonData)
                });
            }, {
                refresh: true // Refresh completo do dashboard
            });

            if (result.success) {
                UI.showSuccess('Salão criado com sucesso!');
                closeSalonModal();
            } else {
                UI.showError(result.error || 'Erro ao criar salão');
            }

        } catch (error) {
            console.error('Erro ao criar salão:', error);
            UI.showError('Erro ao criar salão');
        }
    }

    /**
     * Atualizar dados de um salão específico
     */
    async updateSalon(salonId, updateData) {
        try {
            const result = await this.realtime.performDataOperation(async () => {
                // Simulação - implementar endpoint real se necessário
                return await api.request(`/salons/admin/${salonId}`, {
                    method: 'PUT',
                    body: JSON.stringify(updateData)
                });
            }, {
                refreshSalonId: salonId
            });

            if (result.success) {
                UI.showSuccess('Salão atualizado com sucesso!');
            }

        } catch (error) {
            UI.showError('Erro ao atualizar salão');
        }
    }
}

// ==========================================
// EXEMPLO 3: Integração com Agendamentos (Futuro)
// ==========================================

/**
 * Exemplo de como seria a integração com agendamentos
 * (quando houver endpoints admin para agendamentos)
 */
class AppointmentManager {
    constructor() {
        this.realtime = window.DashboardRealtime;
    }

    /**
     * Atualizar status de agendamento
     */
    async updateAppointmentStatus(appointmentId, newStatus) {
        try {
            const result = await this.realtime.performDataOperation(async () => {
                return await api.request(`/appointments/${appointmentId}/status`, {
                    method: 'PUT',
                    body: JSON.stringify({ status: newStatus })
                });
            }, {
                refresh: true // Refresh completo para atualizar estatísticas
            });

            if (result.success) {
                UI.showSuccess('Status do agendamento atualizado!');
            }

        } catch (error) {
            UI.showError('Erro ao atualizar agendamento');
        }
    }

    /**
     * Cancelar agendamento
     */
    async cancelAppointment(appointmentId) {
        try {
            const result = await this.realtime.performDataOperation(async () => {
                return await api.request(`/appointments/${appointmentId}`, {
                    method: 'DELETE'
                });
            }, {
                refresh: true
            });

            if (result.success) {
                UI.showSuccess('Agendamento cancelado!');
            }

        } catch (error) {
            UI.showError('Erro ao cancelar agendamento');
        }
    }
}

// ==========================================
// EXEMPLO 4: Funções de Utilitário Reutilizáveis
// ==========================================

/**
 * Funções utilitárias para atualização de elementos específicos
 */
class DashboardUtils {

    /**
     * Atualizar badge de status em qualquer lugar
     */
    static updateStatusBadge(elementId, status, textTrue = 'Ativo', textFalse = 'Inativo') {
        window.DashboardRealtime.updateStatusBadge(elementId, status, textTrue, textFalse);
    }

    /**
     * Atualizar contador numérico
     */
    static updateCounter(elementId, value, prefix = '', suffix = '') {
        window.DashboardRealtime.updateCounter(elementId, value, prefix, suffix);
    }

    /**
     * Formatar data para DD/MM/AAAA
     */
    static formatDate(date) {
        return window.DashboardRealtime.formatDate(date);
    }

    /**
     * Calcular dias restantes com cores
     */
    static calculateDaysRemaining(dueDate) {
        return window.DashboardRealtime.calculateDaysRemaining(dueDate);
    }

    /**
     * Mostrar loading em elemento específico
     */
    static showLoading(elementId, message = 'Carregando...') {
        window.DashboardRealtime.showLoading(elementId, message);
    }

    /**
     * Esconder loading
     */
    static hideLoading(elementId) {
        window.DashboardRealtime.hideLoading(elementId);
    }
}

// ==========================================
// EXEMPLO 5: Integração no dashboard-admin.html
// ==========================================

/**
 * Como integrar no dashboard-admin.html
 *
 * 1. Adicionar script na seção <head> ou antes do </body>:
 *    <script src="/frontend/services/dashboard-realtime.js"></script>
 *
 * 2. Modificar funções existentes para usar o sistema:
 */

// Exemplo de modificação da função handleSubscriptionSubmit
function handleSubscriptionSubmitModified(event) {
    event.preventDefault();

    const paymentStatus = document.getElementById('paymentStatus').value === 'true';
    const dueDate = document.getElementById('dueDate').value;

    if (!dueDate) {
        UI.showError('Data de vencimento é obrigatória');
        return;
    }

    // Usar o wrapper para operação com refresh automático
    window.DashboardRealtime.performDataOperation(async () => {
        return await api.request(`/salons/admin/${currentSalonId}/subscription`, {
            method: 'PUT',
            body: JSON.stringify({
                mensalidade_pago: paymentStatus,
                data_vencimento: dueDate
            })
        });
    }, {
        refreshSalonId: currentSalonId
    }).then(result => {
        if (result.success) {
            UI.showSuccess('Mensalidade atualizada com sucesso!');
            closeSubscriptionModal();
        } else {
            UI.showError(result.error || 'Erro ao atualizar mensalidade');
        }
    }).catch(error => {
        console.error('Erro ao atualizar mensalidade:', error);
        UI.showError('Erro ao atualizar mensalidade');
    });
}

// Exemplo de modificação da função handleSalonSubmit
function handleSalonSubmitModified(event) {
    event.preventDefault();

    const name = document.getElementById('salonName').value.trim();
    const email = document.getElementById('salonEmail').value.trim();

    if (!name) {
        UI.showError('Nome do salão é obrigatório');
        return;
    }

    window.DashboardRealtime.performDataOperation(async () => {
        return await api.request('/salons/admin/create', {
            method: 'POST',
            body: JSON.stringify({
                nome: name,
                email: email || undefined
            })
        });
    }, {
        refresh: true // Refresh completo após criar salão
    }).then(result => {
        if (result.success) {
            UI.showSuccess('Salão criado com sucesso!');
            closeSalonModal();
        } else {
            UI.showError(result.error || 'Erro ao criar salão');
        }
    }).catch(error => {
        console.error('Erro ao criar salão:', error);
        UI.showError('Erro ao criar salão');
    });
}

// ==========================================
// EXEMPLO 6: Criação de Novas Seções no Dashboard
// ==========================================

/**
 * Exemplo de como criar novas seções que se atualizam automaticamente
 */

// HTML para adicionar no dashboard-admin.html
const newSectionsHTML = `
<!-- Próximos Agendamentos -->
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Próximos Agendamentos</h3>
    </div>
    <div id="upcomingAppointments">
        <div class="loading">Carregando agendamentos...</div>
    </div>
</div>

<!-- Agendamentos Pendentes -->
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Agendamentos Pendentes</h3>
    </div>
    <div id="pendingAppointments">
        <div class="loading">Carregando agendamentos...</div>
    </div>
</div>

<!-- Histórico de Serviços -->
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Histórico de Serviços</h3>
    </div>
    <div id="serviceHistory">
        <div class="loading">Carregando histórico...</div>
    </div>
</div>
`;

// JavaScript para implementar essas seções
class ExtendedDashboardManager {
    constructor() {
        this.realtime = window.DashboardRealtime;
    }

    /**
     * Carregar agendamentos próximos
     */
    async loadUpcomingAppointments() {
        try {
            // Simulação - implementar endpoint real quando disponível
            const response = await api.request('/appointments/admin/upcoming');
            if (response.success) {
                this.updateUpcomingAppointments(response.appointments);
            }
        } catch (error) {
            console.error('Erro ao carregar próximos agendamentos:', error);
            document.getElementById('upcomingAppointments').innerHTML =
                '<p class="text-center">Erro ao carregar agendamentos</p>';
        }
    }

    /**
     * Atualizar lista de próximos agendamentos
     */
    updateUpcomingAppointments(appointments) {
        const container = document.getElementById('upcomingAppointments');

        if (!appointments || appointments.length === 0) {
            container.innerHTML = '<p class="text-center">Nenhum agendamento próximo.</p>';
            return;
        }

        let html = '<div class="table-responsive"><table class="table">';
        html += '<thead><tr><th>Data/Hora</th><th>Cliente</th><th>Serviço</th><th>Salão</th><th>Status</th></tr></thead>';
        html += '<tbody>';

        appointments.forEach(apt => {
            const dateTime = new Date(apt.data_hora).toLocaleString('pt-BR');
            const statusClass = this.getAppointmentStatusClass(apt.status);
            const statusText = this.getAppointmentStatusText(apt.status);

            html += `
                <tr>
                    <td>${dateTime}</td>
                    <td>${apt.cliente?.nome || 'N/A'}</td>
                    <td>${apt.servico?.nome || 'N/A'}</td>
                    <td>${apt.salon_nome || 'N/A'}</td>
                    <td><span class="badge ${statusClass}">${statusText}</span></td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
    }

    /**
     * Obter classe CSS para status de agendamento
     */
    getAppointmentStatusClass(status) {
        const classes = {
            'agendado': 'badge-info',
            'confirmado': 'badge-success',
            'concluido': 'badge-success',
            'cancelado': 'badge-danger',
            'nao_compareceu': 'badge-warning'
        };
        return classes[status] || 'badge-secondary';
    }

    /**
     * Obter texto para status de agendamento
     */
    getAppointmentStatusText(status) {
        const texts = {
            'agendado': 'Agendado',
            'confirmado': 'Confirmado',
            'concluido': 'Concluído',
            'cancelado': 'Cancelado',
            'nao_compareceu': 'Não Compareceu'
        };
        return texts[status] || status;
    }

    /**
     * Carregar agendamentos pendentes
     */
    async loadPendingAppointments() {
        try {
            const response = await api.request('/appointments/admin/pending');
            if (response.success) {
                this.updatePendingAppointments(response.appointments);
            }
        } catch (error) {
            console.error('Erro ao carregar agendamentos pendentes:', error);
            document.getElementById('pendingAppointments').innerHTML =
                '<p class="text-center">Erro ao carregar agendamentos</p>';
        }
    }

    /**
     * Atualizar lista de agendamentos pendentes
     */
    updatePendingAppointments(appointments) {
        const container = document.getElementById('pendingAppointments');

        if (!appointments || appointments.length === 0) {
            container.innerHTML = '<p class="text-center">Nenhum agendamento pendente.</p>';
            return;
        }

        let html = '<div class="table-responsive"><table class="table">';
        html += '<thead><tr><th>Data/Hora</th><th>Cliente</th><th>Serviço</th><th>Salão</th><th>Ações</th></tr></thead>';
        html += '<tbody>';

        appointments.forEach(apt => {
            const dateTime = new Date(apt.data_hora).toLocaleString('pt-BR');

            html += `
                <tr>
                    <td>${dateTime}</td>
                    <td>${apt.cliente?.nome || 'N/A'}</td>
                    <td>${apt.servico?.nome || 'N/A'}</td>
                    <td>${apt.salon_nome || 'N/A'}</td>
                    <td>
                        <button class="btn btn-sm btn-success" onclick="confirmAppointment(${apt.id})">
                            Confirmar
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="cancelAppointment(${apt.id})">
                            Cancelar
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
    }
}

// ==========================================
// EXEMPLO 7: Configuração de Interceptadores Personalizados
// ==========================================

/**
 * Como configurar interceptadores personalizados para APIs específicas
 */

// Se sua API service tiver interceptadores
if (typeof api.addResponseInterceptor === 'function') {
    api.addResponseInterceptor((response) => {
        // Interceptar respostas específicas
        if (response.url?.includes('/salons/admin/')) {
            console.log('[INTERCEPTOR] Operação admin detectada');
            // Trigger refresh após operações admin
            setTimeout(() => {
                window.DashboardRealtime.refreshDashboard();
            }, 300);
        }

        return response;
    });
}

// Para APIs que não têm interceptadores nativos
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const result = await originalFetch.apply(this, args);

    // Interceptar chamadas específicas
    const url = args[0];
    if (typeof url === 'string' && url.includes('/salons/admin/')) {
        // Clonar response para não consumir o stream
        const clonedResponse = result.clone();

        // Verificar se foi uma operação de escrita
        if (args[1]?.method && ['POST', 'PUT', 'DELETE'].includes(args[1].method)) {
            setTimeout(() => {
                window.DashboardRealtime.refreshDashboard();
            }, 300);
        }
    }

    return result;
};

// Exportar classes para uso global
window.SubscriptionManager = SubscriptionManager;
window.SalonManager = SalonManager;
window.AppointmentManager = AppointmentManager;
window.DashboardUtils = DashboardUtils;
window.ExtendedDashboardManager = ExtendedDashboardManager;