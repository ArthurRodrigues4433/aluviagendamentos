"""
Definições de modelo de profissional para o backend Aluvi.
Gerencia profissionais do salão e seus serviços.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel, TimestampMixin, SoftDeleteMixin


class Professional(BaseModel, TimestampMixin, SoftDeleteMixin):
    """
    Modelo de profissional representando equipe do salão.

    Profissionais trabalham em salões e fornecem serviços.
    """

    __tablename__ = "profissionais"

    # Informações básicas
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    telefone = Column(String(20), nullable=True)
    especialidade = Column(String(255), nullable=True)
    foto = Column(String(500), nullable=True)  # URL da foto do profissional


    # Status
    ativo = Column(Boolean, default=True)

    # Relacionamento com salão
    salon_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    salon = relationship("User", back_populates="professionals")

    # Relacionamentos
    appointments = relationship("Appointment", primaryjoin="Professional.id == Appointment.professional_id", back_populates="professional")
    services = relationship("ServiceProfessional", back_populates="professional")

    def __repr__(self) -> str:
        return f"<Professional(id={self.id}, nome='{self.nome}', salon_id={self.salon_id})>"


class ServiceProfessional(BaseModel):
    """
    Relacionamento muitos-para-muitos entre serviços e profissionais.
    """

    __tablename__ = "servicos_profissionais"

    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=False)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=False)
    salon_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Relationships
    service = relationship("Service", back_populates="professionals")
    professional = relationship("Professional", back_populates="services")