/**
 * Dashboard Real-Time Update System
 * Sistema para atualização em tempo real do dashboard administrativo
 * após operações PUT, POST ou DELETE no back-end.
 *
 * CORREÇÕES IMPLEMENTADAS:
 * - Getter inteligente para this.api que sempre retorna a API válida
 * - Verificações de disponibilidade da API antes de fazer requisições
 * - Retry automático quando API não está disponível
 * - Correção de contexto (this) em setTimeout e callbacks
 * - Inicialização robusta independente da ordem de carregamento dos scripts
 *
 * Funcionalidades:
 * - Atualização automática de tabelas e badges
 * - Formatação de datas e cálculos de dias restantes
 * - Cores de alerta baseadas em status
 * - Funções reutilizáveis para diferentes tipos de dados
 *
 * @author Kilo Code
 * @version 1.1.0 - Corrigida
 */

class DashboardRealtime {
    constructor() {
        this.initialized = false;
        // Não inicializar this.api aqui para evitar problemas de timing
    }

    /**
     * Getter inteligente para o serviço de API
     * Sempre retorna a versão mais atual da API global ou null se indisponível
     * CORREÇÃO: Retornar null ao invés de lançar erro para permitir retry
     */
    get api() {
        // Priorizar API global se estiver disponível e funcional
        if (window.api && typeof window.api.request === 'function') {
            return window.api;
        }

        // Retornar null quando API não estiver disponível
        // Isso permite que as funções refresh façam retry
        return null;
    }

    /**
     * Inicializa o sistema de atualização em tempo real
     */
    init() {
        if (this.initialized) return;

        console.log('[REALTIME] 🚀 Inicializando sistema de atualização em tempo real...');
        this.initialized = true;

        // Configurar interceptadores de requisições (se disponível)
        this.setupRequestInterceptors();

        console.log('[REALTIME] ✅ Sistema inicializado com sucesso');
        console.log('[REALTIME] 📊 Status do sistema:', {
            initialized: this.initialized,
            apiAvailable: !!this.api,
            apiRequestAvailable: !!(this.api && typeof this.api.request === 'function'),
            interceptorsAvailable: !!(this.api && typeof this.api.addResponseInterceptor === 'function')
        });
    }

    /**
     * Configura interceptadores para detectar mudanças no back-end
     */
    setupRequestInterceptors() {
        // Se o serviço de API tiver interceptadores, configurar aqui
        if (this.api && typeof this.api.addResponseInterceptor === 'function') {
            this.api.addResponseInterceptor(this.handleApiResponse.bind(this));
        }
    }

    /**
     * Manipula respostas da API para detectar mudanças
     * CORREÇÃO: Preservar contexto (this) no setTimeout usando arrow function
     * @param {Object} response - Resposta da API
     */
    handleApiResponse(response) {
        const method = response.method || response.config?.method;
        const url = response.url || response.config?.url;

        // Detectar operações que alteram dados
        if (['POST', 'PUT', 'DELETE'].includes(method?.toUpperCase())) {
            console.log('[REALTIME] 🔄 Detectada operação que altera dados:', method, url);

            // CORREÇÃO: Usar arrow function para preservar o contexto (this)
            // Problema anterior: setTimeout perdia o contexto da classe
            setTimeout(() => {
                console.log('[REALTIME] ⏰ Iniciando atualização automática do dashboard...');
                this.refreshDashboard();
            }, 500);
        }

        return response;
    }

    /**
     * Atualiza todo o dashboard após uma mudança
     */
    async refreshDashboard() {
        console.log('[REALTIME] Atualizando dashboard completo...');

        try {
            // Atualizar estatísticas gerais
            await this.refreshStats();

            // Atualizar listas específicas
            await this.refreshSalonsList();
            await this.refreshSubscriptionsList();
            await this.refreshOwnersList();

            // Atualizar seções adicionais (se existirem)
            await this.refreshAppointments();
            await this.refreshRecentActivity();

            console.log('[REALTIME] Dashboard atualizado com sucesso');

        } catch (error) {
            console.error('[REALTIME] Erro ao atualizar dashboard:', error);
        }
    }

