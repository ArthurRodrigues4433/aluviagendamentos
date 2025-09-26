// Componente DatePicker - Seletor de data customizado
class DatePicker {
    constructor(input, options = {}) {
        this.input = input;
        this.options = {
            format: 'DD/MM/YYYY',
            locale: 'pt-BR',
            minDate: null,
            maxDate: null,
            disabledDates: [],
            highlightedDates: [],
            position: 'bottom', // 'bottom', 'top', 'auto'
            onSelect: null,
            onOpen: null,
            onClose: null,
            showTime: false,
            timeFormat: 'HH:mm',
            ...options
        };

        this.calendar = null;
        this.popup = null;
        this.isOpen = false;
        this.selectedDate = null;

        this.init();
    }

    // Inicializar date picker
    init() {
        this.createPopup();
        this.setupEventListeners();
        this.parseInitialValue();
    }

    // Criar popup do calendário
    createPopup() {
        // Criar container do popup
        this.popup = document.createElement('div');
        this.popup.className = 'date-picker-popup';
        this.popup.style.display = 'none';
        this.popup.style.position = 'absolute';
        this.popup.style.zIndex = '9999';

        // Adicionar ao body
        document.body.appendChild(this.popup);

        // Criar instância do calendário
        this.calendar = new Calendar({
            minDate: this.options.minDate,
            maxDate: this.options.maxDate,
            disabledDates: this.options.disabledDates,
            highlightedDates: this.options.highlightedDates,
            onDateSelect: (date) => this.onDateSelected(date)
        });
    }

