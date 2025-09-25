"""
Definições de modelo de serviço para o backend Aluvi.
Gerencia serviços do salão e suas configurações.
"""

from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel, TimestampMixin


class Service(BaseModel, TimestampMixin):
    """
    Modelo de serviço representando serviços do salão.

    Serviços oferecidos por salões com preço e duração.
    """

    __tablename__ = "servicos"

    # Informações básicas
    nome = Column(String(255), nullable=False)
    descricao = Column(String(1000), nullable=True)
    duracao_minutos = Column(Integer, nullable=False)
    preco = Column(Float, nullable=False)
    pontos_fidelidade = Column(Integer, default=0)

    # Salon relationship
    salon_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    salon = relationship("User", back_populates="services")

    # Relationships
    appointments = relationship("Appointment", primaryjoin="Service.id == Appointment.service_id", back_populates="service")
    professionals = relationship("ServiceProfessional", back_populates="service")

    @property
    def display_price(self) -> str:
        """Obter exibição de preço formatada."""
        return f"R$ {self.preco:.2f}".replace(".", ",")

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, nome='{self.nome}', preco={self.preco})>"