/**
 * Cliente da API - Classe principal para comunicação com o backend
 * Centraliza todas as chamadas HTTP e tratamento de erros
 */

// CORREÇÃO: Definir API global o mais cedo possível para compatibilidade com outros módulos
// Isso evita erros "this.api.request is not a function" em módulos que carregam antes do app.js
let api; // Declarar globalmente

// CORREÇÃO: Expor API globalmente imediatamente (fallback vazio)
// Permite que outros scripts usem window.api mesmo antes da API real ser inicializada
window.api = window.api || {};
class APIClient {
    constructor() {
        this.baseURL = API_CONFIG.BASE_URL;  // URL base da API (definida em config.js)
    }

    /**
     * Método genérico para fazer requisições HTTP
     * Trata autenticação, CORS e erros automaticamente
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const token = TokenManager.get();  // Usar TokenManager em vez de localStorage diretamente

        // Configuração padrão da requisição
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'  // Especificar que esperamos JSON
            },
            ...options  // Sobrescreve opções específicas (method, body, etc.)
        };

        // Só inclui Authorization se houver token válido
        if (token && TokenManager.isValid()) {
            config.headers['Authorization'] = `Bearer ${token}`;
            console.log(`[API] Incluindo Authorization header para ${endpoint}`);
        } else if (token && !TokenManager.isValid()) {
            console.warn('[API] Token inválido detectado, removendo...');
            TokenManager.remove();
        }

        try {
            console.log(`[API] Fazendo requisição: ${config.method || 'GET'} ${url}`);
            const response = await fetch(url, config);

            // Tratamento especial para erros de autenticação
            if (response.status === 401) {
                console.warn('[API] Token rejeitado pelo servidor (401)');
                TokenManager.remove();  // Remove token inválido
                // Não redirecionar automaticamente aqui, deixar o código chamador decidir
                throw new Error('Sessão expirada. Faça login novamente.');
            }

            // Tratamento para erro 422 (Unprocessable Entity)
            if (response.status === 422) {
                console.warn('[API] Erro de validação (422)');
                let errorData;
                try {
                    errorData = await response.json();
                    const errorMessage = errorData.detail || errorData.message || 'Dados inválidos enviados';
                    throw new Error(`Erro de validação: ${errorMessage}`);
                } catch (jsonError) {
                    throw new Error('Erro de validação nos dados enviados');
                }
            }

            let data;
            const contentType = response.headers.get('content-type');

            try {
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();  // Parse como JSON
                } else {
                    // Se não é JSON, tentar ler como texto
                    const textData = await response.text();
                    data = { message: textData };
                }
            } catch (jsonError) {
                console.warn('[API] Erro no parse da resposta:', jsonError);
                // Se falhar o parse, criar resposta padrão baseada no status
                data = {
                    success: false,
                    error: response.ok ? 'Resposta do servidor malformada' : `Erro HTTP ${response.status}`
                };
            }

            // Verifica se a resposta HTTP foi bem-sucedida
            if (!response.ok) {
                console.error(`[API] Erro HTTP ${response.status}:`, data);

                // Se erro estruturado (nosso formato), usa a mensagem do backend
                if (data.success === false) {
                    throw new Error(data.error || `Erro HTTP ${response.status}`);
                } else if (data.detail) {
                    // Erro de validação Pydantic
                    throw new Error(data.detail);
                } else if (data.message) {
                    // Outros erros estruturados
                    throw new Error(data.message);
                } else {
                    // Erro genérico
                    throw new Error(`Erro do servidor (${response.status})`);
                }
            }

            console.log(`[API] Resposta bem-sucedida para ${endpoint}`);
            return data;  // Retorna dados da resposta bem-sucedida

        } catch (error) {
            console.error('[API] Erro na requisição:', error);

            // Se é um erro de rede ou fetch, criar mensagem amigável
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Erro de conexão. Verifique sua internet.');
            }

            // Garante que sempre lança um Error object
            if (error instanceof Error) {
                throw error;  // Relança erro já tratado
            } else {
                throw new Error('Erro desconhecido na comunicação com o servidor');
            }
        }
    }

    // ============ MÉTODOS DE AUTENTICAÇÃO ============

    /**
     * Faz login de usuário (dono ou cliente)
     * @param {string} email - Email do usuário
     * @param {string} password - Senha do usuário
     * @param {boolean} isOwner - Se é dono do salão (true) ou cliente (false)
     * @returns {Promise<Object>} Dados do login com tokens
     */
    async login(email, password, isOwner = false) {
        const endpoint = isOwner ? API_CONFIG.ENDPOINTS.LOGIN : API_CONFIG.ENDPOINTS.CLIENT_LOGIN;
        const response = await this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify({ email, senha: password })  // Campo senha no backend é 'senha'
        });

        // Armazena token JWT automaticamente se login foi bem-sucedido
        if (response.access_token) {
            TokenManager.set(response.access_token);
        }

        return response;
    }

    /**
     * Faz login específico de cliente
     * @param {string} email - Email do cliente
     * @param {string} password - Senha do cliente
     * @returns {Promise<Object>} Dados do login com tokens
     */
    async loginCliente(email, password) {
        try {
            const response = await this.login(email, password, false); // false = cliente

            // Validações adicionais para cliente
            if (!response.access_token) {
                throw new Error('Token de acesso não recebido do servidor');
            }

            if (response.role !== 'cliente') {
                throw new Error('Resposta inválida - role incorreta');
            }

            // Armazenamento já feito no método login()
            return response;
        } catch (error) {
            console.error('Erro no login do cliente:', error);
            throw error; // Relança para tratamento no frontend
        }
    }

    /**
     * Registra novo usuário (dono ou cliente)
     * @param {Object} userData - Dados do usuário a ser cadastrado
     * @param {boolean} isOwner - Se é dono do salão ou cliente
     * @returns {Promise<Object>} Dados do registro com tokens
     */
    async register(userData, isOwner = false) {
        const endpoint = isOwner ? API_CONFIG.ENDPOINTS.REGISTER : API_CONFIG.ENDPOINTS.CLIENT_REGISTER;

        // Dados específicos para dono de salão
        if (isOwner) {
            const ownerData = {
                nome: userData.name,
                email: userData.email,
                senha: userData.password,
                ativo: true,      // Donos sempre começam ativos
                admin: true       // Donos têm privilégios de admin
            };
            return this.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(ownerData)
            });
        }

        // Dados para cliente
        const clientData = {
            nome: userData.name,
            email: userData.email,
            telefone: userData.phone,
            senha: userData.password,
            salon_id: userData.salon_id || 1  // ID do salão (padrão 1 para desenvolvimento)
        };

        const response = await this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(clientData)
        });

        // Validações adicionais da resposta
        if (response.success === false) {
            throw new Error(response.error || 'Erro no cadastro');
        }

        // Confirma que o cadastro foi bem-sucedido
        if (!response.client_id) {
            throw new Error('Resposta inválida do servidor - client_id ausente');
        }

        // Armazena token se registro foi bem-sucedido
        if (response.access_token) {
            TokenManager.set(response.access_token);
        }

        return response;
    }

    /**
     * Faz logout do usuário atual
     * Remove token, dados do salão e redireciona para página inicial
     */
    async logout() {
        try {
            // Tenta fazer logout no servidor (opcional)
            await this.request(API_CONFIG.ENDPOINTS.LOGOUT, { method: 'POST' });
        } finally {
            // Sempre limpa dados locais e redireciona, mesmo se servidor falhar
            TokenManager.remove();
            SalonManager.clearActiveSalon(); // Limpar dados do salão ativo
            window.location.href = 'index.html';
        }
    }

    // Serviços
    async getServices() {
        return this.request(API_CONFIG.ENDPOINTS.SERVICES);
    }

    // Serviços públicos (não requer autenticação)
    async getPublicServices() {
        const url = `${this.baseURL}${API_CONFIG.ENDPOINTS.SERVICES_PUBLIC}`;
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async createService(serviceData) {
        return this.request(API_CONFIG.ENDPOINTS.SERVICES, {
            method: 'POST',
            body: JSON.stringify(serviceData)
        });
    }

    async updateService(id, serviceData) {
        return this.request(`${API_CONFIG.ENDPOINTS.SERVICES}${id}`, {
            method: 'PUT',
            body: JSON.stringify(serviceData)
        });
    }

    async deleteService(id) {
        return this.request(`${API_CONFIG.ENDPOINTS.SERVICES}${id}`, {
            method: 'DELETE'
        });
    }

    // Profissionais
    async getProfessionals() {
        return this.request(API_CONFIG.ENDPOINTS.PROFESSIONALS);
    }

    async getAvailableProfessionals(serviceId) {
        const endpoint = API_CONFIG.ENDPOINTS.PROFESSIONALS_AVAILABLE.replace('{service_id}', serviceId);
        return this.request(endpoint);
    }

    async createProfessional(professionalData) {
        return this.request(API_CONFIG.ENDPOINTS.PROFESSIONALS, {
            method: 'POST',
            body: JSON.stringify(professionalData)
        });
    }

    async createProfessionalWithPhoto(formData) {
        const url = `${this.baseURL}${API_CONFIG.ENDPOINTS.PROFESSIONALS}`;
        const token = TokenManager.get();

        const config = {
            method: 'POST',
            body: formData
        };

        // Add authorization header if token is valid
        if (token && TokenManager.isValid()) {
            config.headers = {
                'Authorization': `Bearer ${token}`
            };
        }

        try {
            console.log(`[API] Making FormData request: POST ${url}`);
            const response = await fetch(url, config);

            // Handle authentication errors
            if (response.status === 401) {
                console.warn('[API] Token rejected by server (401)');
                TokenManager.remove();
                throw new Error('Session expired. Please login again.');
            }

            let data;
            const contentType = response.headers.get('content-type');

            try {
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    const textData = await response.text();
                    data = { message: textData };
                }
            } catch (jsonError) {
                console.warn('[API] Error parsing response:', jsonError);
                data = {
                    success: false,
                    error: response.ok ? 'Server response malformed' : `HTTP Error ${response.status}`
                };
            }

            // Check if HTTP response was successful
            if (!response.ok) {
                console.error(`[API] HTTP Error ${response.status}:`, data);

                if (data.success === false) {
                    throw new Error(data.error || `HTTP Error ${response.status}`);
                } else if (data.detail) {
                    throw new Error(data.detail);
                } else if (data.message) {
                    throw new Error(data.message);
                } else {
                    throw new Error(`Server error (${response.status})`);
                }
            }

            console.log(`[API] Successful FormData response for ${API_CONFIG.ENDPOINTS.PROFESSIONALS}`);
            return data;

        } catch (error) {
            console.error('[API] FormData request error:', error);

            // Handle network errors
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Connection error. Check your internet.');
            }

            // Ensure Error object is always thrown
            if (error instanceof Error) {
                throw error;
            } else {
                throw new Error('Unknown error communicating with server');
            }
        }
    }

    async updateProfessional(id, professionalData) {
        return this.request(`${API_CONFIG.ENDPOINTS.PROFESSIONALS}${id}`, {
            method: 'PUT',
            body: JSON.stringify(professionalData)
        });
    }

    async deleteProfessional(id) {
        return this.request(`${API_CONFIG.ENDPOINTS.PROFESSIONALS}${id}`, {
            method: 'DELETE'
        });
    }

    // Clientes
    async getClients() {
        return this.request(API_CONFIG.ENDPOINTS.CLIENTS);
    }

    async getClientProfile() {
        return this.request(API_CONFIG.ENDPOINTS.CLIENT_ME);
    }

    async createClient(clientData) {
        return this.request(API_CONFIG.ENDPOINTS.CLIENTS, {
            method: 'POST',
            body: JSON.stringify(clientData)
        });
    }

    async updateClient(id, clientData) {
        return this.request(`${API_CONFIG.ENDPOINTS.CLIENTS}${id}`, {
            method: 'PUT',
            body: JSON.stringify(clientData)
        });
    }

    async deleteClient(id) {
        return this.request(`${API_CONFIG.ENDPOINTS.CLIENTS}${id}`, {
            method: 'DELETE'
        });
    }

    async addClientPoints(id, points) {
        const endpoint = API_CONFIG.ENDPOINTS.CLIENT_ADD_POINTS.replace('{id}', id);
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify({ points })
        });
    }

    async redeemClientPoints(id, points) {
        const endpoint = API_CONFIG.ENDPOINTS.CLIENT_REDEEM_POINTS.replace('{id}', id);
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify({ points })
        });
    }

    // Agendamentos
    async getAppointments() {
        return this.request(API_CONFIG.ENDPOINTS.APPOINTMENTS);
    }

    async createPublicAppointment(appointmentData) {
        // Formatar dados conforme esperado pelo backend
        const formattedData = {
            nome_cliente: appointmentData.client_name,
            email_cliente: appointmentData.client_email,
            telefone_cliente: appointmentData.client_phone,
            servico_id: parseInt(appointmentData.service_id),
            profissional_id: appointmentData.professional_id ? parseInt(appointmentData.professional_id) : null,
            salon_id: 1, // ID padrão para desenvolvimento
            data_hora: appointmentData.appointment_date
        };

        return this.request(API_CONFIG.ENDPOINTS.APPOINTMENTS_PUBLIC, {
            method: 'POST',
            body: JSON.stringify(formattedData)
        });
    }

    async createAppointment(appointmentData) {
        return this.request(API_CONFIG.ENDPOINTS.APPOINTMENTS, {
            method: 'POST',
            body: JSON.stringify(appointmentData)
        });
    }

    async updateAppointment(id, appointmentData) {
        return this.request(`${API_CONFIG.ENDPOINTS.APPOINTMENTS}${id}`, {
            method: 'PUT',
            body: JSON.stringify(appointmentData)
        });
    }

    async deleteAppointment(id) {
        return this.request(`${API_CONFIG.ENDPOINTS.APPOINTMENTS}${id}`, {
            method: 'DELETE'
        });
    }

    async updateAppointmentStatus(id, status) {
        const endpoint = API_CONFIG.ENDPOINTS.APPOINTMENTS_STATUS.replace('{id}', id);
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    }

    // Relatórios
    async getDashboardStats() {
        return this.request(API_CONFIG.ENDPOINTS.REPORTS_DASHBOARD);
    }

    async getRevenueReport(period) {
        return this.request(`${API_CONFIG.ENDPOINTS.REPORTS_REVENUE}?period=${period}`);
    }

    async getNewClientsReport(period) {
        return this.request(`${API_CONFIG.ENDPOINTS.REPORTS_NEW_CLIENTS}?period=${period}`);
    }

    async getPerformanceReport(period) {
        return this.request(`${API_CONFIG.ENDPOINTS.REPORTS_PERFORMANCE}?period=${period}`);
    }
}

