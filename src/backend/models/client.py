"""
Definições de modelo de cliente para o backend Aluvi.
Gerencia clientes do salão e seus programas de fidelidade.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel, TimestampMixin, SoftDeleteMixin


class Client(BaseModel, TimestampMixin, SoftDeleteMixin):
    """
    Modelo de cliente representando clientes do salão.

    Clientes podem ser anônimos (sem senha) ou registrados (com senha).
    Inclui sistema de pontos de fidelidade.
    """

    __tablename__ = "clientes"

    # Informações básicas
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)  # Opcional para clientes anônimos
    telefone = Column(String(20), nullable=True)  # Único por salão

    # Autenticação (opcional para clientes registrados)
    senha = Column(String(255), nullable=True)  # Senha criptografada

    # Programa de fidelidade
    pontos_fidelidade = Column(Integer, default=0)

    # Salon relationship
    salon_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    salon = relationship("User", back_populates="clients")

    # Appointments
    appointments = relationship("Appointment", back_populates="client", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('telefone', 'salon_id', name='unique_telefone_per_salon'),
        CheckConstraint('pontos_fidelidade >= 0', name='chk_pontos_nao_negativos'),
    )

    @property
    def is_registered(self) -> bool:
        """Verificar se o cliente tem senha (está registrado)."""
        return self.senha is not None

    @property
    def display_name(self) -> str:
        """Obter nome de exibição para o cliente."""
        return self.nome or f"Cliente #{self.id}"

    def adicionar_pontos(self, pontos: int):
        """Adicionar pontos de fidelidade ao cliente."""
        self.pontos_fidelidade += pontos

    def resgatar_pontos(self, pontos: int) -> bool:
        """Resgatar pontos de fidelidade se saldo suficiente."""
        if self.pontos_fidelidade >= pontos:
            self.pontos_fidelidade -= pontos
            return True
        return False

    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, nome='{self.nome}', salon_id={self.salon_id})>"