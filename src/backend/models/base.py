"""
Definições de modelo base e utilitários para o backend Aluvi.
Fornece funcionalidade comum para todos os modelos de banco de dados.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, func, Integer
from sqlalchemy.ext.declarative import declared_attr

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
    def get_all(cls, session, limit: Optional[int] = None, offset: Optional[int] = None):
        """Obter todos os registros com paginação opcional."""
        query = session.query(cls)
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