// ============ INSTÂNCIAS GLOBAIS ============

// Instância global do cliente da API - usada em todo o frontend
api = new APIClient();

// Expor API globalmente para compatibilidade com outros módulos (definir imediatamente)
window.api = api;

// ============ UTILITÁRIOS DE INTERFACE (UI) ============

const UI = {
    /**
     * Mostra indicador de carregamento em um elemento
     * @param {HTMLElement} element - Elemento onde mostrar o loading
     */
    showLoading: (element) => {
        if (element) {
            element.innerHTML = '<div class="loading">Carregando...</div>';
        }
    },

    /**
     * Mostra mensagem de sucesso temporária
     * @param {string} message - Mensagem a ser exibida
     * @param {HTMLElement} container - Container onde inserir (padrão: body)
     */
    showSuccess: (message, container = null) => {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success';  // Classe CSS para estilizar
        alert.textContent = message;

        // Insere no container especificado ou no body
        if (container) {
            container.prepend(alert);
        } else {
            document.body.prepend(alert);
        }

        // Remove automaticamente após 5 segundos
        setTimeout(() => alert.remove(), 5000);
    },

    /**
     * Mostra mensagem de erro temporária
     * @param {string} message - Mensagem de erro
     * @param {HTMLElement} container - Container onde inserir
     */
    showError: (message, container = null) => {
        const alert = document.createElement('div');
        alert.className = 'alert alert-error';
        alert.textContent = message;

        if (container) {
            container.prepend(alert);
        } else {
            document.body.prepend(alert);
        }

        setTimeout(() => alert.remove(), 5000);
    },

    /**
     * Mostra mensagem informativa em um elemento específico ou via alert
     * @param {string} msg - Mensagem a ser exibida
     * @param {string} targetId - ID do elemento onde inserir a mensagem (opcional)
     */
    showInfo: (msg, targetId = null) => {
        if (targetId) {
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.innerHTML = `<div class="alert alert-info">${msg}</div>`;
                return;
            }
        }
        // Fallback: usa alert se targetId não for encontrado ou não especificado
        alert(msg);
    },

    /**
     * Remove indicador de carregamento de um elemento
     * @param {HTMLElement} element - Elemento onde remover o loading
     */
    hideLoading: (element) => {
        if (element) {
            const loadingElement = element.querySelector('.loading');
            if (loadingElement) {
                loadingElement.remove();
            }
        }
    },

    /**
     * Remove todas as mensagens de alerta da página
     */
    clearAlerts: () => {
        document.querySelectorAll('.alert').forEach(alert => alert.remove());
    }
};

