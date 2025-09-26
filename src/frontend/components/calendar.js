// Componente Calendar - Calendário interativo avançado
class Calendar {
    constructor(options = {}) {
        this.options = {
            minDate: new Date(),
            maxDate: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000), // 90 dias à frente
            selectedDate: null,
            disabledDates: [],
            highlightedDates: [],
            onDateSelect: null,
            onMonthChange: null,
            showWeekends: true,
            locale: 'pt-BR',
            firstDayOfWeek: 0, // 0 = Domingo
            ...options
        };

        this.currentDate = new Date();
        this.selectedDate = this.options.selectedDate;
        this.element = null;
        this.dateButtons = new Map();
    }

    // Renderizar calendário
    render(container) {
        if (!container) return;

        const calendarHTML = `
            <div class="calendar">
                <div class="calendar-header">
                    <button class="calendar-nav prev-month" aria-label="Mês anterior">
                        <span class="mobile-hide">‹</span>
                        <span class="mobile-show">←</span>
                    </button>
                    <h3 class="calendar-title"></h3>
                    <button class="calendar-nav next-month" aria-label="Próximo mês">
                        <span class="mobile-hide">›</span>
                        <span class="mobile-show">→</span>
                    </button>
                </div>
                <div class="calendar-weekdays"></div>
                <div class="calendar-grid"></div>
            </div>
        `;

        container.innerHTML = calendarHTML;
        this.element = container.querySelector('.calendar');

        this.attachEventListeners();
        this.renderCalendar();

        return this.element;
    }

    // Renderizar calendário para o mês atual
    renderCalendar() {
        this.renderHeader();
        this.renderWeekdays();
        this.renderDays();
    }

    // Renderizar cabeçalho
    renderHeader() {
        const title = this.element.querySelector('.calendar-title');
        const monthName = this.currentDate.toLocaleDateString(this.options.locale, {
            month: 'long',
            year: 'numeric'
        });

        title.textContent = monthName.charAt(0).toUpperCase() + monthName.slice(1);
    }

    // Renderizar dias da semana
    renderWeekdays() {
        const weekdaysContainer = this.element.querySelector('.calendar-weekdays');
        const weekdays = [];

        // Nomes dos dias da semana
        const weekdayNames = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

        for (let i = 0; i < 7; i++) {
            const dayIndex = (i + this.options.firstDayOfWeek) % 7;
            const isWeekend = dayIndex === 0 || dayIndex === 6;

            weekdays.push(`
                <div class="calendar-weekday ${isWeekend ? 'weekend' : ''}">
                    <span class="mobile-hide">${weekdayNames[dayIndex]}</span>
                    <span class="mobile-show">${weekdayNames[dayIndex].charAt(0)}</span>
                </div>
            `);
        }

        weekdaysContainer.innerHTML = weekdays.join('');
    }

    // Renderizar dias do mês
    renderDays() {
        const grid = this.element.querySelector('.calendar-grid');
        const days = [];

        // Data do primeiro dia do mês
        const firstDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
        const lastDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
        const startDate = new Date(firstDay);

        // Ajustar para começar na primeira coluna correta
        const startOffset = (firstDay.getDay() - this.options.firstDayOfWeek + 7) % 7;
        startDate.setDate(startDate.getDate() - startOffset);

        // Limpar mapa de botões
        this.dateButtons.clear();

        // Gerar 42 dias (6 semanas)
        for (let i = 0; i < 42; i++) {
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);

            const isCurrentMonth = currentDate.getMonth() === this.currentDate.getMonth();
            const isToday = this.isToday(currentDate);
            const isSelected = this.isSelected(currentDate);
            const isDisabled = this.isDisabled(currentDate);
            const isHighlighted = this.isHighlighted(currentDate);
            const isPast = currentDate < this.options.minDate;

            const classes = [
                'calendar-day',
                isCurrentMonth ? '' : 'other-month',
                isToday ? 'today' : '',
                isSelected ? 'selected' : '',
                isDisabled || isPast ? 'disabled' : '',
                isHighlighted ? 'highlighted' : ''
            ].filter(cls => cls).join(' ');

            const dayHTML = `
                <button class="${classes}"
                        data-date="${currentDate.toISOString().split('T')[0]}"
                        ${isDisabled || isPast ? 'disabled' : ''}
                        aria-label="${currentDate.toLocaleDateString(this.options.locale, {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                        })}">
                    ${currentDate.getDate()}
                </button>
            `;

            days.push(dayHTML);
        }

        grid.innerHTML = days.join('');

        // Armazenar referências dos botões
        grid.querySelectorAll('.calendar-day').forEach(button => {
            const dateStr = button.dataset.date;
            this.dateButtons.set(dateStr, button);
        });
    }

    // Anexar event listeners
    attachEventListeners() {
        // Navegação de mês
        const prevBtn = this.element.querySelector('.prev-month');
        const nextBtn = this.element.querySelector('.next-month');

        prevBtn.addEventListener('click', () => this.navigateMonth(-1));
        nextBtn.addEventListener('click', () => this.navigateMonth(1));

        // Cliques nos dias
        this.element.addEventListener('click', (e) => {
            if (e.target.classList.contains('calendar-day') && !e.target.disabled) {
                const dateStr = e.target.dataset.date;
                this.selectDate(dateStr);
            }
        });
    }

    // Navegar entre meses
    navigateMonth(delta) {
        this.currentDate.setMonth(this.currentDate.getMonth() + delta);
        this.renderCalendar();

        if (this.options.onMonthChange) {
            this.options.onMonthChange(this.currentDate);
        }
    }

    // Selecionar data
    selectDate(dateStr) {
        const date = new Date(dateStr + 'T00:00:00');

        if (this.isDisabled(date) || date < this.options.minDate) {
            return;
        }

        // Remover seleção anterior
        if (this.selectedDate) {
            const prevButton = this.dateButtons.get(this.selectedDate.toISOString().split('T')[0]);
            if (prevButton) {
                prevButton.classList.remove('selected');
            }
        }

        // Definir nova seleção
        this.selectedDate = date;
        const currentButton = this.dateButtons.get(dateStr);
        if (currentButton) {
            currentButton.classList.add('selected');
        }

        if (this.options.onDateSelect) {
            this.options.onDateSelect(date);
        }
    }

    // Verificar se é hoje
    isToday(date) {
        const today = new Date();
        return date.toDateString() === today.toDateString();
    }

    // Verificar se está selecionada
    isSelected(date) {
        return this.selectedDate && date.toDateString() === this.selectedDate.toDateString();
    }

    // Verificar se está desabilitada
    isDisabled(date) {
        return this.options.disabledDates.some(disabledDate =>
            date.toDateString() === disabledDate.toDateString()
        );
    }

    // Verificar se está destacada
    isHighlighted(date) {
        return this.options.highlightedDates.some(highlightedDate =>
            date.toDateString() === highlightedDate.toDateString()
        );
    }

    // Métodos públicos para controle externo
    setSelectedDate(date) {
        this.selectedDate = date;
        this.renderCalendar();
    }

    setDisabledDates(dates) {
        this.options.disabledDates = dates;
        this.renderCalendar();
    }

    setHighlightedDates(dates) {
        this.options.highlightedDates = dates;
        this.renderCalendar();
    }

    goToDate(date) {
        this.currentDate = new Date(date.getFullYear(), date.getMonth(), 1);
        this.renderCalendar();
    }

    goToToday() {
        this.goToDate(new Date());
    }

    // Destruir componente
    destroy() {
        if (this.element) {
            this.element.remove();
        }
        this.element = null;
        this.dateButtons.clear();
    }
}

