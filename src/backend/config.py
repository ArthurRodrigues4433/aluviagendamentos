# Configurações da aplicação FilaDigital
# Centraliza todas as configurações e constantes
import os
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv 

# Carrega variáveis de ambiente
load_dotenv()

# Configurações de segurança
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Configurações de autenticação
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login-form")

# Configurações da aplicação
APP_TITLE = "Aluvi"
APP_VERSION = "1.0.0"

# Configurações de CORS
CORS_ORIGINS = ["*"]  # Em produção, especifique domínios permitidos
CORS_CREDENTIALS = True
CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS = ["*"]

# Configurações de arquivos estáticos
STATIC_DIRECTORY = "frontend"
STATIC_MOUNT_PATH = "/frontend"

# Configurações de dashboard
DASHBOARD_ALERT_THRESHOLD = 10  # Threshold para alertas de fila cheia