// ============ GUARDA DE AUTENTICAÇÃO ============

const AuthGuard = {
    /**
     * Verifica se usuário está autenticado e tem role permitida
     * Redireciona para login se não autorizado
     * @param {string[]} allowedRoles - Roles permitidos (vazio = qualquer autenticado)
     * @returns {boolean} true se autorizado, false se redirecionado
     */
    requireAuth: (allowedRoles = []) => {
        if (!TokenManager.isValid()) {
            window.location.href = 'login.html';  // Redireciona se não tem token válido
            return false;
        }

        const userRole = TokenManager.getRole();
        if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
            window.location.href = 'index.html';  // Redireciona se role não permitida
            return false;
        }

        return true;  // Autorizado
    },

    /**
     * Redireciona usuário autenticado para dashboard apropriado
     * Usado em páginas públicas para evitar que usuários logados vejam login/cadastro
     */
    redirectIfAuthenticated: () => {
        if (TokenManager.isValid()) {
            const role = TokenManager.getRole();
            if (role === 'admin') {
                window.location.href = 'dashboard-admin.html';  // Dashboard do administrador
            } else if (role === 'dono') {
                window.location.href = 'dashboard-dono.html';  // Dashboard do dono
            } else if (role === 'cliente') {
                window.location.href = 'dashboard-cliente.html';  // Dashboard do cliente
            }
        }
    }
};