// Calendário com funcionalidade de time slots
class TimeSlotCalendar extends Calendar {
    constructor(options = {}) {
        super({
            ...options,
            onDateSelect: (date) => this.onDateSelected(date)
        });

        this.timeSlots = [];
        this.selectedTimeSlot = null;
        this.onTimeSlotSelect = options.onTimeSlotSelect || null;
    }

    // Quando uma data é selecionada, carregar horários disponíveis
    async onDateSelected(date) {
        if (this.options.onDateSelect) {
            this.options.onDateSelect(date);
        }

        // Carregar horários disponíveis para a data
        await this.loadTimeSlots(date);
    }

    // Carregar horários disponíveis
    async loadTimeSlots(date) {
        try {
            const dateStr = date.toISOString().split('T')[0];

            // Simular chamada para API (ajuste conforme necessário)
            const response = await api.request(`/appointments/available-slots?date=${dateStr}&service_id=${this.options.serviceId || 1}&professional_id=${this.options.professionalId || 1}`);

            if (response && Array.isArray(response)) {
                this.timeSlots = response;
                this.renderTimeSlots();
            } else {
                this.timeSlots = this.generateDefaultTimeSlots();
                this.renderTimeSlots();
            }

        } catch (error) {
            console.error('[TimeSlotCalendar] Erro ao carregar horários:', error);
            this.timeSlots = this.generateDefaultTimeSlots();
            this.renderTimeSlots();
        }
    }

