// Configurações da API
const API_CONFIG = {
    BASE_URL: 'http://localhost:8000', // URL do back-end FastAPI
    ENDPOINTS: {
        // Auth - Endpoints de autenticação
        LOGIN: '/auth/login',
        REGISTER: '/auth/register',
        LOGOUT: '/auth/logout',
        ME: '/auth/me',
        REFRESH: '/auth/refresh',

        // Clients - Endpoints de clientes
        CLIENTS: '/clients/',
        CLIENT_LOGIN: '/clients/login',
        CLIENT_REGISTER: '/clients/register',
        CLIENT_ME: '/clients/me',
        CLIENT_ADD_POINTS: '/clients/{id}/add_points',
        CLIENT_REDEEM_POINTS: '/clients/{id}/redeem_points',

        // Services - Endpoints de serviços
        SERVICES: '/services/',
        SERVICES_PUBLIC: '/services/public',

        // Professionals - Endpoints de profissionais
        PROFESSIONALS: '/professionals/',
        PROFESSIONALS_AVAILABLE: '/professionals/available/{service_id}',

        // Appointments - Endpoints de agendamentos
        APPOINTMENTS: '/appointments/',
        APPOINTMENTS_PUBLIC: '/appointments/public',
        APPOINTMENTS_STATUS: '/appointments/{id}/status',

        // Reports - Endpoints de relatórios
        REPORTS_DASHBOARD: '/reports/dashboard',
        REPORTS_REVENUE: '/reports/revenue/daily',
        REPORTS_NEW_CLIENTS: '/reports/clients/new',
        REPORTS_PERFORMANCE: '/reports/performance'
    }
};

// Utilitários para JWT - Gerenciamento seguro de tokens
const TokenManager = {
    /**
     * Armazena token JWT no localStorage
     * @param {string} token - Token JWT a ser armazenado
     */
    set: (token) => {
        try {
            localStorage.setItem('token', token);
            console.log('[TokenManager] Token armazenado com sucesso');
        } catch (error) {
            console.error('[TokenManager] Erro ao armazenar token:', error);
        }
    },

    /**
     * Recupera token JWT do localStorage
     * @returns {string|null} Token JWT ou null se não existir
     */
    get: () => {
        try {
            return localStorage.getItem('token');
        } catch (error) {
            console.error('[TokenManager] Erro ao recuperar token:', error);
            return null;
        }
    },

    /**
     * Remove token JWT do localStorage
     */
    remove: () => {
        try {
            localStorage.removeItem('token');
            console.log('[TokenManager] Token removido');
        } catch (error) {
            console.error('[TokenManager] Erro ao remover token:', error);
        }
    },

    /**
     * Verifica se o token é válido (não expirado e bem formado)
     * @returns {boolean} true se válido, false caso contrário
     */
    isValid: () => {
        const token = TokenManager.get();
        if (!token) {
            console.log('[TokenManager] Nenhum token encontrado');
            return false;
        }

        try {
            // Decodificar payload do JWT (parte do meio)
            const payload = JSON.parse(atob(token.split('.')[1]));

            // Verificar se não expirou
            const isExpired = payload.exp <= Date.now() / 1000;

            if (isExpired) {
                console.log('[TokenManager] Token expirado');
                TokenManager.remove(); // Remover token expirado
                return false;
            }

            console.log('[TokenManager] Token válido');
            return true;
        } catch (error) {
            console.error('[TokenManager] Erro ao validar token:', error);
            TokenManager.remove(); // Remover token malformado
            return false;
        }
    },

    /**
     * Extrai o role do token JWT
     * @returns {string|null} Role do usuário ou null se erro
     */
    getRole: () => {
        const token = TokenManager.get();
        if (!token) return null;

        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.role || payload.user_type || null;
        } catch (error) {
            console.error('[TokenManager] Erro ao extrair role:', error);
            return null;
        }
    },

    /**
     * Extrai dados completos do payload do token
     * @returns {object|null} Payload decodificado ou null se erro
     */
    getPayload: () => {
        const token = TokenManager.get();
        if (!token) return null;

        try {
            return JSON.parse(atob(token.split('.')[1]));
        } catch (error) {
            console.error('[TokenManager] Erro ao extrair payload:', error);
            return null;
        }
    }
};