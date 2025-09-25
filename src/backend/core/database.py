"""
Configuração e gerenciamento de conexões do banco de dados.
Suporta tanto SQLite (desenvolvimento) quanto PostgreSQL (produção).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Engine
from typing import Generator, Optional
import logging

from .config import database as db_config

# Configurar logging
logger = logging.getLogger(__name__)

# Base SQLAlchemy para todos os modelos
Base = declarative_base()


class DatabaseManager:
    """Gerencia conexões e sessões do banco de dados."""

    def __init__(self):
        self.engine: Optional[Engine] = None
        self.SessionLocal = None
        self._create_engine()

    def _create_engine(self):
        """Cria engine do banco de dados baseada na configuração."""
        try:
            database_url = db_config.DATABASE_URL

            # Configurar opções da engine baseadas no tipo de banco
            if database_url.startswith("sqlite"):
                # Configuração específica do SQLite
                connect_args = {
                    "check_same_thread": False,
                }
                # Usar StaticPool para SQLite para evitar problemas de threading
                poolclass = StaticPool
                logger.info("Usando banco SQLite")

            elif database_url.startswith("postgresql"):
                # Configuração específica do PostgreSQL
                connect_args = {}
                poolclass = None
                logger.info("Usando banco PostgreSQL")

            else:
                raise ValueError(f"Esquema de URL de banco não suportado: {database_url}")

            # Criar engine com parâmetros específicos do banco
            engine_kwargs = {
                "connect_args": connect_args,
                "echo": False,  # Definir como True para logging de queries SQL em desenvolvimento
            }

            # Adicionar configuração de pool apenas para PostgreSQL
            if database_url.startswith("postgresql"):
                engine_kwargs.update({
                    "pool_size": db_config.POOL_SIZE,
                    "max_overflow": db_config.MAX_OVERFLOW,
                })

            # Adicionar poolclass apenas para SQLite
            if poolclass is not None:
                engine_kwargs["poolclass"] = poolclass

            self.engine = create_engine(database_url, **engine_kwargs)

            # Criar fábrica de sessões
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            # Configurar listeners de eventos específicos do SQLite
            if database_url.startswith("sqlite"):
                self._configure_sqlite()

            logger.info("Engine do banco de dados criada com sucesso")

        except Exception as e:
            logger.error(f"Falha ao criar engine do banco de dados: {e}")
            raise

    def _configure_sqlite(self):
        """Configurar definições específicas do SQLite."""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Habilitar chaves estrangeiras e outras otimizações do SQLite."""
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    def get_session(self) -> Generator[Session, None, None]:
        """Obter uma sessão do banco de dados."""
        if self.SessionLocal is None:
            raise RuntimeError("Banco de dados não inicializado. Chame _create_engine() primeiro.")
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_tables(self):
        """Criar todas as tabelas definidas nos modelos."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tabelas do banco de dados criadas com sucesso")
        except Exception as e:
            logger.error(f"Falha ao criar tabelas: {e}")
            raise

    def drop_tables(self):
        """Remover todas as tabelas (use com cuidado!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Todas as tabelas do banco de dados foram removidas")
        except Exception as e:
            logger.error(f"Falha ao remover tabelas: {e}")
            raise

    def health_check(self) -> bool:
        """Verificar conectividade do banco de dados."""
        if self.engine is None:
            logger.error("Engine do banco de dados não inicializada")
            return False

        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Verificação de saúde do banco de dados falhou: {e}")
            return False


# Instância global do gerenciador de banco de dados
db_manager = DatabaseManager()

# Funções de compatibilidade legado
def get_db() -> Generator[Session, None, None]:
    """Função legado para injeção de dependência FastAPI."""
    yield from db_manager.get_session()


# Exportar objetos comumente usados
engine = db_manager.engine
SessionLocal = db_manager.SessionLocal