    // Gerar horários padrão (fallback)
    generateDefaultTimeSlots() {
        const slots = [];
        const startHour = 8;
        const endHour = 18;

        for (let hour = startHour; hour < endHour; hour++) {
            for (let minute of [0, 30]) {
                const timeStr = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
                slots.push({
                    time: timeStr,
                    available: Math.random() > 0.3 // 70% de chance de disponível
                });
            }
        }

        return slots;
    }

    // Renderizar time slots
    renderTimeSlots() {
        if (!this.element) return;

        let timeSlotsHTML = '<div class="time-slots-section"><h4>Horários Disponíveis</h4>';

        if (this.timeSlots.length === 0) {
            timeSlotsHTML += '<p class="no-slots">Nenhum horário disponível para esta data.</p>';
        } else {
            timeSlotsHTML += '<div class="time-slots-grid">';

            this.timeSlots.forEach(slot => {
                const isSelected = this.selectedTimeSlot === slot.time;
                const isAvailable = slot.available;

                timeSlotsHTML += `
                    <button class="time-slot ${isSelected ? 'selected' : ''} ${!isAvailable ? 'disabled' : ''}"
                            data-time="${slot.time}"
                            ${!isAvailable ? 'disabled' : ''}
                            onclick="this.closest('.calendar')._calendar.selectTimeSlot('${slot.time}')">
                        ${slot.time}
                    </button>
                `;
            });

            timeSlotsHTML += '</div>';
        }

        timeSlotsHTML += '</div>';

        // Adicionar após o grid de dias
        const existingSlots = this.element.querySelector('.time-slots-section');
        if (existingSlots) {
            existingSlots.remove();
        }

        this.element.querySelector('.calendar-grid').insertAdjacentHTML('afterend', timeSlotsHTML);
    }

    // Selecionar time slot
    selectTimeSlot(timeStr) {
        this.selectedTimeSlot = timeStr;

        // Atualizar UI
        this.renderTimeSlots();

        if (this.onTimeSlotSelect) {
            this.onTimeSlotSelect(timeStr);
        }
    }

    // Obter data e hora selecionadas
    getSelectedDateTime() {
        if (!this.selectedDate || !this.selectedTimeSlot) return null;

        const [hours, minutes] = this.selectedTimeSlot.split(':');
        const dateTime = new Date(this.selectedDate);
        dateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);

        return dateTime;
    }
}

// Exportar para uso global
window.Calendar = Calendar;
window.TimeSlotCalendar = TimeSlotCalendar;