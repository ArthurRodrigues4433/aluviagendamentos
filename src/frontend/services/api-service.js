/**
 * Serviço de API - Cliente HTTP centralizado para comunicação com backend.
 * Gerencia autenticação, CORS e tratamento de erros.
 */

export default class ApiService {
    constructor() {
        this.baseURL = API_CONFIG.BASE_URL;
    }

    /**
     * Método genérico de requisição HTTP com autenticação e tratamento de erros.
     * @param {string} endpoint - Endpoint da API
     * @param {Object} options - Opções do fetch
     * @returns {Promise<Object>} Dados da resposta
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const token = TokenManager.get();

        // Default headers
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            ...options
        };

        // Add authorization header if token is valid
        if (token && TokenManager.isValid()) {
            config.headers['Authorization'] = `Bearer ${token}`;
            console.log(`[API] Including Authorization header for ${endpoint}`);
        } else if (token && !TokenManager.isValid()) {
            console.warn('[API] Invalid token detected, removing...');
            TokenManager.remove();
        }

        try {
            console.log(`[API] Making request: ${config.method || 'GET'} ${url}`);
            const response = await fetch(url, config);

            // Handle authentication errors
            if (response.status === 401) {
                console.warn('[API] Token rejected by server (401)');
                TokenManager.remove();
                throw new Error('Session expired. Please login again.');
            }

            // Handle validation errors
            if (response.status === 422) {
                console.warn('[API] Validation error (422)');
                let errorData;
                try {
                    errorData = await response.json();
                    const errorMessage = errorData.detail || errorData.message || 'Invalid data sent';
                    throw new Error(`Validation error: ${errorMessage}`);
                } catch (jsonError) {
                    throw new Error('Validation error in sent data');
                }
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

            console.log(`[API] Successful response for ${endpoint}`);
            return data;

        } catch (error) {
            console.error('[API] Request error:', error);

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

    // ============ MÉTODOS DE AUTENTICAÇÃO ============

    /**
     * Login de usuário (dono ou cliente)
     * @param {string} email - Email do usuário
     * @param {string} password - Senha do usuário
     * @param {boolean} isOwner - Se o usuário é dono do salão
     * @returns {Promise<Object>} Resposta de login com tokens
     */
    async login(email, password, isOwner = false) {
        const endpoint = isOwner ? API_CONFIG.ENDPOINTS.LOGIN : API_CONFIG.ENDPOINTS.CLIENT_LOGIN;
        const response = await this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify({ email, senha: password })
        });

        // Store JWT token automatically if login successful
        if (response.access_token) {
            TokenManager.set(response.access_token);
        }

        return response;
    }

    /**
     * Login específico de cliente
     * @param {string} email - Email do cliente
     * @param {string} password - Senha do cliente
     * @returns {Promise<Object>} Resposta de login com tokens
     */
    async loginClient(email, password) {
        try {
            const response = await this.login(email, password, false);

            // Additional client validations
            if (!response.access_token) {
                throw new Error('Access token not received from server');
            }

            if (response.role !== 'cliente') {
                throw new Error('Invalid response - incorrect role');
            }

            return response;
        } catch (error) {
            console.error('Client login error:', error);
            throw error;
        }
    }

    /**
     * Registro de usuário (dono ou cliente)
     * @param {Object} userData - Dados de registro do usuário
     * @param {boolean} isOwner - Se está registrando como dono
     * @returns {Promise<Object>} Resposta de registro com tokens
     */
    async register(userData, isOwner = false) {
        const endpoint = isOwner ? API_CONFIG.ENDPOINTS.REGISTER : API_CONFIG.ENDPOINTS.CLIENT_REGISTER;

        if (isOwner) {
            const ownerData = {
                nome: userData.name,
                email: userData.email,
                senha: userData.password,
                ativo: true,
                admin: true
            };
            return this.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(ownerData)
            });
        }

        const clientData = {
            nome: userData.name,
            email: userData.email,
            telefone: userData.phone,
            senha: userData.password,
            salon_id: userData.salon_id || 1
        };

        const response = await this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(clientData)
        });

        // Validate response
        if (response.success === false) {
            throw new Error(response.error || 'Registration error');
        }

        if (!response.client_id) {
            throw new Error('Invalid server response - client_id missing');
        }

        // Store token if registration successful
        if (response.access_token) {
            TokenManager.set(response.access_token);
        }

        return response;
    }

    /**
     * Logout do usuário
     * Remove token e redireciona para página inicial
     */
    async logout() {
        try {
            await this.request(API_CONFIG.ENDPOINTS.LOGOUT, { method: 'POST' });
        } finally {
            TokenManager.remove();
            SalonManager.clearActiveSalon();
            window.location.href = 'index.html';
        }
    }

    // ============ MÉTODOS DE SERVIÇOS ============

    async getServices() {
        return this.request(API_CONFIG.ENDPOINTS.SERVICES);
    }

    async getPublicServices() {
        const url = `${this.baseURL}${API_CONFIG.ENDPOINTS.SERVICES_PUBLIC}`;
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json' }
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

    // ============ MÉTODOS DE PROFISSIONAIS ============

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

    // ============ MÉTODOS DE CLIENTES ============

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

    // ============ MÉTODOS DE AGENDAMENTOS ============

    async getAppointments() {
        return this.request(API_CONFIG.ENDPOINTS.APPOINTMENTS);
    }

    async createPublicAppointment(appointmentData) {
        const formattedData = {
            nome_cliente: appointmentData.client_name,
            email_cliente: appointmentData.client_email,
            telefone_cliente: appointmentData.client_phone,
            service_id: parseInt(appointmentData.service_id),
            professional_id: appointmentData.professional_id ? parseInt(appointmentData.professional_id) : null,
            salon_id: appointmentData.salon_id || 1,
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

    // ============ MÉTODOS DE RELATÓRIOS ============

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