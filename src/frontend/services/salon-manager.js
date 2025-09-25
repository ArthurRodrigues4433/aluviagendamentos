/**
 * Gerenciador de Salão - Gerencia seleção e administração de salão.
 * Gerencia estado de salão ativo e troca de salão.
 */

export default class SalonManager {
    static STORAGE_KEYS = {
        ACTIVE_SALON_ID: 'activeSalonId',
        SALON_INFO: 'salonInfo'
    };

    /**
     * Obter salon_id dos parâmetros de query da URL
     * @returns {string|null} salon_id ou null se não encontrado
     */
    static getSalonIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('salon_id');
    }

    /**
     * Definir salão ativo
     * @param {number} salonId - ID do salão
     * @param {Object} salonInfo - Informações do salão (opcional)
     */
    static setActiveSalon(salonId, salonInfo = null) {
        try {
            sessionStorage.setItem(this.STORAGE_KEYS.ACTIVE_SALON_ID, salonId.toString());
            if (salonInfo) {
                sessionStorage.setItem(this.STORAGE_KEYS.SALON_INFO, JSON.stringify(salonInfo));
            }
            console.log(`[SALON] Active salon set: ${salonId}`);
        } catch (error) {
            console.error('[SALON] Error saving active salon:', error);
        }
    }

    /**
     * Obter ID do salão ativo
     * @returns {number|null} ID do salão ativo ou null
     */
    static getActiveSalonId() {
        try {
            const salonId = sessionStorage.getItem(this.STORAGE_KEYS.ACTIVE_SALON_ID);
            return salonId ? parseInt(salonId) : null;
        } catch (error) {
            console.error('[SALON] Error getting active salon:', error);
            return null;
        }
    }

    /**
     * Obter informações do salão ativo
     * @returns {Object|null} Informações do salão ou null
     */
    static getActiveSalonInfo() {
        try {
            const salonInfo = sessionStorage.getItem(this.STORAGE_KEYS.SALON_INFO);
            return salonInfo ? JSON.parse(salonInfo) : null;
        } catch (error) {
            console.error('[SALON] Error getting salon info:', error);
            return null;
        }
    }

    /**
     * Carregar informações do salão do backend com validações de segurança
     * @param {number} salonId - ID do salão a carregar
     * @returns {Promise<Object>} Informações do salão
     */
    static async loadSalonInfo(salonId) {
        try {
            console.log(`[SALON] Loading salon information: ${salonId}`);

            // Basic ID validation
            if (!salonId || salonId <= 0) {
                throw new Error('Invalid salon ID');
            }

            const response = await fetch(`${API_CONFIG.BASE_URL}/salons/public/${salonId}`);

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Salon not found or not available');
                } else if (response.status === 403) {
                    throw new Error('This salon is not available at the moment');
                } else if (response.status === 400) {
                    throw new Error('Invalid salon ID');
                } else {
                    throw new Error(`Error loading salon information (${response.status})`);
                }
            }

            const salonInfo = await response.json();

            // Response validation
            if (!salonInfo || !salonInfo.id || !salonInfo.nome) {
                throw new Error('Invalid server response');
            }

            this.setActiveSalon(salonId, salonInfo);

            console.log(`[SALON] Information loaded successfully:`, salonInfo);
            return salonInfo;

        } catch (error) {
            console.error('[SALON] Error loading salon information:', error);

            // Clear invalid data from storage
            if (error.message.includes('not found') || error.message.includes('not available')) {
                this.clearActiveSalon();
            }

            throw error;
        }
    }

    /**
     * Inicializar salão baseado na URL ou cliente logado
     * @returns {Promise<Object>} Informações do salão ativo
     */
    static async initializeSalon() {
        try {
            // For clients, always use their profile salon_id (highest priority)
            try {
                const userRole = TokenManager.getRole();
                if (userRole === 'cliente') {
                    // Get client profile to get salon_id
                    const profileResponse = await fetch(`${API_CONFIG.BASE_URL}/clients/profile`, {
                        headers: {
                            'Authorization': `Bearer ${TokenManager.get()}`,
                            'Content-Type': 'application/json'
                        }
                    });

                    if (profileResponse.ok) {
                        const profile = await profileResponse.json();
                        if (profile && profile.salon_id) {
                            console.log(`[SALON] Client using profile salon: ${profile.salon_id}`);
                            return await this.loadSalonInfo(parseInt(profile.salon_id));
                        }
                    }
                }
            } catch (error) {
                console.warn('[SALON] Error getting client salon from profile:', error);
            }

            // For owners/admins, try to get from URL first
            let salonId = this.getSalonIdFromURL();

            if (salonId) {
                console.log(`[SALON] Salon found in URL: ${salonId}`);
                return await this.loadSalonInfo(parseInt(salonId));
            }

            // If not in URL, check if we already have an active salon selected by user
            salonId = this.getActiveSalonId();
            if (salonId) {
                console.log(`[SALON] Active salon found in storage: ${salonId}`);
                let salonInfo = this.getActiveSalonInfo();
                if (!salonInfo) {
                    // Load information if not cached
                    salonInfo = await this.loadSalonInfo(salonId);
                }
                return salonInfo;
            }

            // Fallback: try to load available salons and use the first one
            try {
                const availableSalons = await this.loadAvailableSalons();
                if (availableSalons && availableSalons.length > 0) {
                    const firstSalon = availableSalons[0];
                    console.log(`[SALON] Using first available salon: ${firstSalon.id} (${firstSalon.nome})`);
                    return await this.loadSalonInfo(firstSalon.id);
                }
            } catch (error) {
                console.warn('[SALON] Error loading available salons:', error);
            }

            // Last resort: default salon (ID 2 if available, otherwise 1)
            console.log('[SALON] Using fallback salon logic');
            try {
                // Try salon 2 first (assuming it's a real salon)
                return await this.loadSalonInfo(2);
            } catch (error) {
                console.warn('[SALON] Salon 2 not available, using default salon (ID 1)');
                return await this.loadSalonInfo(1);
            }

        } catch (error) {
            console.error('[SALON] Error initializing salon:', error);
            throw error;
        }
    }

    /**
     * Trocar para um salão diferente (apenas para donos/admins)
     * @param {number} newSalonId - Novo ID do salão
     * @returns {Promise<Object>} Informações do novo salão
     */
    static async switchSalon(newSalonId) {
        try {
            // Check if user is a client - clients cannot switch salons
            const userRole = TokenManager.getRole();
            if (userRole === 'cliente') {
                throw new Error('Clientes não podem trocar de salão. Você só pode agendar serviços no seu salão cadastrado.');
            }

            console.log(`[SALON] Switching to salon ${newSalonId}`);

            // Load new salon information
            const salonInfo = await this.loadSalonInfo(newSalonId);

            // Dispatch salon change event
            window.dispatchEvent(new CustomEvent('salonChanged', {
                detail: { salonId: newSalonId, salonInfo }
            }));

            console.log(`[SALON] Switch completed successfully`);
            return salonInfo;

        } catch (error) {
            console.error('[SALON] Error switching salon:', error);
            throw error;
        }
    }

    /**
     * Carregar lista de salões disponíveis
     * @returns {Promise<Array>} Lista de salões
     */
    static async loadAvailableSalons() {
        try {
            console.log('[SALON] Loading list of available salons');
            const response = await fetch(`${API_CONFIG.BASE_URL}/salons/public`);

            if (!response.ok) {
                throw new Error(`Error loading salons (${response.status})`);
            }

            const salons = await response.json();
            console.log(`[SALON] ${salons.length} available salons loaded`);
            return salons;

        } catch (error) {
            console.error('[SALON] Error loading available salons:', error);
            throw error;
        }
    }

    /**
     * Limpar dados do salão ativo
     */
    static clearActiveSalon() {
        try {
            sessionStorage.removeItem(this.STORAGE_KEYS.ACTIVE_SALON_ID);
            sessionStorage.removeItem(this.STORAGE_KEYS.SALON_INFO);
            console.log('[SALON] Active salon data cleared');
        } catch (error) {
            console.error('[SALON] Error clearing salon data:', error);
        }
    }

    /**
     * Verificar se há um salão ativo válido
     * @returns {boolean} true se há um salão ativo
     */
    static hasActiveSalon() {
        const salonId = this.getActiveSalonId();
        const salonInfo = this.getActiveSalonInfo();
        return !!(salonId && salonInfo && salonInfo.id === salonId);
    }

    /**
     * Obter nome do salão ativo
     * @returns {string} Nome do salão ou string vazia
     */
    static getActiveSalonName() {
        const info = this.getActiveSalonInfo();
        return info ? info.nome : '';
    }

    /**
     * Verificar se salão está disponível para agendamentos
     * @returns {boolean} true se salão está disponível
     */
    static isSalonAvailable() {
        const info = this.getActiveSalonInfo();
        return info && info.ativo !== false;
    }

    /**
     * Obter informações de contato do salão
     * @returns {Object} Informações de contato
     */
    static getSalonContact() {
        const info = this.getActiveSalonInfo();
        return info ? {
            telefone: info.telefone || '',
            email: info.email || '',
            endereco: info.endereco || ''
        } : {};
    }
}