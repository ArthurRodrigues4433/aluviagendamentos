"""
Definições de modelo de horário comercial para o backend Aluvi.
Gerencia configuração de horário de funcionamento do salão.
"""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import Base


class BusinessHours(Base):
    """
    Modelo de horário comercial para horários de funcionamento do salão.

    Armazena horários de abertura e fechamento para cada dia da semana.
    """

    __tablename__ = "horarios_funcionamento"

    # Foreign key to salon
    salon_id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)

    # Monday
    monday_open = Column(String(5), nullable=True)   # HH:MM format
    monday_close = Column(String(5), nullable=True)

    # Tuesday
    tuesday_open = Column(String(5), nullable=True)
    tuesday_close = Column(String(5), nullable=True)

    # Wednesday
    wednesday_open = Column(String(5), nullable=True)
    wednesday_close = Column(String(5), nullable=True)

    # Thursday
    thursday_open = Column(String(5), nullable=True)
    thursday_close = Column(String(5), nullable=True)

    # Friday
    friday_open = Column(String(5), nullable=True)
    friday_close = Column(String(5), nullable=True)

    # Saturday
    saturday_open = Column(String(5), nullable=True)
    saturday_close = Column(String(5), nullable=True)

    # Sunday
    sunday_open = Column(String(5), nullable=True)
    sunday_close = Column(String(5), nullable=True)

    # Relationship
    salon = relationship("User", back_populates="business_hours")

    def get_hours_for_day(self, day_name: str) -> tuple:
        """Obter horários de abertura e fechamento para um dia específico."""
        day_lower = day_name.lower()
        open_attr = f"{day_lower}_open"
        close_attr = f"{day_lower}_close"

        return getattr(self, open_attr), getattr(self, close_attr)

    def __repr__(self) -> str:
        return f"<BusinessHours(salon_id={self.salon_id})>"