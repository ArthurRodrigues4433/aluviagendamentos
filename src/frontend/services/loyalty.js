// Sistema Avançado de Fidelidade
class LoyaltySystem {
    constructor() {
        this.levels = {
            bronze: { min: 0, max: 99, name: 'Bronze', color: '#CD7F32', multiplier: 1 },
            silver: { min: 100, max: 299, name: 'Prata', color: '#C0C0C0', multiplier: 1.1 },
            gold: { min: 300, max: 599, name: 'Ouro', color: '#FFD700', multiplier: 1.2 },
            platinum: { min: 600, max: 999, name: 'Platina', color: '#E5E4E2', multiplier: 1.3 },
            diamond: { min: 1000, max: Infinity, name: 'Diamante', color: '#B9F2FF', multiplier: 1.5 }
        };

        this.benefits = {
            bronze: [
                'Acúmulo básico de pontos',
                'Acesso ao histórico de agendamentos'
            ],
            silver: [
                '10% de desconto em serviços selecionados',
                'Lembrete automático por SMS',
                'Prioridade na fila de espera'
            ],
            gold: [
                '15% de desconto em todos os serviços',
                'Serviço de cortesia a cada 10 agendamentos',
                'Acesso antecipado a novos serviços'
            ],
            platinum: [
                '20% de desconto em todos os serviços',
                'Convite para eventos exclusivos',
                'Atendimento personalizado',
                'Upgrade automático para serviços premium'
            ],
            diamond: [
                '25% de desconto em todos os serviços',
                'Serviços ilimitados de cortesia',
                'Concierge pessoal',
                'Benefícios vitalícios',
                'Acesso VIP a todos os serviços'
            ]
        };

        this.achievements = {
            first_appointment: { name: 'Primeiro Passo', description: 'Realizou seu primeiro agendamento', points: 10, icon: '🎯' },
            five_appointments: { name: 'Cliente Frequente', description: 'Completou 5 agendamentos', points: 50, icon: '🔥' },
            ten_appointments: { name: 'Cliente VIP', description: 'Completou 10 agendamentos', points: 100, icon: '👑' },
            no_show_free: { name: 'Cliente Pontual', description: 'Nunca faltou a um agendamento', points: 75, icon: '⏰' },
            early_bird: { name: 'Madrugador', description: 'Agendou 3x antes das 9h', points: 30, icon: '🌅' },
            loyal_customer: { name: 'Cliente Leal', description: 'Cliente há mais de 1 ano', points: 200, icon: '💎' }
        };
    }

    // Calcular nível baseado nos pontos
    getLevel(points) {
        for (const [levelKey, levelData] of Object.entries(this.levels)) {
            if (points >= levelData.min && points <= levelData.max) {
                return { ...levelData, key: levelKey };
            }
        }
        return this.levels.bronze;
    }

    // Calcular progresso para próximo nível
    getProgress(points) {
        const currentLevel = this.getLevel(points);
        const nextLevelKey = this.getNextLevel(currentLevel.key);

        if (!nextLevelKey) {
            return { current: points, target: points, percentage: 100, nextLevel: null };
        }

        const nextLevel = this.levels[nextLevelKey];
        const progress = points - currentLevel.min;
        const target = nextLevel.min - currentLevel.min;
        const percentage = Math.min((progress / target) * 100, 100);

        return {
            current: progress,
            target: target,
            percentage: percentage,
            nextLevel: nextLevel.name,
            pointsToNext: nextLevel.min - points
        };
    }

    // Obter próximo nível
    getNextLevel(currentLevelKey) {
        const levelKeys = Object.keys(this.levels);
        const currentIndex = levelKeys.indexOf(currentLevelKey);

        if (currentIndex < levelKeys.length - 1) {
            return levelKeys[currentIndex + 1];
        }

        return null;
    }

    // Calcular pontos ganhos por serviço
    calculatePoints(service, level) {
        const basePoints = service.pontos_fidelidade || 0;
        const multiplier = level.multiplier || 1;

        return Math.round(basePoints * multiplier);
    }

