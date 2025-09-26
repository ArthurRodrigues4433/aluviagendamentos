// Sistema de Validação Avançada de Formulários
class FormValidator {
    constructor(form, options = {}) {
        this.form = form;
        this.options = {
            validateOnBlur: true,
            validateOnInput: false,
            showErrors: true,
            errorClass: 'error',
            successClass: 'success',
            errorContainer: null,
            onValidate: null,
            onError: null,
            onSuccess: null,
            ...options
        };

        this.rules = {};
        this.errors = {};
        this.isValid = true;

        this.init();
    }

    // Inicializar validador
    init() {
        this.setupEventListeners();
        this.parseValidationRules();
    }

    // Configurar event listeners
    setupEventListeners() {
        // Validação em blur
        if (this.options.validateOnBlur) {
            this.form.addEventListener('blur', (e) => {
                if (e.target.matches('input, select, textarea')) {
                    this.validateField(e.target);
                }
            }, true);
        }

        // Validação em input
        if (this.options.validateOnInput) {
            this.form.addEventListener('input', (e) => {
                if (e.target.matches('input, select, textarea')) {
                    this.validateField(e.target);
                }
            });
        }

        // Validação no submit
        this.form.addEventListener('submit', (e) => {
            if (!this.validate()) {
                e.preventDefault();
                this.showErrors();
            }
        });
    }

    // Parsear regras de validação dos atributos data-*
    parseValidationRules() {
        const inputs = this.form.querySelectorAll('input, select, textarea');

        inputs.forEach(input => {
            const rules = {};

            // Regras básicas
            if (input.hasAttribute('required')) {
                rules.required = true;
            }

            if (input.hasAttribute('minlength')) {
                rules.minlength = parseInt(input.getAttribute('minlength'));
            }

            if (input.hasAttribute('maxlength')) {
                rules.maxlength = parseInt(input.getAttribute('maxlength'));
            }

            if (input.hasAttribute('min')) {
                rules.min = input.getAttribute('min');
            }

            if (input.hasAttribute('max')) {
                rules.max = input.getAttribute('max');
            }

            if (input.hasAttribute('pattern')) {
                rules.pattern = input.getAttribute('pattern');
            }

            // Regras customizadas via data-attributes
            const customRules = input.dataset.validation;
            if (customRules) {
                try {
                    const parsedRules = JSON.parse(customRules);
                    Object.assign(rules, parsedRules);
                } catch (e) {
                    console.warn('[FormValidator] Erro ao parsear regras customizadas:', customRules);
                }
            }

            if (Object.keys(rules).length > 0) {
                this.rules[input.name || input.id] = rules;
            }
        });
    }

    // Adicionar regra customizada
    addRule(fieldName, ruleName, ruleValue) {
        if (!this.rules[fieldName]) {
            this.rules[fieldName] = {};
        }
        this.rules[fieldName][ruleName] = ruleValue;
    }

    // Remover regra
    removeRule(fieldName, ruleName) {
        if (this.rules[fieldName]) {
            delete this.rules[fieldName][ruleName];
        }
    }

    // Validar campo específico
    validateField(field) {
        const fieldName = field.name || field.id;
        const rules = this.rules[fieldName];

        if (!rules) return true;

        const value = field.value.trim();
        const errors = [];

        // Aplicar cada regra
        for (const [ruleName, ruleValue] of Object.entries(rules)) {
            const error = this.validateRule(ruleName, ruleValue, value, field);
            if (error) {
                errors.push(error);
            }
        }

        // Atualizar estado do campo
        this.errors[fieldName] = errors;

        if (this.options.showErrors) {
            this.updateFieldUI(field, errors);
        }

        return errors.length === 0;
    }

