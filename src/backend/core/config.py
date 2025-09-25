"""
Configurações da aplicação para o backend Aluvi.
Centraliza todas as constantes de configuração e variáveis de ambiente.
"""

import os
from typing import List
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


# =============================================================================
# CONFIGURAÇÃO DE SEGURANÇA
# =============================================================================

class SecurityConfig:
    """Configurações relacionadas à segurança."""

    # Configuração JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here_change_in_production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Hash de senhas
    bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Esquema OAuth2
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login-form")


# =============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# =============================================================================

class AppConfig:
    """Configuração geral da aplicação."""

    TITLE: str = "Aluvi - Sistema de Agendamento"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema completo de agendamento para salões de beleza"

    # Ambiente
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")


# =============================================================================
# CONFIGURAÇÃO CORS
# =============================================================================

class CORSConfig:
    """Configuração CORS (Cross-Origin Resource Sharing)."""

    ORIGINS: List[str] = ["*"]  # Em produção, especifique domínios permitidos
    CREDENTIALS: bool = True
    METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    HEADERS: List[str] = ["*"]


# =============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# =============================================================================

class DatabaseConfig:
    """Configuração de conexão do banco de dados."""

    # SQLite para desenvolvimento (fácil migração para PostgreSQL)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./aluvi.db")

    # Configurações do pool de conexões
    POOL_SIZE: int = int(os.getenv("POOL_SIZE", "10"))
    MAX_OVERFLOW: int = int(os.getenv("MAX_OVERFLOW", "20"))

    # Configurações de migração
    AUTO_MIGRATE: bool = os.getenv("AUTO_MIGRATE", "true").lower() == "true"


# =============================================================================
# CONFIGURAÇÃO DO SISTEMA DE ARQUIVOS
# =============================================================================

class FileSystemConfig:
    """Configuração do sistema de arquivos e arquivos estáticos."""

    # Arquivos estáticos
    STATIC_DIRECTORY: str = "src/frontend/assets"
    STATIC_MOUNT_PATH: str = "/assets"

    # Arquivos do frontend (servidos diretamente pelo FastAPI)
    FRONTEND_DIRECTORY: str = "src/frontend/pages"
    FRONTEND_MOUNT_PATH: str = "/"

    # Diretórios de upload
    UPLOAD_DIRECTORY: str = "uploads"
    LOGO_UPLOAD_DIRECTORY: str = f"{UPLOAD_DIRECTORY}/logos"


# =============================================================================
# CONFIGURAÇÃO DA LÓGICA DE NEGÓCIO
# =============================================================================

class BusinessConfig:
    """Configuração específica da lógica de negócio."""

    # Configurações do dashboard
    DASHBOARD_ALERT_THRESHOLD: int = 10  # Alertar quando fila estiver cheia

    # Configurações de agendamento
    APPOINTMENT_REMINDER_MINUTES: int = 30  # Minutos antes do agendamento para enviar lembrete
    PRESENCE_TIMEOUT_SECONDS: int = 300  # 5 minutos para confirmar presença

    # Configurações de assinatura
    DEFAULT_SUBSCRIPTION_DAYS: int = 30  # Período de teste padrão

    # Sistema de pontos
    POINTS_PER_SERVICE: int = 10  # Pontos base por serviço
    POINTS_REDEEM_THRESHOLD: int = 100  # Pontos necessários para resgate


# =============================================================================
# CONFIGURAÇÃO DE EMAIL (Integração SMTP futura)
# =============================================================================

class EmailConfig:
    """Configuração de email para integração SMTP futura."""

    # Configurações SMTP (para implementação futura)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # Templates de email
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@aluvi.com")
    FROM_NAME: str = "Aluvi Sistema"

    # Funcionalidades de email
    ENABLE_EMAIL_NOTIFICATIONS: bool = os.getenv("ENABLE_EMAIL", "false").lower() == "true"


# =============================================================================
# CONFIGURAÇÃO DE LOGGING
# =============================================================================

class LoggingConfig:
    """Configuração de logging."""

    LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Arquivos de log
    LOG_FILE: str = "logs/aluvi.log"
    ERROR_LOG_FILE: str = "logs/error.log"

    # Logging de auditoria
    ENABLE_AUDIT_LOG: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 90


# =============================================================================
# INSTÂNCIAS
# =============================================================================

# Criar instâncias de configuração
security = SecurityConfig()
app = AppConfig()
cors = CORSConfig()
database = DatabaseConfig()
filesystem = FileSystemConfig()
business = BusinessConfig()
email = EmailConfig()
logging = LoggingConfig()

# Compatibilidade legado (para migração gradual)
SECRET_KEY = security.SECRET_KEY
ALGORITHM = security.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = security.ACCESS_TOKEN_EXPIRE_MINUTES
bcrypt_context = security.bcrypt_context
oauth2_scheme = security.oauth2_scheme

APP_TITLE = app.TITLE
APP_VERSION = app.VERSION

CORS_ORIGINS = cors.ORIGINS
CORS_CREDENTIALS = cors.CREDENTIALS
CORS_METHODS = cors.METHODS
CORS_HEADERS = cors.HEADERS

STATIC_DIRECTORY = filesystem.STATIC_DIRECTORY
STATIC_MOUNT_PATH = filesystem.STATIC_MOUNT_PATH

DASHBOARD_ALERT_THRESHOLD = business.DASHBOARD_ALERT_THRESHOLD