    // Verificar conquistas desbloqueadas
    checkAchievements(clientData, appointments) {
        const unlocked = [];
        const achievements = { ...this.achievements };

        // Primeiro agendamento
        if (appointments.length >= 1) {
            unlocked.push(achievements.first_appointment);
        }

        // 5 agendamentos
        if (appointments.length >= 5) {
            unlocked.push(achievements.five_appointments);
        }

        // 10 agendamentos
        if (appointments.length >= 10) {
            unlocked.push(achievements.ten_appointments);
        }

        // Nunca faltou
        const completedAppointments = appointments.filter(apt => apt.status === 'concluido').length;
        const noShowAppointments = appointments.filter(apt => apt.status === 'nao_compareceu').length;

        if (completedAppointments > 0 && noShowAppointments === 0) {
            unlocked.push(achievements.no_show_free);
        }

        // Madrugador (agendamentos antes das 9h)
        const earlyAppointments = appointments.filter(apt => {
            const hour = new Date(apt.data_hora).getHours();
            return hour < 9;
        }).length;

        if (earlyAppointments >= 3) {
            unlocked.push(achievements.early_bird);
        }

        // Cliente leal (mais de 1 ano)
        if (clientData && clientData.created_at) {
            const registrationDate = new Date(clientData.created_at);
            const oneYearAgo = new Date();
            oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);

            if (registrationDate <= oneYearAgo) {
                unlocked.push(achievements.loyal_customer);
            }
        }

        return unlocked;
    }

    // Calcular valor do desconto baseado no nível
    getDiscountPercentage(level) {
        const discounts = {
            bronze: 0,
            silver: 10,
            gold: 15,
            platinum: 20,
            diamond: 25
        };

        return discounts[level] || 0;
    }

    // Verificar elegibilidade para benefícios
    getEligibleBenefits(points, appointments) {
        const level = this.getLevel(points);
        const achievements = this.checkAchievements(null, appointments);

        return {
            level: level,
            benefits: this.benefits[level.key] || [],
            achievements: achievements,
            discountPercentage: this.getDiscountPercentage(level.key)
        };
    }

    // Calcular pontos necessários para benefício específico
    getPointsForBenefit(benefitType) {
        const benefitRequirements = {
            discount_10: 100,
            discount_15: 300,
            discount_20: 600,
            free_service: 300,
            vip_access: 600,
            lifetime_benefits: 1000
        };

        return benefitRequirements[benefitType] || 0;
    }

    // Sistema de gamificação
    getGamificationData(points, appointments) {
        const level = this.getLevel(points);
        const progress = this.getProgress(points);
        const achievements = this.checkAchievements(null, appointments);

        // Calcular streak (sequência de agendamentos consecutivos)
        const streak = this.calculateStreak(appointments);

        // Próximas conquistas disponíveis
        const nextAchievements = this.getNextAchievements(appointments);

        return {
            level: level,
            progress: progress,
            achievements: achievements,
            streak: streak,
            nextAchievements: nextAchievements,
            gamificationScore: this.calculateGamificationScore(points, appointments, achievements)
        };
    }

    // Calcular sequência de agendamentos
    calculateStreak(appointments) {
        if (appointments.length === 0) return 0;

        // Ordenar por data
        const sortedAppointments = appointments
            .filter(apt => apt.status === 'concluido')
            .sort((a, b) => new Date(a.data_hora) - new Date(b.data_hora));

        let streak = 1;
        let maxStreak = 1;

        for (let i = 1; i < sortedAppointments.length; i++) {
            const prevDate = new Date(sortedAppointments[i - 1].data_hora);
            const currDate = new Date(sortedAppointments[i].data_hora);

            // Verificar se são consecutivos (considerando meses)
            const diffTime = Math.abs(currDate - prevDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays <= 30) { // Dentro de 30 dias
                streak++;
                maxStreak = Math.max(maxStreak, streak);
            } else {
                streak = 1;
            }
        }

        return maxStreak;
    }

    // Próximas conquistas disponíveis
    getNextAchievements(appointments) {
        const completedCount = appointments.filter(apt => apt.status === 'concluido').length;
        const nextAchievements = [];

        if (completedCount < 5) {
            nextAchievements.push({
                ...this.achievements.five_appointments,
                progress: completedCount,
                target: 5
            });
        }

        if (completedCount < 10) {
            nextAchievements.push({
                ...this.achievements.ten_appointments,
                progress: completedCount,
                target: 10
            });
        }

        return nextAchievements.slice(0, 3); // Máximo 3 próximas
    }

    // Calcular score de gamificação
    calculateGamificationScore(points, appointments, achievements) {
        let score = points;

        // Bonus por conquistas
        score += achievements.length * 50;

        // Bonus por streak
        const streak = this.calculateStreak(appointments);
        score += streak * 10;

        // Bonus por nível
        const level = this.getLevel(points);
        const levelBonus = Object.keys(this.levels).indexOf(level.key) * 100;
        score += levelBonus;

        return score;
    }

    // Previsão de pontos futuros
    predictFuturePoints(currentPoints, monthlyAppointments, avgPointsPerAppointment) {
        const months = [1, 3, 6, 12];
        const predictions = {};

        months.forEach(months => {
            const futurePoints = currentPoints + (monthlyAppointments * avgPointsPerAppointment * months);
            const futureLevel = this.getLevel(futurePoints);

            predictions[`${months}m`] = {
                points: futurePoints,
                level: futureLevel.name,
                benefits: this.benefits[futureLevel.key] || []
            };
        });

        return predictions;
    }
}