    // Configurar event listeners
    setupEventListeners() {
        // Click no input para abrir/fechar
        this.input.addEventListener('click', () => this.toggle());
        this.input.addEventListener('focus', () => this.open());

        // Fechar ao clicar fora
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.popup.contains(e.target)) {
                this.close();
            }
        });

        // Suporte a teclado
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.close();
            } else if (e.key === 'Enter' && this.isOpen) {
                e.preventDefault();
                this.close();
            }
        });

        // Prevenir fechamento ao clicar no popup
        this.popup.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    // Parsear valor inicial do input
    parseInitialValue() {
        const value = this.input.value.trim();
        if (value) {
            try {
                this.selectedDate = this.parseDate(value);
                if (this.selectedDate) {
                    this.calendar.setSelectedDate(this.selectedDate);
                }
            } catch (error) {
                console.warn('[DatePicker] Erro ao parsear data inicial:', value);
            }
        }
    }

    // Abrir date picker
    open() {
        if (this.isOpen) return;

        this.positionPopup();
        this.popup.style.display = 'block';
        this.isOpen = true;

        // Renderizar calendário
        this.calendar.render(this.popup);

        // Ir para mês da data selecionada ou atual
        if (this.selectedDate) {
            this.calendar.goToDate(this.selectedDate);
        }

        if (this.options.onOpen) {
            this.options.onOpen();
        }

        // Animação de entrada
        this.animateIn();
    }

    // Fechar date picker
    close() {
        if (!this.isOpen) return;

        this.isOpen = false;
        this.animateOut();

        setTimeout(() => {
            this.popup.style.display = 'none';
        }, 200); // Tempo da animação

        if (this.options.onClose) {
            this.options.onClose();
        }
    }

    // Alternar aberto/fechado
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    // Posicionar popup
    positionPopup() {
        const inputRect = this.input.getBoundingClientRect();
        const popupRect = this.popup.getBoundingClientRect();

        let top, left;

        switch (this.options.position) {
            case 'top':
                top = inputRect.top - popupRect.height - 10;
                left = inputRect.left;
                break;
            case 'auto':
                const spaceBelow = window.innerHeight - inputRect.bottom;
                const spaceAbove = inputRect.top;

                if (spaceBelow >= 200 || spaceBelow > spaceAbove) {
                    // Posicionar abaixo
                    top = inputRect.bottom + 5;
                    left = inputRect.left;
                } else {
                    // Posicionar acima
                    top = inputRect.top - 200 - 5;
                    left = inputRect.left;
                }
                break;
            default: // 'bottom'
                top = inputRect.bottom + 5;
                left = inputRect.left;
        }

        // Ajustar para não sair da tela
        const maxLeft = window.innerWidth - popupRect.width - 10;
        left = Math.max(10, Math.min(left, maxLeft));

        this.popup.style.top = `${top}px`;
        this.popup.style.left = `${left}px`;
    }

    // Quando uma data é selecionada
    onDateSelected(date) {
        this.selectedDate = date;
        this.setInputValue(date);
        this.close();

        if (this.options.onSelect) {
            this.options.onSelect(date);
        }
    }

    // Definir valor do input
    setInputValue(date) {
        const formatted = this.formatDate(date);
        this.input.value = formatted;
    }

    // Formatar data
    formatDate(date) {
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();

        return this.options.format
            .replace('DD', day)
            .replace('MM', month)
            .replace('YYYY', year);
    }

    // Parsear data
    parseDate(dateStr) {
        // Suporte a diferentes formatos
        const formats = [
            /^(\d{2})\/(\d{2})\/(\d{4})$/, // DD/MM/YYYY
            /^(\d{4})-(\d{2})-(\d{2})$/, // YYYY-MM-DD
            /^(\d{2})\.(\d{2})\.(\d{4})$/ // DD.MM.YYYY
        ];

        for (const format of formats) {
            const match = dateStr.match(format);
            if (match) {
                const [, part1, part2, part3] = match;

                if (dateStr.includes('/')) {
                    // DD/MM/YYYY
                    return new Date(part3, part2 - 1, part1);
                } else if (dateStr.includes('-')) {
                    // YYYY-MM-DD
                    return new Date(part1, part2 - 1, part3);
                } else if (dateStr.includes('.')) {
                    // DD.MM.YYYY
                    return new Date(part3, part2 - 1, part1);
                }
            }
        }

        // Fallback: tentar parse nativo
        const date = new Date(dateStr);
        return isNaN(date.getTime()) ? null : date;
    }

    // Definir data selecionada
    setDate(date) {
        this.selectedDate = date;
        this.calendar.setSelectedDate(date);
        this.setInputValue(date);
    }

    // Obter data selecionada
    getDate() {
        return this.selectedDate;
    }

    // Definir datas desabilitadas
    setDisabledDates(dates) {
        this.options.disabledDates = dates;
        if (this.calendar) {
            this.calendar.setDisabledDates(dates);
        }
    }

    // Definir datas destacadas
    setHighlightedDates(dates) {
        this.options.highlightedDates = dates;
        if (this.calendar) {
            this.calendar.setHighlightedDates(dates);
        }
    }

    // Animações
    animateIn() {
        this.popup.style.opacity = '0';
        this.popup.style.transform = 'translateY(-10px) scale(0.95)';

        requestAnimationFrame(() => {
            this.popup.style.transition = 'all 0.2s ease-out';
            this.popup.style.opacity = '1';
            this.popup.style.transform = 'translateY(0) scale(1)';
        });
    }

    animateOut() {
        this.popup.style.opacity = '0';
        this.popup.style.transform = 'translateY(-10px) scale(0.95)';
    }

    // Destruir componente
    destroy() {
        this.close();

        if (this.popup && this.popup.parentNode) {
            this.popup.parentNode.removeChild(this.popup);
        }

        if (this.calendar) {
            this.calendar.destroy();
        }

        // Limpar referências
        this.input = null;
        this.popup = null;
        this.calendar = null;
    }
}

// DatePicker com suporte a horário
class DateTimePicker extends DatePicker {
    constructor(input, options = {}) {
        super(input, {
            showTime: true,
            ...options
        });

        this.selectedTime = null;
        this.timeInput = null;
    }