    // Validar regra específica
    validateRule(ruleName, ruleValue, value, field) {
        switch (ruleName) {
            case 'required':
                if (!value) return 'Este campo é obrigatório';
                break;

            case 'email':
                if (value && !this.isValidEmail(value)) return 'E-mail inválido';
                break;

            case 'phone':
                if (value && !this.isValidPhone(value)) return 'Telefone inválido';
                break;

            case 'cpf':
                if (value && !this.isValidCPF(value)) return 'CPF inválido';
                break;

            case 'minlength':
                if (value && value.length < ruleValue) return `Mínimo ${ruleValue} caracteres`;
                break;

            case 'maxlength':
                if (value && value.length > ruleValue) return `Máximo ${ruleValue} caracteres`;
                break;

            case 'min':
                if (value && parseFloat(value) < parseFloat(ruleValue)) return `Valor mínimo: ${ruleValue}`;
                break;

            case 'max':
                if (value && parseFloat(value) > parseFloat(ruleValue)) return `Valor máximo: ${ruleValue}`;
                break;

            case 'pattern':
                if (value && !new RegExp(ruleValue).test(value)) return 'Formato inválido';
                break;

            case 'equalTo':
                const otherField = this.form.querySelector(`[name="${ruleValue}"]`);
                if (otherField && value !== otherField.value) return 'Campos não coincidem';
                break;

            case 'date':
                if (value && !this.isValidDate(value)) return 'Data inválida';
                break;

            case 'future':
                if (value && !this.isFutureDate(value)) return 'Data deve ser futura';
                break;

            case 'custom':
                if (typeof ruleValue === 'function') {
                    return ruleValue(value, field);
                }
                break;
        }

        return null;
    }

    // Validar formulário completo
    validate() {
        this.errors = {};
        this.isValid = true;

        for (const fieldName in this.rules) {
            const field = this.form.querySelector(`[name="${fieldName}"], #${fieldName}`);
            if (field) {
                const isFieldValid = this.validateField(field);
                if (!isFieldValid) {
                    this.isValid = false;
                }
            }
        }

        if (!this.isValid && this.options.onError) {
            this.options.onError(this.errors);
        } else if (this.isValid && this.options.onSuccess) {
            this.options.onSuccess();
        }

        if (this.options.onValidate) {
            this.options.onValidate(this.isValid, this.errors);
        }

        return this.isValid;
    }

    // Atualizar UI do campo
    updateFieldUI(field, errors) {
        const fieldName = field.name || field.id;
        const container = field.closest('.form-group') || field.parentElement;

        // Remover classes anteriores
        container.classList.remove(this.options.errorClass, this.options.successClass);

        // Remover mensagens de erro anteriores
        const existingError = container.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }

        if (errors.length > 0) {
            // Campo com erro
            container.classList.add(this.options.errorClass);

            // Adicionar mensagem de erro
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error';
            errorDiv.textContent = errors[0]; // Mostrar primeiro erro
            container.appendChild(errorDiv);

        } else if (field.value.trim()) {
            // Campo válido com valor
            container.classList.add(this.options.successClass);
        }
    }

    // Mostrar todos os erros
    showErrors() {
        if (this.options.errorContainer) {
            const container = document.querySelector(this.options.errorContainer);
            if (container) {
                container.innerHTML = '';

                if (Object.keys(this.errors).length > 0) {
                    const errorList = document.createElement('ul');
                    errorList.className = 'error-list';

                    for (const [fieldName, fieldErrors] of Object.entries(this.errors)) {
                        if (fieldErrors.length > 0) {
                            const li = document.createElement('li');
                            li.textContent = `${this.getFieldLabel(fieldName)}: ${fieldErrors[0]}`;
                            errorList.appendChild(li);
                        }
                    }

                    container.appendChild(errorList);
                    container.style.display = 'block';
                } else {
                    container.style.display = 'none';
                }
            }
        }
    }

    // Obter label do campo
    getFieldLabel(fieldName) {
        const field = this.form.querySelector(`[name="${fieldName}"], #${fieldName}`);
        if (field) {
            const label = this.form.querySelector(`label[for="${field.id}"]`);
            if (label) return label.textContent.trim();

            const placeholder = field.placeholder;
            if (placeholder) return placeholder;
        }

        return fieldName.charAt(0).toUpperCase() + fieldName.slice(1);
    }

    // Utilitários de validação
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    isValidPhone(phone) {
        // Remove todos os caracteres não numéricos
        const cleanPhone = phone.replace(/\D/g, '');
        // Verifica se tem 10 ou 11 dígitos (com ou sem DDD)
        return cleanPhone.length >= 10 && cleanPhone.length <= 11;
    }

    isValidCPF(cpf) {
        cpf = cpf.replace(/\D/g, '');

        if (cpf.length !== 11) return false;

        // Verifica se todos os dígitos são iguais
        if (/^(\d)\1+$/.test(cpf)) return false;

        // Calcula primeiro dígito verificador
        let sum = 0;
        for (let i = 0; i < 9; i++) {
            sum += parseInt(cpf[i]) * (10 - i);
        }
        let digit = (sum * 10) % 11;
        if (digit === 10) digit = 0;
        if (digit !== parseInt(cpf[9])) return false;

        // Calcula segundo dígito verificador
        sum = 0;
        for (let i = 0; i < 10; i++) {
            sum += parseInt(cpf[i]) * (11 - i);
        }
        digit = (sum * 10) % 11;
        if (digit === 10) digit = 0;
        if (digit !== parseInt(cpf[10])) return false;

        return true;
    }

    isValidDate(dateStr) {
        const date = new Date(dateStr);
        return date instanceof Date && !isNaN(date);
    }

    isFutureDate(dateStr) {
        const date = new Date(dateStr);
        const now = new Date();
        now.setHours(0, 0, 0, 0);
        return date >= now;
    }

    // Resetar validação
    reset() {
        this.errors = {};
        this.isValid = true;

        // Limpar UI
        this.form.querySelectorAll('.form-group').forEach(group => {
            group.classList.remove(this.options.errorClass, this.options.successClass);
            const error = group.querySelector('.field-error');
            if (error) error.remove();
        });

        if (this.options.errorContainer) {
            const container = document.querySelector(this.options.errorContainer);
            if (container) {
                container.style.display = 'none';
            }
        }
    }

    // Destruir validador
    destroy() {
        // Remover event listeners (simplificado)
        this.form.removeEventListener('submit', this.handleSubmit);
        this.reset();
    }
}

