"""
Database models for Aluvi backend.
Provides all SQLAlchemy model definitions and relationships.
"""

# Import base classes and enums first
from .base import Base, BaseModel, TimestampMixin, SoftDeleteMixin
from .enums import (
    AppointmentStatus,
    UserRole,
    AuditAction,
    SubscriptionStatus
)

# Import models
from .user import User
from .client import Client
from .service import Service
from .professional import Professional, ServiceProfessional
from .appointment import Appointment
from .business_hours import BusinessHours
from .audit import AuditLog, TokenBlacklist

# Legacy compatibility - import old names
Usuario = User
Cliente = Client
Servico = Service
Profissional = Professional
ServicoProfissional = ServiceProfessional
Agendamento = Appointment
HorarioFuncionamento = BusinessHours
StatusAgendamento = AppointmentStatus

# Export all models for easy importing
__all__ = [
    # Base classes
    'Base', 'BaseModel', 'TimestampMixin', 'SoftDeleteMixin',

    # Enums
    'AppointmentStatus', 'UserRole', 'AuditAction', 'SubscriptionStatus',

    # Models
    'User', 'Client', 'Service', 'Professional', 'ServiceProfessional', 'Appointment',
    'BusinessHours', 'AuditLog', 'TokenBlacklist',

    # Legacy names
    'Usuario', 'Cliente', 'Servico', 'Profissional', 'ServicoProfissional', 'Agendamento',
    'HorarioFuncionamento', 'StatusAgendamento'
]