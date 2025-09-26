"""
Definições de modelo base e utilitários para o backend Aluvi.
Fornece funcionalidade comum para todos os modelos de banco de dados.
"""

from datetime import datetime
from typing import Optional, Callable, Any
from sqlalchemy import Column, DateTime, func, Integer, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import exc

from ..core.database import Base


class TimestampMixin:
    """Mixin para adicionar campos de timestamp aos modelos."""

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Mixin para adicionar funcionalidade de exclusão suave aos modelos."""

    deleted_at = Column(DateTime, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)

    def soft_delete(self):
        """Marcar registro como excluído sem removê-lo fisicamente."""
        self.deleted_at = func.now()
        self.is_active = 0

    def restore(self):
        """Restaurar um registro excluído suavemente."""
        self.deleted_at = None
        self.is_active = 1

    @property
    def is_deleted(self) -> bool:
        """Verificar se o registro está excluído suavemente."""
        return self.is_active == 0 or self.deleted_at is not None


class AuditMixin:
    """Mixin para adicionar campos de auditoria aos modelos."""

    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos para auditoria
    creator = relationship("User", primaryjoin="AuditMixin.created_by == User.id", foreign_keys=[created_by])
    updater = relationship("User", primaryjoin="AuditMixin.updated_by == User.id", foreign_keys=[updated_by])


class BaseModel(Base):
    """Modelo base aprimorado com funcionalidade comum."""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


    def to_dict(self) -> dict:
        """Converter instância do modelo para dicionário."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def update_from_dict(self, data: dict):
        """Atualizar instância do modelo a partir de dicionário."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def get_by_id(cls, session, id: int):
        """Obter registro por ID."""
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_all(cls, session, limit: Optional[int] = None, offset: Optional[int] = None, include_deleted: bool = False):
        """Obter todos os registros com paginação opcional."""
        query = session.query(cls)
        if not include_deleted and hasattr(cls, 'is_active'):
            query = query.filter(cls.is_active == 1)
            if hasattr(cls, 'deleted_at'):
                query = query.filter(cls.deleted_at.is_(None))
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all()

    def save(self, session):
        """Salvar a instância do modelo."""
        session.add(self)
        session.commit()
        session.refresh(self)
        return self

    def delete(self, session):
        """Excluir a instância do modelo."""
        session.delete(self)
        session.commit()
        return True

    @classmethod
    def execute_in_transaction(cls, session: Session, operation: Callable[[Session], Any]) -> Any:
        """Executar operação dentro de uma transação."""
        try:
            with session.begin():
                return operation(session)
        except exc.SQLAlchemyError as e:
            session.rollback()
            raise e

    @classmethod
    def get_active(cls, session, **filters):
        """Obter registros ativos (não soft-deletados) com filtros."""
        query = session.query(cls).filter(cls.is_active == 1)
        if hasattr(cls, 'deleted_at'):
            query = query.filter(cls.deleted_at.is_(None))
        for key, value in filters.items():
            query = query.filter(getattr(cls, key) == value)
        return query.all()