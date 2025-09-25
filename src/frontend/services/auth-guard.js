/**
 * Guarda de Autenticação - Proteção de rotas e redirecionamento de usuário.
 * Gerencia verificações de autenticação e redirecionamentos baseados em papéis de usuário.
 */

export default class AuthGuard {
    /**
     * Verificar se usuário está autenticado e tem papéis permitidos
     * Redireciona para login se não autorizado
     * @param {string[]} allowedRoles - Papéis permitidos (vazio = qualquer autenticado)
     * @returns {boolean} true se autorizado, false se redirecionado
     */
    static requireAuth(allowedRoles = []) {
        if (!TokenManager.isValid()) {
            window.location.href = 'login.html';
            return false;
        }

        const userRole = TokenManager.getRole();
        if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
            window.location.href = 'index.html';
            return false;
        }

        return true;
    }

    /**
     * Redirecionar usuários autenticados para dashboard apropriado
     * Usado em páginas públicas para evitar mostrar login para usuários logados
     */
    static redirectIfAuthenticated() {
        if (TokenManager.isValid()) {
            const role = TokenManager.getRole();
            if (role === 'admin') {
                window.location.href = 'dashboard-admin.html';
            } else if (role === 'dono') {
                window.location.href = 'dashboard-dono.html';
            } else if (role === 'cliente') {
                window.location.href = 'dashboard-cliente.html';
            }
        }
    }

    /**
     * Verificar se usuário atual tem papel de admin
     * @returns {boolean} true se usuário é admin
     */
    static isAdmin() {
        return TokenManager.isValid() && TokenManager.getRole() === 'admin';
    }

    /**
     * Verificar se usuário atual tem papel de dono
     * @returns {boolean} true se usuário é dono
     */
    static isOwner() {
        return TokenManager.isValid() && TokenManager.getRole() === 'dono';
    }

    /**
     * Verificar se usuário atual tem papel de cliente
     * @returns {boolean} true se usuário é cliente
     */
    static isClient() {
        return TokenManager.isValid() && TokenManager.getRole() === 'cliente';
    }

    /**
     * Verificar se usuário está autenticado
     * @returns {boolean} true se autenticado
     */
    static isAuthenticated() {
        return TokenManager.isValid();
    }

    /**
     * Obter papel do usuário atual
     * @returns {string|null} papel do usuário ou null se não autenticado
     */
    static getCurrentRole() {
        return TokenManager.getRole();
    }

    /**
     * Obter informações do usuário atual do token
     * @returns {Object|null} informações do usuário ou null se não autenticado
     */
    static getCurrentUser() {
        if (!this.isAuthenticated()) return null;

        const token = TokenManager.get();
        if (!token) return null;

        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return {
                id: payload.sub,
                role: payload.role,
                exp: payload.exp
            };
        } catch (error) {
            console.error('Error parsing user token:', error);
            return null;
        }
    }

    /**
     * Requerer papel de admin para operação atual
     * @param {string} redirectUrl - URL para redirecionar se não admin (padrão: index.html)
     * @returns {boolean} true se admin, false se redirecionado
     */
    static requireAdmin(redirectUrl = 'index.html') {
        if (!this.isAdmin()) {
            window.location.href = redirectUrl;
            return false;
        }
        return true;
    }

    /**
     * Requerer papel de dono para operação atual
     * @param {string} redirectUrl - URL para redirecionar se não dono (padrão: index.html)
     * @returns {boolean} true se dono, false se redirecionado
     */
    static requireOwner(redirectUrl = 'index.html') {
        if (!this.isOwner()) {
            window.location.href = redirectUrl;
            return false;
        }
        return true;
    }

    /**
     * Requerer papel de cliente para operação atual
     * @param {string} redirectUrl - URL para redirecionar se não cliente (padrão: index.html)
     * @returns {boolean} true se cliente, false se redirecionado
     */
    static requireClient(redirectUrl = 'index.html') {
        if (!this.isClient()) {
            window.location.href = redirectUrl;
            return false;
        }
        return true;
    }

    /**
     * Verificar se usuário pode acessar recursos de gerenciamento de salão
     * @returns {boolean} true se usuário pode gerenciar salão
     */
    static canManageSalon() {
        const role = this.getCurrentRole();
        return role === 'admin' || role === 'dono';
    }

    /**
     * Verificar se usuário pode acessar recursos de cliente
     * @returns {boolean} true se usuário pode acessar recursos de cliente
     */
    static canAccessClientFeatures() {
        const role = this.getCurrentRole();
        return role === 'admin' || role === 'dono' || role === 'cliente';
    }

    /**
     * Verificar se usuário pode acessar recursos apenas de admin
     * @returns {boolean} true se usuário tem privilégios de admin
     */
    static canAccessAdminFeatures() {
        return this.isAdmin();
    }

    /**
     * Fazer logout do usuário atual e redirecionar para login
     */
    static logout() {
        TokenManager.remove();
        SalonManager.clearActiveSalon();
        window.location.href = 'login.html';
    }

    /**
     * Lidar com erros de autenticação (respostas 401)
     * Automaticamente faz logout do usuário e redireciona
     */
    static handleAuthError() {
        console.warn('Authentication error - logging out user');
        this.logout();
    }

    /**
     * Atualizar token de autenticação se necessário
     * @returns {Promise<boolean>} true se token foi atualizado
     */
    static async refreshTokenIfNeeded() {
        // This would implement token refresh logic
        // For now, just check if current token is still valid
        return this.isAuthenticated();
    }
}