/**
 * Utilitários de formatação - Funções de formatação de dados.
 * Gerencia moeda, datas e outras formatações de exibição.
 */

export default class Formatter {
    /**
     * Format number to Brazilian currency (R$)
     * @param {number} value - Value to format
     * @returns {string} Formatted currency string
     */
    static currency(value) {
        if (value === null || value === undefined) return 'R$ 0,00';

        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    /**
     * Formatar data para padrão brasileiro (DD/MM/YYYY)
     * @param {string|Date} dateString - Data a formatar
     * @returns {string} String de data formatada
     */
    static date(dateString) {
        if (!dateString) return '';

        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('pt-BR');
        } catch (error) {
            console.warn('Invalid date format:', dateString);
            return dateString;
        }
    }

    /**
     * Formatar data e hora para padrão brasileiro
     * @param {string|Date} dateString - Data/hora a formatar
     * @returns {string} String de data/hora formatada
     */
    static datetime(dateString) {
        if (!dateString) return '';

        try {
            const date = new Date(dateString);
            return date.toLocaleString('pt-BR');
        } catch (error) {
            console.warn('Invalid datetime format:', dateString);
            return dateString;
        }
    }

    /**
     * Formatar hora para HH:MM
     * @param {string|Date} timeString - Hora a formatar
     * @returns {string} String de hora formatada
     */
    static time(timeString) {
        if (!timeString) return '';

        try {
            const date = new Date(timeString);
            return date.toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            console.warn('Invalid time format:', timeString);
            return timeString;
        }
    }

    /**
     * Formatar número de telefone para padrão brasileiro
     * @param {string} phone - Número de telefone a formatar
     * @returns {string} String de telefone formatada
     */
    static phone(phone) {
        if (!phone) return '';

        // Remove all non-digits
        const cleaned = phone.replace(/\D/g, '');

        // Format according to length
        if (cleaned.length === 11) {
            // Mobile: (11) 99999-9999
            return cleaned.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
        } else if (cleaned.length === 10) {
            // Landline: (11) 9999-9999
            return cleaned.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
        }

        return phone; // Return original if format doesn't match
    }

    /**
     * Formatar CPF para XXX.XXX.XXX-XX
     * @param {string} cpf - CPF a formatar
     * @returns {string} String de CPF formatada
     */
    static cpf(cpf) {
        if (!cpf) return '';

        const cleaned = cpf.replace(/\D/g, '');
        if (cleaned.length !== 11) return cpf;

        return cleaned.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }

    /**
     * Formatar CEP para XXXXX-XXX
     * @param {string} cep - CEP a formatar
     * @returns {string} String de CEP formatada
     */
    static cep(cep) {
        if (!cep) return '';

        const cleaned = cep.replace(/\D/g, '');
        if (cleaned.length !== 8) return cep;

        return cleaned.replace(/(\d{5})(\d{3})/, '$1-$2');
    }

    /**
     * Formatar número com separadores de milhares
     * @param {number} value - Número a formatar
     * @param {number} decimals - Número de casas decimais
     * @returns {string} String de número formatada
     */
    static number(value, decimals = 2) {
        if (value === null || value === undefined) return '0';

        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    }

    /**
     * Formatar porcentagem
     * @param {number} value - Valor a formatar como porcentagem
     * @param {number} decimals - Número de casas decimais
     * @returns {string} String de porcentagem formatada
     */
    static percentage(value, decimals = 1) {
        if (value === null || value === undefined) return '0%';

        return new Intl.NumberFormat('pt-BR', {
            style: 'percent',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value / 100);
    }

    /**
     * Capitalizar primeira letra de cada palavra
     * @param {string} text - Texto a capitalizar
     * @returns {string} Texto capitalizado
     */
    static capitalize(text) {
        if (!text) return '';

        return text.toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Truncar texto para comprimento especificado
     * @param {string} text - Texto a truncar
     * @param {number} maxLength - Comprimento máximo
     * @param {string} suffix - Sufixo a adicionar quando truncado
     * @returns {string} Texto truncado
     */
    static truncate(text, maxLength = 50, suffix = '...') {
        if (!text || text.length <= maxLength) return text;

        return text.substring(0, maxLength - suffix.length) + suffix;
    }

    /**
     * Formatar tamanho de arquivo em formato legível por humanos
     * @param {number} bytes - Tamanho em bytes
     * @returns {string} String de tamanho formatada
     */
    static fileSize(bytes) {
        if (bytes === 0) return '0 B';

        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Formatar duração em minutos para formato legível por humanos
     * @param {number} minutes - Duração em minutos
     * @returns {string} String de duração formatada
     */
    static duration(minutes) {
        if (!minutes || minutes <= 0) return '0 min';

        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;

        if (hours > 0) {
            return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
        }

        return `${mins}min`;
    }

    /**
     * Obter tempo relativo (ex: "2 horas atrás")
     * @param {string|Date} dateString - Data a comparar
     * @returns {string} String de tempo relativo
     */
    static relativeTime(dateString) {
        if (!dateString) return '';

        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);

            const intervals = [
                { label: 'ano', seconds: 31536000 },
                { label: 'mês', seconds: 2592000 },
                { label: 'dia', seconds: 86400 },
                { label: 'hora', seconds: 3600 },
                { label: 'minuto', seconds: 60 },
                { label: 'segundo', seconds: 1 }
            ];

            for (const interval of intervals) {
                const count = Math.floor(diffInSeconds / interval.seconds);
                if (count > 0) {
                    const plural = count > 1 ? 's' : '';
                    return `${count} ${interval.label}${plural} atrás`;
                }
            }

            return 'agora';
        } catch (error) {
            console.warn('Invalid date for relative time:', dateString);
            return '';
        }
    }
}