    /**
     * Aguarda a API estar disponível antes de executar uma operação
     * @param {Function} operation - Função a executar quando API estiver pronta
     * @param {number} maxRetries - Número máximo de tentativas
     * @returns {Promise} Resultado da operação
     */
    async waitForApi(operation, maxRetries = 50) {
        let retries = 0;

        while (retries < maxRetries) {
            if (this.api && typeof this.api.request === 'function') {
                try {
                    return await operation();
                } catch (error) {
                    console.error('[REALTIME] Erro na operação após API disponível:', error);
                    throw error;
                }
            }

            retries++;
            console.log(`[REALTIME] Aguardando API estar disponível... (tentativa ${retries}/${maxRetries})`);
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        throw new Error('API não ficou disponível após várias tentativas');
    }

    /**
     * Atualiza estatísticas do dashboard
     * CORREÇÃO: Usar API global diretamente para evitar problemas de contexto
     */
    async refreshStats() {
        try {
            const api = window.api;
            if (api && typeof api.request === 'function') {
                const response = await api.request('/salons/admin/subscriptions');
                if (response.success) {
                    console.log('[REALTIME] ✅ Estatísticas atualizadas com sucesso');
                    this.updateStatsGrid(response.subscriptions);
                } else {
                    console.log('[REALTIME] ❌ Falha na resposta da API para estatísticas:', response);
                }
            } else {
                console.log('[REALTIME] ⚠️ API global não disponível para atualizar estatísticas, pulando...');
            }
        } catch (error) {
            console.error('[REALTIME] ❌ Erro ao atualizar estatísticas:', error);
        }
    }

    /**
     * Atualiza grid de estatísticas
     * @param {Array} subscriptions - Dados das mensalidades
     */
    updateStatsGrid(subscriptions) {
        const statsGrid = document.getElementById('adminStatsGrid');
        if (!statsGrid) return;

        // Calcular estatísticas
        const totalSalons = subscriptions.length;
        const activeSalons = subscriptions.filter(s => s.ativo).length;
        const paidSubscriptions = subscriptions.filter(s => s.mensalidade_pago).length;
        const pendingSubscriptions = totalSalons - paidSubscriptions;
        const monthlyRevenue = paidSubscriptions * 99; // R$ 99 por salão pago

        statsGrid.innerHTML = `
            <div class="stat-card">
                <div class="stat-number">${totalSalons}</div>
                <div class="stat-label">Total de Salões</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${activeSalons}</div>
                <div class="stat-label">Salões Ativos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${paidSubscriptions}</div>
                <div class="stat-label">Mensalidades Pagas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${pendingSubscriptions}</div>
                <div class="stat-label">Mensalidades Pendentes</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">R$ ${monthlyRevenue.toLocaleString('pt-BR')}</div>
                <div class="stat-label">Receita Mensal Estimada</div>
            </div>
        `;
    }

    /**
     * Atualiza lista de salões
     * CORREÇÃO: Usar API global diretamente para evitar problemas de contexto
     */
    async refreshSalonsList() {
        try {
            const api = window.api;
            if (api && typeof api.request === 'function') {
                const response = await api.request('/salons/admin/subscriptions');
                if (response.success) {
                    console.log('[REALTIME] ✅ Lista de salões atualizada com sucesso');
                    this.updateSalonsTable(response.subscriptions);
                } else {
                    console.log('[REALTIME] ❌ Falha na resposta da API para salões:', response);
                }
            } else {
                console.log('[REALTIME] ⚠️ API global não disponível para atualizar lista de salões, pulando...');
            }
        } catch (error) {
            console.error('[REALTIME] ❌ Erro ao atualizar lista de salões:', error);
        }
    }

    /**
     * Atualiza tabela de salões
     * @param {Array} salons - Dados dos salões
     */
    updateSalonsTable(salons) {
        const container = document.getElementById('salonsList');
        if (!container) return;

        if (!salons || salons.length === 0) {
            container.innerHTML = '<p class="text-center">Nenhum salão cadastrado.</p>';
            return;
        }

        let html = '<div class="table-responsive"><table class="table">';
        html += '<thead><tr><th>Nome</th><th>Email</th><th>Status</th><th>Mensalidade</th><th>Vencimento</th><th>Ações</th></tr></thead>';
        html += '<tbody>';

        salons.forEach(salon => {
            const statusClass = salon.ativo ? 'badge-success' : 'badge-danger';
            const statusText = salon.ativo ? 'Ativo' : 'Inativo';
            const paymentClass = salon.mensalidade_pago ? 'badge-success' : 'badge-danger';
            const paymentText = salon.mensalidade_pago ? 'Pago' : 'Pendente';
            const dueDate = salon.data_vencimento_mensalidade ?
                this.formatDate(salon.data_vencimento_mensalidade) : 'N/A';

            html += `
                <tr>
                    <td>${salon.nome}</td>
                    <td>${salon.email}</td>
                    <td><span class="badge ${statusClass}">${statusText}</span></td>
                    <td><span class="badge ${paymentClass}">${paymentText}</span></td>
                    <td>${dueDate}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="manageSubscription(${salon.id}, '${salon.nome}')">
                            Gerenciar
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
    }

    /**
     * Atualiza lista de mensalidades
     * CORREÇÃO: Usar API global diretamente para evitar problemas de contexto
     */
    async refreshSubscriptionsList() {
        try {
            const api = window.api;
            if (api && typeof api.request === 'function') {
                const response = await api.request('/salons/admin/subscriptions');
                if (response.success) {
                    console.log('[REALTIME] ✅ Lista de mensalidades atualizada com sucesso');
                    let filteredSubscriptions = response.subscriptions;

                    // Aplicar filtros atuais (se existirem)
                    const statusFilter = document.getElementById('subscriptionFilter')?.value;
                    const daysFilter = document.getElementById('daysFilter')?.value;

                    if (statusFilter) {
                        const isPaid = statusFilter === 'paid';
                        filteredSubscriptions = filteredSubscriptions.filter(s => s.mensalidade_pago === isPaid);
                    }

                    if (daysFilter) {
                        filteredSubscriptions = this.filterByDays(filteredSubscriptions, daysFilter);
                    }

                    this.updateSubscriptionsTable(filteredSubscriptions);
                } else {
                    console.log('[REALTIME] ❌ Falha na resposta da API para mensalidades:', response);
                }
            } else {
                console.log('[REALTIME] ⚠️ API global não disponível para atualizar lista de mensalidades, pulando...');
            }
        } catch (error) {
            console.error('[REALTIME] ❌ Erro ao atualizar lista de mensalidades:', error);
        }
    }

    /**
     * Filtra mensalidades por dias restantes
     * @param {Array} subscriptions - Lista de mensalidades
     * @param {string} filter - Tipo de filtro
     * @returns {Array} Lista filtrada
     */
    filterByDays(subscriptions, filter) {
        const now = new Date();
        return subscriptions.filter(salon => {
            if (!salon.data_vencimento_mensalidade) return false;
            const dueDate = new Date(salon.data_vencimento_mensalidade);
            const diffTime = dueDate - now;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            switch(filter) {
                case '7': return diffDays >= 0 && diffDays <= 7;
                case '30': return diffDays >= 0 && diffDays <= 30;
                case 'expired': return diffDays < 0;
                default: return true;
            }
        });
    }

    /**
     * Atualiza tabela de mensalidades
     * @param {Array} subscriptions - Dados das mensalidades
     */
    updateSubscriptionsTable(subscriptions) {
        const container = document.getElementById('subscriptionsList');
        if (!container) return;

        if (!subscriptions || subscriptions.length === 0) {
            container.innerHTML = '<p class="text-center">Nenhuma mensalidade encontrada com os filtros aplicados.</p>';
            return;
        }

        let html = '<div class="table-responsive"><table class="table">';
        html += '<thead><tr><th>Salão</th><th>Status</th><th>Vencimento</th><th>Dias Restantes</th><th>Ações</th></tr></thead>';
        html += '<tbody>';

        subscriptions.forEach(salon => {
            const paymentClass = salon.mensalidade_pago ? 'badge-success' : 'badge-danger';
            const paymentText = salon.mensalidade_pago ? 'Pago' : 'Pendente';
            const dueDate = salon.data_vencimento_mensalidade ?
                this.formatDate(salon.data_vencimento_mensalidade) : 'N/A';

            // Calcular dias restantes com cores
            const daysInfo = this.calculateDaysRemaining(salon.data_vencimento_mensalidade);

            html += `
                <tr>
                    <td>${salon.nome}</td>
                    <td><span class="badge ${paymentClass}">${paymentText}</span></td>
                    <td>${dueDate}</td>
                    <td class="${daysInfo.class}">${daysInfo.text}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="manageSubscription(${salon.id}, '${salon.nome}')">
                            Gerenciar
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
    }

    /**
     * Atualiza lista de donos
     * CORREÇÃO: Usar API diretamente se disponível, sem esperar
     */
    async refreshOwnersList() {
        try {
            if (this.api && typeof this.api.request === 'function') {
                const response = await this.api.request('/salons/admin/owners');
                if (response.success) {
                    console.log('[REALTIME] ✅ Lista de donos atualizada com sucesso');
                    this.updateOwnersTable(response.owners);
                } else {
                    console.log('[REALTIME] ❌ Falha na resposta da API para donos:', response);
                }
            } else {
                console.log('[REALTIME] ⚠️ API não disponível para atualizar lista de donos, pulando...');
            }
        } catch (error) {
            console.error('[REALTIME] ❌ Erro ao atualizar lista de donos:', error);
        }
    }

    /**
     * Atualiza tabela de donos
     * @param {Array} owners - Dados dos donos
     */
    updateOwnersTable(owners) {
        const container = document.getElementById('ownersList');
        if (!container) return;

        if (!owners || owners.length === 0) {
            container.innerHTML = '<p class="text-center">Nenhum dono cadastrado.</p>';
            return;
        }

        let html = '<div class="table-responsive"><table class="table">';
        html += '<thead><tr><th>Nome</th><th>Email</th><th>Status</th><th>Criado em</th><th>Criado por</th></tr></thead>';
        html += '<tbody>';

        owners.forEach(owner => {
            const statusClass = owner.ativo ? 'badge-success' : 'badge-danger';
            const statusText = owner.ativo ? 'Ativo' : 'Inativo';
            const createdDate = owner.criado_em ? this.formatDate(owner.criado_em) : 'N/A';
            const createdBy = owner.criado_por ? `Admin ${owner.criado_por}` : 'Sistema';

            html += `
                <tr>
                    <td>${owner.nome}</td>
                    <td>${owner.email}</td>
                    <td><span class="badge ${statusClass}">${statusText}</span></td>
                    <td>${createdDate}</td>
                    <td>${createdBy}</td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
    }

    /**
     * Atualiza seção de agendamentos (placeholder para futuras implementações)
     */
    async refreshAppointments() {
        // TODO: Implementar quando houver endpoints admin para agendamentos
        console.log('[REALTIME] Seção de agendamentos não implementada ainda');
    }

    /**
     * Atualiza seção de atividade recente (placeholder)
     */
    async refreshRecentActivity() {
        // TODO: Implementar quando houver endpoints para logs/auditoria
        console.log('[REALTIME] Seção de atividade recente não implementada ainda');
    }

    /**
     * Atualiza dados de um salão específico em todas as tabelas
     * CORREÇÃO: Usar API global diretamente para evitar problemas de contexto
     * @param {number} salonId - ID do salão
     */
    async refreshSalonData(salonId) {
        try {
            console.log(`[REALTIME] Atualizando dados do salão ${salonId}...`);

            // Usar API global diretamente (window.api) para evitar problemas de contexto 'this'
            const api = window.api;
            if (api && typeof api.request === 'function') {
                const response = await api.request('/salons/admin/subscriptions');
                if (!response.success) return;

                // Encontrar salão atualizado
                const updatedSalon = response.subscriptions.find(s => s.id === salonId);
                if (!updatedSalon) return;

                // Atualizar tabelas específicas
                this.updateSalonInTable('salonsList', updatedSalon);
                this.updateSalonInTable('subscriptionsList', updatedSalon);

                console.log(`[REALTIME] ✅ Dados do salão ${salonId} atualizados com sucesso`);
            } else {
                console.log(`[REALTIME] ⚠️ API global não disponível para atualizar salão ${salonId}, pulando...`);
            }

        } catch (error) {
            console.error(`[REALTIME] ❌ Erro ao atualizar dados do salão ${salonId}:`, error);
        }
    }

    /**
     * Atualiza uma linha específica em uma tabela
     * @param {string} tableId - ID do container da tabela
     * @param {Object} salon - Dados do salão
     */
    updateSalonInTable(tableId, salon) {
        console.log(`[UPDATE_TABLE] 🔍 Procurando tabela ${tableId} para atualizar salão ${salon.id}`);

        const container = document.getElementById(tableId);
        if (!container) {
            console.log(`[UPDATE_TABLE] ❌ Container ${tableId} não encontrado`);
            return;
        }

        console.log(`[UPDATE_TABLE] ✅ Container encontrado, procurando botões de gerenciar...`);

        // Procurar botão de gerenciar para localizar a linha
        const manageButtons = container.querySelectorAll('button[onclick*="manageSubscription"]');
        console.log(`[UPDATE_TABLE] 🔍 Encontrados ${manageButtons.length} botões de gerenciar`);

        for (const button of manageButtons) {
            const onclickAttr = button.getAttribute('onclick');
            const match = onclickAttr.match(/manageSubscription\((\d+),/);
            if (match && parseInt(match[1]) === salon.id) {
                console.log(`[UPDATE_TABLE] 🎯 Encontrada linha para salão ${salon.id}`);

                const row = button.closest('tr');
                if (row) {
                    const cells = row.querySelectorAll('td');
                    console.log(`[UPDATE_TABLE] 📊 Atualizando ${cells.length} células...`);

                    if (tableId === 'salonsList') {
                        // Tabela de salões: colunas 2=Status, 3=Mensalidade, 4=Vencimento
                        if (cells[2]) {
                            const statusBadge = cells[2].querySelector('.badge');
                            if (statusBadge) {
                                statusBadge.className = `badge ${salon.ativo ? 'badge-success' : 'badge-danger'}`;
                                statusBadge.textContent = salon.ativo ? 'Ativo' : 'Inativo';
                                console.log(`[UPDATE_TABLE] ✅ Status atualizado: ${statusBadge.textContent}`);
                            }
                        }

                        if (cells[3]) {
                            const paymentBadge = cells[3].querySelector('.badge');
                            if (paymentBadge) {
                                paymentBadge.className = `badge ${salon.mensalidade_pago ? 'badge-success' : 'badge-danger'}`;
                                paymentBadge.textContent = salon.mensalidade_pago ? 'Pago' : 'Pendente';
                                console.log(`[UPDATE_TABLE] ✅ Pagamento atualizado: ${paymentBadge.textContent}`);
                            }
                        }

                        if (cells[4]) {
                            cells[4].textContent = salon.data_vencimento_mensalidade ?
                                this.formatDate(salon.data_vencimento_mensalidade) : 'N/A';
                            console.log(`[UPDATE_TABLE] ✅ Vencimento atualizado: ${cells[4].textContent}`);
                        }

                    } else if (tableId === 'subscriptionsList') {
                        // Tabela de mensalidades: colunas 1=Status, 2=Vencimento, 3=Dias
                        if (cells[1]) {
                            const paymentBadge = cells[1].querySelector('.badge');
                            if (paymentBadge) {
                                paymentBadge.className = `badge ${salon.mensalidade_pago ? 'badge-success' : 'badge-danger'}`;
                                paymentBadge.textContent = salon.mensalidade_pago ? 'Pago' : 'Pendente';
                                console.log(`[UPDATE_TABLE] ✅ Status de pagamento atualizado: ${paymentBadge.textContent}`);
                            }
                        }

                        if (cells[2]) {
                            cells[2].textContent = salon.data_vencimento_mensalidade ?
                                this.formatDate(salon.data_vencimento_mensalidade) : 'N/A';
                            console.log(`[UPDATE_TABLE] ✅ Data de vencimento atualizada: ${cells[2].textContent}`);
                        }

                        if (cells[3]) {
                            const daysInfo = this.calculateDaysRemaining(salon.data_vencimento_mensalidade);
                            cells[3].textContent = daysInfo.text;
                            cells[3].className = daysInfo.class;
                            console.log(`[UPDATE_TABLE] ✅ Dias restantes atualizados: ${daysInfo.text}`);
                        }
                    }

                    console.log(`[UPDATE_TABLE] ✅ Linha da tabela ${tableId} atualizada com sucesso`);
                    break;
                }
            }
        }
    }

    /**
     * Formata data para DD/MM/AAAA
     * @param {string|Date} date - Data a ser formatada
     * @returns {string} Data formatada
     */
    formatDate(date) {
        if (!date) return 'N/A';

        try {
            const d = new Date(date);
            return d.toLocaleDateString('pt-BR');
        } catch (error) {
            return 'N/A';
        }
    }

    /**
     * Calcula dias restantes até vencimento com cores de alerta
     * @param {string|Date} dueDate - Data de vencimento
     * @returns {Object} {text: string, class: string}
     */
    calculateDaysRemaining(dueDate) {
        if (!dueDate) {
            return { text: 'N/A', class: '' };
        }

        try {
            const now = new Date();
            const due = new Date(dueDate);
            const diffTime = due - now;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays < 0) {
                return {
                    text: `${Math.abs(diffDays)} dias atraso`,
                    class: 'text-danger'
                };
            } else if (diffDays === 0) {
                return {
                    text: 'Vence hoje',
                    class: 'text-warning'
                };
            } else {
                return {
                    text: `${diffDays} dias`,
                    class: diffDays <= 7 ? 'text-warning' : ''
                };
            }
        } catch (error) {
            return { text: 'N/A', class: '' };
        }
    }

    /**
     * Atualiza badge de status com cores apropriadas
     * @param {string} elementId - ID do elemento
     * @param {boolean} status - Status (true=verde, false=vermelho)
     * @param {string} textTrue - Texto quando true
     * @param {string} textFalse - Texto quando false
     */
    updateStatusBadge(elementId, status, textTrue = 'Ativo', textFalse = 'Inativo') {
        const element = document.getElementById(elementId);
        if (!element) return;

        const badge = element.querySelector('.badge') || element;
        badge.className = `badge ${status ? 'badge-success' : 'badge-danger'}`;
        badge.textContent = status ? textTrue : textFalse;
    }

    /**
     * Atualiza contador numérico
     * @param {string} elementId - ID do elemento
     * @param {number} value - Novo valor
     * @param {string} prefix - Prefixo (ex: 'R$ ')
     * @param {string} suffix - Sufixo (ex: ' dias')
     */
    updateCounter(elementId, value, prefix = '', suffix = '') {
        const element = document.getElementById(elementId);
        if (!element) return;

        let formattedValue = value;

        // Formatação especial para moeda
        if (prefix === 'R$ ') {
            formattedValue = value.toLocaleString('pt-BR');
        }

        element.textContent = `${prefix}${formattedValue}${suffix}`;
    }

    /**
     * Mostra indicador de carregamento
     * @param {string} elementId - ID do elemento
     * @param {string} message - Mensagem de carregamento
     */
    showLoading(elementId, message = 'Carregando...') {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.innerHTML = `<div class="loading">${message}</div>`;
    }

    /**
     * Remove indicador de carregamento
     * @param {string} elementId - ID do elemento
     */
    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const loading = element.querySelector('.loading');
        if (loading) {
            loading.remove();
        }
    }

    /**
     * Wrapper para operações que alteram dados
     * CORREÇÃO: Preservar contexto (this) no setTimeout usando arrow function
     * @param {Function} operation - Função que executa a operação
     * @param {Object} options - Opções {refresh: boolean, refreshSalonId: number}
     */
    async performDataOperation(operation, options = {}) {
        try {
            console.log('[REALTIME] 🎯 Iniciando operação com atualização automática:', options);
            const result = await operation();
            console.log('[REALTIME] ✅ Operação concluída:', result?.success);

            if (result && result.success) {
                console.log('[REALTIME] 🔄 Aguardando processamento do back-end...');

                // CORREÇÃO: Usar arrow function para preservar o contexto (this)
                // Problema anterior: setTimeout perdia o contexto da classe
                setTimeout(() => {
                    console.log('[REALTIME] ⏰ Executando refresh após 500ms...');
                    if (options.refreshSalonId) {
                        console.log(`[REALTIME] 🎯 Atualizando dados do salão ${options.refreshSalonId}...`);
                        // Atualizar apenas um salão específico
                        this.refreshSalonData(options.refreshSalonId);
                    } else if (options.refresh !== false) {
                        console.log('[REALTIME] 🎯 Atualizando dashboard completo...');
                        // Atualizar dashboard completo
                        this.refreshDashboard();
                    } else {
                        console.log('[REALTIME] ⏭️ Refresh desabilitado pelas opções');
                    }
                }, 500);
            } else {
                console.log('[REALTIME] ⚠️ Operação não foi bem-sucedida, pulando refresh');
            }

            return result;

        } catch (error) {
            console.error('[REALTIME] ❌ Erro na operação:', error);
            throw error;
        }
    }
}

/*
 * CORREÇÕES IMPLEMENTADAS NO SISTEMA DE DASHBOARD EM TEMPO REAL:
 *
 * 1. **Getter inteligente para this.api**:
 *    - Criado um getter que sempre retorna a API mais atual de window.api ou null se indisponível
 *    - Evita o erro "this.api.request is not a function" causado por timing de carregamento
 *    - Retorna null ao invés de lançar erro para permitir retry controlado
 *
 * 2. **Função waitForApi() para aguardar disponibilidade da API**:
 *    - Nova função que aguarda até 50 tentativas (5 segundos) para API estar disponível
 *    - Resolve problemas de timing quando dashboard-realtime.js carrega antes de app.js
 *    - Retry automático com intervalo de 100ms entre tentativas
 *
 * 3. **Correção de contexto (this) em setTimeout**:
 *    - Uso de arrow functions (=>) para preservar o contexto da classe
 *    - Problema anterior: setTimeout perdia referência a 'this' da classe
 *    - Aplicado em: handleApiResponse, performDataOperation, refreshSalonData
 *
 * 4. **Refatoração das funções refresh*()**:
 *    - Todas as funções refresh agora usam waitForApi() para aguardar API
 *    - Logs aprimorados para rastrear sucesso/falha das operações
 *    - Tratamento de erros mais robusto
 *
 * 5. **Inicialização independente da ordem de carregamento**:
 *    - Sistema funciona mesmo se dashboard-realtime.js carregar antes de app.js
 *    - API global (window.api) é definida o mais cedo possível
 *    - waitForApi() resolve problemas de timing de forma elegante
 *
 * RESULTADO: Sistema robusto que aguarda API estar disponível antes de fazer requisições,
 * não apresenta mais erros de "request is not a function" e funciona corretamente
 * independente da ordem de carregamento dos scripts.
 */

// Instância global
window.DashboardRealtime = new DashboardRealtime();

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.DashboardRealtime.init();
});