    // Sobrescrever criação do popup para incluir seletor de horário
    createPopup() {
        super.createPopup();

        // Adicionar seção de horário
        const timeSection = document.createElement('div');
        timeSection.className = 'time-section';
        timeSection.innerHTML = `
            <div class="time-input-group">
                <label for="time-input">Horário:</label>
                <input type="time" id="time-input" class="time-input">
            </div>
            <div class="time-buttons">
                <button class="btn btn-sm btn-outline time-preset" data-time="09:00">9:00</button>
                <button class="btn btn-sm btn-outline time-preset" data-time="14:00">14:00</button>
                <button class="btn btn-sm btn-outline time-preset" data-time="16:30">16:30</button>
            </div>
        `;

        this.popup.appendChild(timeSection);
        this.timeInput = timeSection.querySelector('#time-input');

        // Configurar event listeners para horário
        this.setupTimeEventListeners();
    }

    // Configurar event listeners para horário
    setupTimeEventListeners() {
        // Input de horário
        this.timeInput.addEventListener('change', () => {
            this.selectedTime = this.timeInput.value;
        });

        // Botões de horário pré-definido
        this.popup.querySelectorAll('.time-preset').forEach(btn => {
            btn.addEventListener('click', () => {
                const time = btn.dataset.time;
                this.timeInput.value = time;
                this.selectedTime = time;

                // Remover seleção anterior
                this.popup.querySelectorAll('.time-preset').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    }

    // Sobrescrever seleção de data para incluir horário
    onDateSelected(date) {
        // Não fechar automaticamente se tem horário para selecionar
        if (this.options.showTime) {
            this.selectedDate = date;
            // Focar no input de horário
            setTimeout(() => this.timeInput.focus(), 100);
        } else {
            super.onDateSelected(date);
        }
    }

    // Confirmar seleção (usado quando tem horário)
    confirmSelection() {
        if (!this.selectedDate) return;

        if (this.options.showTime && this.selectedTime) {
            // Combinar data e horário
            const [hours, minutes] = this.selectedTime.split(':');
            const dateTime = new Date(this.selectedDate);
            dateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);

            this.setInputValue(dateTime);
            this.close();

            if (this.options.onSelect) {
                this.options.onSelect(dateTime);
            }
        } else {
            super.onDateSelected(this.selectedDate);
        }
    }

    // Parsear valor inicial incluindo horário
    parseInitialValue() {
        const value = this.input.value.trim();
        if (value) {
            try {
                // Tentar parsear como datetime
                const dateTime = new Date(value);
                if (!isNaN(dateTime.getTime())) {
                    this.selectedDate = dateTime;
                    this.selectedTime = dateTime.toTimeString().slice(0, 5);
                    this.calendar.setSelectedDate(dateTime);
                    return;
                }

                // Tentar parsear apenas data
                this.selectedDate = this.parseDate(value);
                if (this.selectedDate) {
                    this.calendar.setSelectedDate(this.selectedDate);
                }
            } catch (error) {
                console.warn('[DateTimePicker] Erro ao parsear data/hora inicial:', value);
            }
        }
    }

    // Formatar data e hora
    formatDate(date) {
        const dateStr = super.formatDate(date);
        if (this.options.showTime) {
            const timeStr = date.toTimeString().slice(0, 5);
            return `${dateStr} ${timeStr}`;
        }
        return dateStr;
    }
}

// Função utilitária para inicializar date pickers
function initDatePickers(selector = '.date-picker', options = {}) {
    const inputs = document.querySelectorAll(selector);
    const pickers = [];

    inputs.forEach(input => {
        if (!input.dataset.datepickerInitialized) {
            const picker = input.type === 'datetime-local' ?
                new DateTimePicker(input, options) :
                new DatePicker(input, options);

            pickers.push(picker);
            input.dataset.datepickerInitialized = 'true';
        }
    });

    return pickers;
}

// Exportar para uso global
window.DatePicker = DatePicker;
window.DateTimePicker = DateTimePicker;
window.initDatePickers = initDatePickers;