// Validações específicas para o sistema de agendamentos
class AppointmentFormValidator extends FormValidator {
    constructor(form, options = {}) {
        super(form, options);

        // Adicionar regras específicas para agendamentos
        this.addAppointmentRules();
    }

    addAppointmentRules() {
        // Validação de data futura
        this.addRule('appointment_date', 'future', true);
        this.addRule('appointment_date', 'date', true);

        // Validação de horário comercial
        this.addRule('appointment_time', 'custom', (value) => {
            if (!value) return null;

            const [hours, minutes] = value.split(':').map(Number);
            const timeInMinutes = hours * 60 + minutes;

            // Horário comercial: 8:00 às 18:00
            const startTime = 8 * 60; // 8:00
            const endTime = 18 * 60; // 18:00

            if (timeInMinutes < startTime || timeInMinutes > endTime) {
                return 'Horário deve estar entre 08:00 e 18:00';
            }

            return null;
        });

        // Validação de conflito de horário
        this.addRule('appointment_time', 'custom', async (value, field) => {
            if (!value || !this.form.appointment_date?.value) return null;

            try {
                const date = this.form.appointment_date.value;
                const time = value;
                const professionalId = this.form.professional_id?.value;

                if (!professionalId) return null;

                // Verificar conflitos
                const conflict = await this.checkTimeConflict(date, time, professionalId);
                if (conflict) {
                    return 'Horário já ocupado para este profissional';
                }

                return null;
            } catch (error) {
                console.error('[AppointmentValidator] Erro ao verificar conflito:', error);
                return 'Erro ao validar horário';
            }
        });
    }

    async checkTimeConflict(date, time, professionalId) {
        try {
            // Simular verificação de conflito
            // Em produção, isso seria uma chamada para a API
            const dateTimeStr = `${date}T${time}:00`;
            const response = await api.request(`/appointments/check-conflict?datetime=${dateTimeStr}&professional_id=${professionalId}`);

            return response?.conflict || false;
        } catch (error) {
            console.error('[AppointmentValidator] Erro na verificação:', error);
            return false; // Em caso de erro, permitir agendamento
        }
    }
}

// Exportar para uso global
window.FormValidator = FormValidator;
window.AppointmentFormValidator = AppointmentFormValidator;