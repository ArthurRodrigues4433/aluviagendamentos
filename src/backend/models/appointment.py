"""
Definições de modelo de agendamento para o backend Aluvi.
Gerencia agendamentos de serviços e seu ciclo de vida.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, Enum
from sqlalchemy.orm import relationship

from .base import BaseModel, TimestampMixin
from .enums import AppointmentStatus


class Appointment(BaseModel, TimestampMixin):
    """
    Modelo de agendamento representando reservas de serviços.

    Vincula clientes, serviços, profissionais e salões.
    Rastreia status do agendamento e ciclo de vida.
    """

    __tablename__ = "agendamentos"

    # Relationships
    client_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)  # Nullable for anonymous clients
    service_id = Column(Integer, ForeignKey("servicos.id"), nullable=False)
    professional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)
    salon_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Detalhes do agendamento
    appointment_datetime = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)

    # Legacy compatibility properties
    @property
    def valor(self):  # type: ignore
        return self.price

    @valor.setter
    def valor(self, value):  # type: ignore
        self.price = value

    @property
    def cliente_id(self):  # type: ignore
        return self.client_id

    @cliente_id.setter
    def cliente_id(self, value):  # type: ignore
        self.client_id = value

    @property
    def servico_id(self):  # type: ignore
        return self.service_id

    @servico_id.setter
    def servico_id(self, value):  # type: ignore
        self.service_id = value

    @property
    def profissional_id(self):  # type: ignore
        return self.professional_id

    @profissional_id.setter
    def profissional_id(self, value):  # type: ignore
        self.professional_id = value

    @property
    def data_hora(self):  # type: ignore
        return self.appointment_datetime

    @data_hora.setter
    def data_hora(self, value):  # type: ignore
        self.appointment_datetime = value

    # Relationships
    client = relationship("Client", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    professional = relationship("Professional", back_populates="appointments")
    salon = relationship("User", primaryjoin="User.id == Appointment.salon_id", back_populates="appointments")

    @property
    def is_active(self) -> bool:
        """Verificar se o agendamento está em status ativo."""
        return self.status in AppointmentStatus.active_statuses()

    @property
    def is_completed(self) -> bool:
        """Verificar se o agendamento está concluído."""
        return self.status in AppointmentStatus.completed_statuses()

    def can_be_cancelled(self) -> bool:
        """Verificar se o agendamento ainda pode ser cancelado."""
        return self.status == AppointmentStatus.SCHEDULED  # type: ignore

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, client_id={self.client_id}, service_id={self.service_id}, status={self.status})>"