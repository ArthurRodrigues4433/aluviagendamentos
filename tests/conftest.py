"""
Configuração compartilhada para testes.
Fornece fixtures e configurações comuns.
"""

import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Adicionar src ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend.database import Base


@pytest.fixture(scope="session")
def test_engine():
    """Engine de teste com SQLite em memória."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Fábrica de sessões para testes."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_engine, test_session_factory):
    """Sessão de banco de dados para cada teste."""
    # Criar todas as tabelas
    Base.metadata.create_all(bind=test_engine)

    # Criar sessão
    session = test_session_factory()

    try:
        yield session
    finally:
        session.rollback()
        session.close()

    # Limpar tabelas após o teste
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def sample_user_data():
    """Dados de exemplo para usuário."""
    return {
        "nome": "Salão Teste",
        "email": "teste@salao.com",
        "senha": "senha123",
        "ativo": True,
        "admin": False
    }


@pytest.fixture
def sample_client_data():
    """Dados de exemplo para cliente."""
    return {
        "nome": "João Silva",
        "email": "joao@email.com",
        "telefone": "11999999999",
        "salon_id": 1
    }


@pytest.fixture
def sample_service_data():
    """Dados de exemplo para serviço."""
    return {
        "nome": "Corte de Cabelo",
        "descricao": "Corte masculino completo",
        "duracao_minutos": 60,
        "preco": 50.0,
        "pontos_fidelidade": 10,
        "salon_id": 1
    }


@pytest.fixture
def sample_appointment_data():
    """Dados de exemplo para agendamento."""
    from datetime import datetime, timedelta
    return {
        "client_id": 1,
        "service_id": 1,
        "professional_id": 1,
        "salon_id": 1,
        "data_hora": datetime.now() + timedelta(days=1),
        "valor": 50.0
    }