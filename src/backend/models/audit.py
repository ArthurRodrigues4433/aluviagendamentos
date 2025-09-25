"""
Definições de modelo de auditoria e segurança para o backend Aluvi.
Gerencia logs de auditoria e lista negra de tokens.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from typing import Optional

from .base import BaseModel, TimestampMixin
from .enums import AuditAction


class AuditLog(BaseModel, TimestampMixin):
    """
    Modelo de log de auditoria para rastrear ações do sistema.

    Registra ações importantes como logins, criação de proprietários, pagamentos, etc.
    """

    __tablename__ = "audit_logs"

    # Informações da ação
    acao = Column(String(50), nullable=False)
    detalhes = Column(String(1000), nullable=True)

    # Entidades relacionadas
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # Quem realizou a ação
    salon_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # Salão afetado

    # Contexto adicional
    endereco_ip = Column(String(45), nullable=True)  # Endereço IPv4/IPv6

    # Relacionamentos
    usuario = relationship("User", primaryjoin="User.id == AuditLog.usuario_id", foreign_keys=[usuario_id], back_populates="audit_logs_created")
    salon_afetado = relationship("User", primaryjoin="User.id == AuditLog.salon_id", foreign_keys=[salon_id], back_populates="audit_logs_affected")

    @classmethod
    def log_action(cls, session, action: AuditAction, user_id: Optional[int] = None,
                    salon_id: Optional[int] = None, details: Optional[str] = None, ip_address: Optional[str] = None):
        """Método auxiliar para criar entradas de log de auditoria."""
        log_entry = cls(
            acao=action.value,
            usuario_id=user_id,
            salon_id=salon_id,
            detalhes=details,
            endereco_ip=ip_address
        )
        session.add(log_entry)
        session.commit()

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, acao='{self.acao}', usuario_id={self.usuario_id})>"


class TokenBlacklist(BaseModel, TimestampMixin):
    """
    Lista negra de tokens para invalidação JWT.

    Armazena tokens JWT invalidados para prevenir reutilização após logout.
    """

    __tablename__ = "token_blacklist"

    # Informações do token
    token = Column(String(500), unique=True, index=True, nullable=False)
    expiracao = Column(DateTime, nullable=False)  # Quando o token expira naturalmente

    def is_expired(self) -> bool:
        """Verificar se o token está expirado."""
        from datetime import datetime
        return datetime.utcnow() > self.expiracao

    def __repr__(self) -> str:
        return f"<TokenBlacklist(id={self.id}, expiracao={self.expiracao})>"