// Classe para gerenciar fidelidade do cliente
class ClientLoyalty {
    constructor(clientData, appointments = []) {
        this.clientData = clientData;
        this.appointments = appointments;
        this.loyaltySystem = new LoyaltySystem();
    }

    // Obter status completo de fidelidade
    getStatus() {
        const points = this.clientData.pontos_fidelidade || 0;
        const level = this.loyaltySystem.getLevel(points);
        const progress = this.loyaltySystem.getProgress(points);
        const gamification = this.loyaltySystem.getGamificationData(points, this.appointments);

        return {
            points: points,
            level: level,
            progress: progress,
            gamification: gamification,
            benefits: this.loyaltySystem.getEligibleBenefits(points, this.appointments),
            predictions: this.loyaltySystem.predictFuturePoints(
                points,
                this.calculateMonthlyAverage(),
                this.calculateAvgPointsPerAppointment()
            )
        };
    }

    // Calcular média mensal de agendamentos
    calculateMonthlyAverage() {
        if (this.appointments.length === 0) return 0;

        const firstAppointment = new Date(Math.min(...this.appointments.map(apt => new Date(apt.data_hora))));
        const lastAppointment = new Date(Math.max(...this.appointments.map(apt => new Date(apt.data_hora))));

        const monthsDiff = (lastAppointment.getFullYear() - firstAppointment.getFullYear()) * 12 +
                          (lastAppointment.getMonth() - firstAppointment.getMonth()) + 1;

        return Math.round((this.appointments.length / monthsDiff) * 10) / 10;
    }

    // Calcular média de pontos por agendamento
    calculateAvgPointsPerAppointment() {
        if (this.appointments.length === 0) return 0;

        const totalPoints = this.appointments.reduce((sum, apt) => {
            // Simular cálculo de pontos baseado no serviço
            return sum + (apt.servico?.pontos_fidelidade || 0);
        }, 0);

        return Math.round(totalPoints / this.appointments.length);
    }

    // Verificar se pode resgatar benefício
    canRedeemBenefit(benefitType) {
        const points = this.clientData.pontos_fidelidade || 0;
        const requiredPoints = this.loyaltySystem.getPointsForBenefit(benefitType);

        return points >= requiredPoints;
    }

    // Resgatar benefício
    redeemBenefit(benefitType) {
        if (!this.canRedeemBenefit(benefitType)) {
            throw new Error('Pontos insuficientes para resgatar este benefício');
        }

        const cost = this.loyaltySystem.getPointsForBenefit(benefitType);
        this.clientData.pontos_fidelidade -= cost;

        return {
            benefit: benefitType,
            cost: cost,
            remainingPoints: this.clientData.pontos_fidelidade
        };
    }
}

// Exportar para uso global
window.LoyaltySystem = LoyaltySystem;
window.ClientLoyalty = ClientLoyalty;