"""
Enums e constantes de banco de dados para o backend Aluvi.
Define enums de status e outras constantes de banco de dados.
"""

import enum
from typing import List


class AppointmentStatus(str, enum.Enum):
    """Enumeração de status de agendamento."""

    SCHEDULED = "agendado"        # Appointment created, waiting for execution
    CONFIRMED = "confirmado"     # Appointment confirmed (temporary for migration)
    CANCELLED = "cancelado"      # Appointment cancelled by client or salon
    COMPLETED = "concluido"      # Service completed successfully
    NO_SHOW = "nao_compareceu"   # Client did not show up

    @classmethod
    def active_statuses(cls) -> List['AppointmentStatus']:
        """Obter status que representam agendamentos ativos."""
        return [cls.SCHEDULED, cls.CONFIRMED]

    @classmethod
    def completed_statuses(cls) -> List['AppointmentStatus']:
        """Obter status que representam agendamentos concluídos."""
        return [cls.COMPLETED, cls.CANCELLED, cls.NO_SHOW]


class UserRole(str, enum.Enum):
    """Enumeração de papel de usuário."""

    ADMIN = "admin"      # System administrator
    OWNER = "dono"       # Salon owner
    CLIENT = "cliente"   # Salon client


class AuditAction(str, enum.Enum):
    """Tipos de ação de log de auditoria."""

    LOGIN = "login"
    LOGOUT = "logout"
    OWNER_CREATION = "criacao_dono"
    PASSWORD_CHANGE = "troca_senha"
    APPOINTMENT_CREATE = "criacao_agendamento"
    APPOINTMENT_UPDATE = "atualizacao_agendamento"
    APPOINTMENT_CANCEL = "cancelamento_agendamento"
    CLIENT_CREATE = "criacao_cliente"
    SERVICE_CREATE = "criacao_servico"
    PROFESSIONAL_CREATE = "criacao_profissional"


class SubscriptionStatus(str, enum.Enum):
    """Enumeração de status de assinatura."""

    ACTIVE = "ativo"
    EXPIRED = "expirado"
    CANCELLED = "cancelado"
    TRIAL = "trial"