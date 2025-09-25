"""
Definições do modelo de usuário para o backend Aluvi.
Gerencia donos de salão, administradores e usuários do sistema.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Date, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel, TimestampMixin
from .enums import UserRole


class User(BaseModel):
    """
    Modelo de usuário representando donos de salão e administradores.

    Cada usuário representa um estabelecimento diferente (multi-tenant).
    Administradores podem criar e gerenciar donos de salão.
    """

    __tablename__ = "usuarios"

    # Informações básicas
    name = Column("nome", String(255), nullable=False)  # Nome do salão/negócio
    email = Column("email", String(255), unique=True, index=True, nullable=False)
    password = Column("senha", String(255), nullable=False)  # Senha criptografada

    # Status e permissões
    is_active = Column("ativo", Boolean, default=True)
    is_admin = Column("admin", Boolean, default=False)  # Administrador do sistema

    # Gerenciamento de assinatura
    subscription_paid = Column("mensalidade_pago", Boolean, default=False)
    subscription_due_date = Column("data_vencimento_mensalidade", Date, nullable=True)

    # Gerenciamento de senha
    has_temp_password = Column("senha_temporaria", Boolean, default=True)  # Deve trocar senha
    is_first_login = Column("primeiro_login", Boolean, default=True)    # Força troca de senha
    temp_password = Column("senha_temporaria_atual", String(255), nullable=True)  # Senha temporária atual

    # Campos de auditoria
    created_at = Column("criado_em", DateTime, nullable=True)
    created_by = Column("criado_por", Integer, ForeignKey("usuarios.id"), nullable=True)
    creator = relationship("User", primaryjoin="User.id == User.created_by", foreign_keys=[created_by])

    # Relacionamentos
    clients = relationship("Client", primaryjoin="User.id == Client.salon_id", back_populates="salon", cascade="all, delete-orphan")
    services = relationship("Service", primaryjoin="User.id == Service.salon_id", back_populates="salon", cascade="all, delete-orphan")
    professionals = relationship("Professional", primaryjoin="User.id == Professional.salon_id", back_populates="salon", cascade="all, delete-orphan")
    appointments = relationship("Appointment", primaryjoin="User.id == Appointment.salon_id", back_populates="salon", cascade="all, delete-orphan")
    business_hours = relationship("BusinessHours", primaryjoin="User.id == BusinessHours.salon_id", back_populates="salon", uselist=False, cascade="all, delete-orphan")

    # Campos para aparência customizada do card (para exibição na seleção de salão)
    card_display_name = Column("card_display_name", String(255), nullable=True)  # Nome customizado no card
    card_location = Column("card_location", String(255), nullable=True)  # Localização customizada
    card_description = Column("card_description", String(1000), nullable=True)  # Descrição curta no card
    card_logo = Column("card_logo", String(500), nullable=True)  # Logo customizado para o card

    # Campos adicionais da empresa (informações básicas)
    telefone = Column("telefone", String(20), nullable=True)
    endereco = Column("endereco", String(500), nullable=True)
    descricao = Column("descricao", String(1000), nullable=True)
    logo = Column("logo", String(500), nullable=True)

    # Campo para nome do dono (separado do nome da empresa)
    owner_name = Column("nome_dono", String(255), nullable=True)

    # Logs de auditoria onde este usuário está envolvido
    audit_logs_created = relationship("AuditLog", primaryjoin="User.id == AuditLog.usuario_id", foreign_keys="AuditLog.usuario_id", back_populates="usuario")
    audit_logs_affected = relationship("AuditLog", primaryjoin="User.id == AuditLog.salon_id", foreign_keys="AuditLog.salon_id", back_populates="salon_afetado")

    @property
    def role(self) -> UserRole:
        """Obter role do usuário baseado no status de admin."""
        return UserRole.ADMIN if self.is_admin else UserRole.OWNER  # type: ignore

    @role.setter
    def role(self, value: UserRole) -> None:
        """Definir role do usuário (usado internamente pelo sistema de autenticação)."""
        # Esta propriedade é derivada de is_admin, então não podemos definir diretamente
        # Mas precisamos do setter para compatibilidade com o código de autenticação
        pass  # Ignorar tentativas de definir role diretamente

    @property
    def subscription_status(self) -> str:
        """Obter descrição do status da assinatura."""
        if not self.subscription_paid:  # type: ignore
            return "Pendente"
        if self.subscription_due_date:  # type: ignore
            return f"Ativo até {self.subscription_due_date}"
        return "Ativo"

    def can_create_owners(self) -> bool:
        """Verificar se o usuário pode criar outros donos de salão."""
        return self.is_admin and self.is_active  # type: ignore

    def can_manage_salon(self) -> bool:
        """Verificar se o usuário pode gerenciar seu salão."""
        return self.is_active and (self.is_admin or self.subscription_paid)  # type: ignore

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', role={self.role})>"