// ============ GERENCIADOR DE SALÃO ============

const SalonManager = {
    /**
     * Chaves para armazenamento local
     */
    STORAGE_KEYS: {
        ACTIVE_SALON_ID: 'activeSalonId',
        SALON_INFO: 'salonInfo'
    },

    /**
     * Captura salon_id da URL (parâmetro de query)
     * @returns {string|null} salon_id ou null se não encontrado
     */
    getSalonIdFromURL: () => {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('salon_id');
    },

    /**
     * Define o salão ativo
     * @param {number} salonId - ID do salão
     * @param {Object} salonInfo - Informações do salão (opcional)
     */
    setActiveSalon: (salonId, salonInfo = null) => {
        try {
            sessionStorage.setItem(SalonManager.STORAGE_KEYS.ACTIVE_SALON_ID, salonId.toString());
            if (salonInfo) {
                sessionStorage.setItem(SalonManager.STORAGE_KEYS.SALON_INFO, JSON.stringify(salonInfo));
            }
            console.log(`[SALON] Salão ativo definido: ${salonId}`);
        } catch (error) {
            console.error('[SALON] Erro ao salvar salão ativo:', error);
        }
    },

    /**
     * Obtém o ID do salão ativo
     * @returns {number|null} ID do salão ativo ou null
     */
    getActiveSalonId: () => {
        try {
            const salonId = sessionStorage.getItem(SalonManager.STORAGE_KEYS.ACTIVE_SALON_ID);
            return salonId ? parseInt(salonId) : null;
        } catch (error) {
            console.error('[SALON] Erro ao obter salão ativo:', error);
            return null;
        }
    },

    /**
     * Obtém informações do salão ativo
     * @returns {Object|null} Informações do salão ou null
     */
    getActiveSalonInfo: () => {
        try {
            const salonInfo = sessionStorage.getItem(SalonManager.STORAGE_KEYS.SALON_INFO);
            return salonInfo ? JSON.parse(salonInfo) : null;
        } catch (error) {
            console.error('[SALON] Erro ao obter informações do salão:', error);
            return null;
        }
    },

    /**
     * Carrega informações do salão do backend com validações de segurança
     * @param {number} salonId - ID do salão
     * @returns {Promise<Object>} Informações do salão
     */
    loadSalonInfo: async (salonId) => {
        try {
            console.log(`[SALON] Carregando informações do salão ${salonId}...`);

            // Validação básica do ID
            if (!salonId || salonId <= 0) {
                throw new Error('ID do salão inválido');
            }

            const response = await fetch(`${API_CONFIG.BASE_URL}/salons/public/${salonId}`);

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Salão não encontrado ou não disponível');
                } else if (response.status === 403) {
                    throw new Error('Este salão não está disponível no momento');
                } else if (response.status === 400) {
                    throw new Error('ID do salão inválido');
                } else {
                    throw new Error(`Erro ao carregar informações do salão (${response.status})`);
                }
            }

            const salonInfo = await response.json();

            // Validação da resposta
            if (!salonInfo || !salonInfo.id || !salonInfo.nome) {
                throw new Error('Resposta inválida do servidor');
            }

            SalonManager.setActiveSalon(salonId, salonInfo);

            console.log(`[SALON] Informações carregadas com sucesso:`, salonInfo);
            return salonInfo;

        } catch (error) {
            console.error('[SALON] Erro ao carregar informações do salão:', error);

            // Limpar dados inválidos do storage
            if (error.message.includes('não encontrado') || error.message.includes('não disponível')) {
                SalonManager.clearActiveSalon();
            }

            throw error;
        }
    },

    /**
     * Inicializar salão baseado na URL ou cliente logado
     * @returns {Promise<Object>} Informações do salão ativo
     */
    initializeSalon: async () => {
        try {
            // First, try to get from URL (highest priority)
            let salonId = SalonManager.getSalonIdFromURL();

            if (salonId) {
                console.log(`[SALON] Salon found in URL: ${salonId}`);
                return await SalonManager.loadSalonInfo(parseInt(salonId));
            }

            // If not in URL, check if we already have an active salon selected by user
            salonId = SalonManager.getActiveSalonId();
            if (salonId) {
                console.log(`[SALON] Active salon found in storage: ${salonId}`);
                let salonInfo = SalonManager.getActiveSalonInfo();
                if (!salonInfo) {
                    // Load information if not cached
                    salonInfo = await SalonManager.loadSalonInfo(salonId);
                }
                return salonInfo;
            }

            // For clients, don't use profile salon to avoid confusion
            // Clients should explicitly select which salon to use
            console.log('[SALON] Skipping client profile salon to respect user selection');

            // Fallback: try to load available salons and use the first one
            try {
                const availableSalons = await SalonManager.loadAvailableSalons();
                if (availableSalons && availableSalons.length > 0) {
                    const firstSalon = availableSalons[0];
                    console.log(`[SALON] Using first available salon: ${firstSalon.id} (${firstSalon.nome})`);
                    return await SalonManager.loadSalonInfo(firstSalon.id);
                }
            } catch (error) {
                console.warn('[SALON] Error loading available salons:', error);
            }

            // Last resort: default salon (ID 2 if available, otherwise 1)
            console.log('[SALON] Using fallback salon logic');
            try {
                // Try salon 2 first (assuming it's a real salon)
                return await SalonManager.loadSalonInfo(2);
            } catch (error) {
                console.warn('[SALON] Salon 2 not available, using default salon (ID 1)');
                return await SalonManager.loadSalonInfo(1);
            }

        } catch (error) {
            console.error('[SALON] Error initializing salon:', error);
            throw error;
        }
    },

    /**
     * Troca para um salão diferente
     * @param {number} newSalonId - ID do novo salão
     * @returns {Promise<Object>} Informações do novo salão
     */
    switchSalon: async (newSalonId) => {
        try {
            console.log(`[SALON] Trocando para salão ${newSalonId}...`);

            // Carrega informações do novo salão
            const salonInfo = await SalonManager.loadSalonInfo(newSalonId);

            // Dispara evento de mudança de salão
            window.dispatchEvent(new CustomEvent('salonChanged', {
                detail: { salonId: newSalonId, salonInfo }
            }));

            console.log(`[SALON] Troca realizada com sucesso`);
            return salonInfo;

        } catch (error) {
            console.error('[SALON] Erro ao trocar de salão:', error);
            throw error;
        }
    },

    /**
     * Carrega lista de salões disponíveis
     * @returns {Promise<Array>} Lista de salões
     */
    loadAvailableSalons: async () => {
        try {
            console.log('[SALON] Carregando lista de salões disponíveis...');
            const response = await fetch(`${API_CONFIG.BASE_URL}/salons/public`);

            if (!response.ok) {
                throw new Error(`Erro ao carregar salões (${response.status})`);
            }

            const salons = await response.json();
            console.log(`[SALON] ${salons.length} salões disponíveis carregados`);
            return salons;

        } catch (error) {
            console.error('[SALON] Erro ao carregar salões disponíveis:', error);
            throw error;
        }
    },

    /**
     * Limpa dados do salão ativo
     */
    clearActiveSalon: () => {
        try {
            sessionStorage.removeItem(SalonManager.STORAGE_KEYS.ACTIVE_SALON_ID);
            sessionStorage.removeItem(SalonManager.STORAGE_KEYS.SALON_INFO);
            console.log('[SALON] Dados do salão ativo limpos');
        } catch (error) {
            console.error('[SALON] Erro ao limpar dados do salão:', error);
        }
    },

    /**
     * Verifica se há um salão ativo válido
     * @returns {boolean} true se há salão ativo
     */
    hasActiveSalon: () => {
        const salonId = SalonManager.getActiveSalonId();
        const salonInfo = SalonManager.getActiveSalonInfo();
        return !!(salonId && salonInfo && salonInfo.id === salonId);
    }
};

// ============ UTILITÁRIOS DE FORMATAÇÃO ============

const Formatter = {
    /**
     * Formata valor numérico para moeda brasileira (R$)
     * @param {number} value - Valor a ser formatado
     * @returns {string} Valor formatado (ex: "R$ 123,45")
     */
    currency: (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },

    /**
     * Formata data para padrão brasileiro (DD/MM/YYYY)
     * @param {string} dateString - Data em formato ISO
     * @returns {string} Data formatada
     */
    date: (dateString) => {
        return new Date(dateString).toLocaleDateString('pt-BR');
    },

    /**
     * Formata data e hora para padrão brasileiro
     * @param {string} dateString - Data/hora em formato ISO
     * @returns {string} Data e hora formatadas
     */
    datetime: (dateString) => {
        return new Date(dateString).toLocaleString('pt-BR');
    }
};