"""
Arquivo principal da aplicação FastAPI.
Configura a aplicação, middlewares, rotas e handlers globais.
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from .routes import auth_router, clients_router, services_router, appointments_router, reports_router, professionals_router, business_hours_router, salons_router, monitoring_router
from .database import Base, engine, get_db
from .dependencies import verificar_token
from .core.logging import get_logger
from passlib.context import CryptContext  # type: ignore - Biblioteca para hash de senhas
from fastapi.security import OAuth2PasswordBearer  # type: ignore - Para autenticação JWT
from dotenv import load_dotenv  # type: ignore - Carrega variáveis de ambiente
import os

# Carrega variáveis de ambiente do arquivo .env (como chaves secretas, configurações de BD)
load_dotenv()

# Configurar logger
logger = get_logger()

# Configurações movidas para app.config (comentário para referência futura)

# Cria instância principal da aplicação FastAPI com metadados
app = FastAPI(
    title="Aluvi API - Sistema de Agendamentos para Salões",
    description="""
    ## Sistema de Agendamentos para Salões de Beleza

    Esta API fornece funcionalidades completas para gerenciamento de salões, incluindo:

    ### 👥 **Usuários e Autenticação**
    - Cadastro e autenticação de donos de salão
    - Sistema de administradores
    - Controle de permissões por papel (role-based access)

    ### 🏪 **Salões**
    - Gerenciamento de informações do salão
    - Configuração de horários de funcionamento
    - Personalização de cards de apresentação

    ### 👨‍💼 **Clientes**
    - Cadastro de clientes (anônimos ou registrados)
    - Programa de fidelidade com pontos
    - Histórico de agendamentos

    ### ✂️ **Serviços**
    - Catálogo de serviços oferecidos
    - Definição de preços e duração
    - Controle de pontos de fidelidade por serviço

    ### 👩‍💼 **Profissionais**
    - Cadastro de equipe do salão
    - Especialidades e disponibilidade
    - Associação com serviços

    ### 📅 **Agendamentos**
    - Sistema completo de reservas
    - Validação de conflitos de horário
    - Controle de status e ciclo de vida
    - Notificações e lembretes

    ### 🔒 **Segurança**
    - Autenticação JWT
    - Controle de acesso baseado em papéis
    - Logs de auditoria
    - Validações de entrada robustas

    ### 📊 **Relatórios**
    - Dashboard com métricas
    - Análises de performance
    - Relatórios financeiros

    ## Autenticação

    Para acessar endpoints protegidos, inclua o token JWT no header:
    ```
    Authorization: Bearer <seu_token_jwt>
    ```

    ## Status Codes

    - `200`: Sucesso
    - `201`: Criado com sucesso
    - `400`: Dados inválidos
    - `401`: Não autorizado
    - `403`: Acesso proibido
    - `404`: Recurso não encontrado
    - `409`: Conflito (ex: horário ocupado)
    - `500`: Erro interno do servidor
    """,
    version="2.0.0",
    contact={
        "name": "Equipe Aluvi",
        "email": "suporte@aluvi.com",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "autenticação",
            "description": "Operações de login e gerenciamento de tokens"
        },
        {
            "name": "salões",
            "description": "Gerenciamento de salões e suas configurações"
        },
        {
            "name": "clientes",
            "description": "Gerenciamento de clientes e programa de fidelidade"
        },
        {
            "name": "serviços",
            "description": "Catálogo de serviços oferecidos"
        },
        {
            "name": "profissionais",
            "description": "Gerenciamento da equipe do salão"
        },
        {
            "name": "agendamentos",
            "description": "Sistema de reservas e agendamentos"
        },
        {
            "name": "relatórios",
            "description": "Dashboards e análises de performance"
        },
        {
            "name": "monitoramento",
            "description": "Health checks e métricas do sistema"
        }
    ]
)

# Handler global para capturar todas as exceções não tratadas
# Garante que sempre retornamos JSON em vez de HTML de erro do FastAPI
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para todas as exceções não tratadas na aplicação.

    Args:
        request: Requisição HTTP que causou o erro
        exc: Exceção que ocorreu

    Returns:
        JSONResponse: Resposta padronizada com erro
    """
    # Log detalhado para debugging interno
    logger.error(
        f"Erro não tratado na requisição {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
        exc_info=True
    )

    # Resposta genérica para o cliente (não vaza informações sensíveis)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Erro interno do servidor. Nossa equipe foi notificada."
        }
    )

# Configuração do CORS (Cross-Origin Resource Sharing)
# Permite que o frontend (executando em porta diferente) acesse a API
# Configuração segura baseada em ambiente
import os
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# Em produção, adicionar apenas domínios específicos
if os.getenv("ENVIRONMENT") == "production":
    # Adicionar domínios de produção autorizados
    allowed_origins.extend([
        "https://seusite.com",
        "https://www.seusite.com"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,  # Permite envio de cookies/credenciais (tokens JWT)
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # Métodos específicos
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],  # Headers específicos necessários
    max_age=86400,  # Cache de preflight por 24 horas
)

# Monta diretório de arquivos estáticos do frontend
# Permite servir CSS, JS, imagens diretamente pela API
import os
frontend_path = os.path.join(os.path.dirname(__file__), "../../src/frontend")
app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend")

# Monta diretório de uploads (logos dos salões)
# Permite servir imagens de logo diretamente pela API
from .core.config import filesystem
logos_path = os.path.join(os.path.dirname(__file__), f"../../{filesystem.LOGO_UPLOAD_DIRECTORY}")
os.makedirs(logos_path, exist_ok=True)  # Garante que o diretório existe
app.mount("/logos", StaticFiles(directory=logos_path), name="logos")

# Cria todas as tabelas no banco de dados se não existirem
# Base.metadata.create_all() cria as tabelas baseadas nos modelos SQLAlchemy
Base.metadata.create_all(bind=engine)

# ROTAS PARA SERVIR PÁGINAS DO FRONTEND
# Como a API também serve o frontend, temos rotas para as páginas HTML

@app.get("/")
async def read_root():
    """
    Rota para servir a página inicial do sistema.
    Retorna o arquivo index.html do frontend.
    """
    return FileResponse("src/frontend/pages/index.html", media_type="text/html")

@app.get("/{page}.html")
async def read_page(page: str):
    """
    Rota dinâmica para servir qualquer página HTML do frontend.
    Exemplo: /login.html retorna src/frontend/pages/login.html

    Args:
        page: Nome da página sem extensão (ex: "login", "register")
    """
    return FileResponse(f"src/frontend/pages/{page}.html", media_type="text/html")

# ENDPOINTS DE TESTE (para desenvolvimento e debug)

@app.get("/test")
async def test_endpoint():
    """Endpoint simples para testar se a API está funcionando."""
    return {"message": "Endpoint público funcionando!"}

# ENDPOINT PARA PERFIL DO CLIENTE (evitando conflitos de rota)
@app.get("/api/profile", response_model=dict)
async def get_client_profile_endpoint(db: Session = Depends(get_db), cliente = Depends(verificar_token)):
    """
    Endpoint para obter perfil do cliente logado.
    Colocado aqui para evitar conflitos com /clients/{client_id}
    """
    try:
        from . import schemas
        pontos_fidelidade = getattr(cliente, 'pontos_fidelidade', None)
        if pontos_fidelidade is None:
            pontos_fidelidade = 0

        response_data = {
            "id": cliente.id or 0,
            "nome": cliente.nome or "Cliente",
            "email": cliente.email,
            "telefone": cliente.telefone,
            "pontos_fidelidade": pontos_fidelidade,
            "salon_id": cliente.salon_id
        }

        # Validar com schema
        validated_data = schemas.ClientePerfil(**response_data)
        return validated_data.model_dump()

    except Exception as e:
        logger.error(f"[PROFILE] Erro ao processar dados do cliente: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar dados do cliente")

@app.post("/test-login")
async def test_login_endpoint(data: dict):
    """
    Endpoint de teste para receber dados de login.
    Útil para testar envio de dados sem validação.
    """
    return {"received": data, "message": "Dados recebidos com sucesso!"}

# Importação aqui para evitar circular imports
from .schemas import LoginSchema

@app.post("/test-login-schema")
async def test_login_schema(login_data: LoginSchema):
    """
    Endpoint de teste com validação usando Pydantic schema.
    Demonstra como os dados são validados automaticamente.
    """
    return {"received": login_data.model_dump(), "message": "Schema funcionando!"}

@app.post("/simple-test")
async def simple_test():
    """Endpoint de teste mais simples possível, sem dependências."""
    return {"message": "Teste simples funcionando!"}

# INCLUSÃO DOS ROUTERS MODULARES
# Cada router contém endpoints relacionados a uma funcionalidade específica
# O prefix adiciona automaticamente o caminho base para todos os endpoints do router

app.include_router(auth_router, prefix="/auth", tags=["Autenticação"])
# Endpoints: /auth/login, /auth/register, /auth/logout

app.include_router(clients_router, prefix="/clients", tags=["Clientes"])
# Endpoints: /clients/, /clients/register, /clients/login, /clients/me, etc.

# Rota adicional para agendamentos do cliente (evitando conflitos)
@app.get("/test-client-appointments")
def get_client_appointments_api(client_id: int, db: Session = Depends(get_db)):
    """
    Endpoint alternativo para buscar agendamentos do cliente.
    Evita conflitos de rotas no router de clientes.
    """
    try:
        from . import models

        # Buscar agendamentos do cliente específico
        appointments = db.query(models.Agendamento).filter(
            models.Agendamento.cliente_id == client_id
        ).all()

        # Carregar dados relacionados para cada agendamento
        for appointment in appointments:
            try:
                # Carregar serviço
                if appointment.servico_id:
                    appointment.servico = db.query(models.Servico).filter(
                        models.Servico.id == appointment.servico_id
                    ).first()

                # Carregar profissional
                if appointment.profissional_id:
                    appointment.profissional = db.query(models.Profissional).filter(
                        models.Profissional.id == appointment.profissional_id
                    ).first()

                # Carregar cliente
                if appointment.cliente_id:
                    appointment.cliente = db.query(models.Cliente).filter(
                        models.Cliente.id == appointment.cliente_id
                    ).first()

            except Exception as e:
                logger.error(f"Erro ao carregar dados relacionados para agendamento {appointment.id}: {str(e)}")
                # Define valores padrão
                appointment.servico = None
                appointment.profissional = None
                appointment.cliente = None

        return appointments

    except Exception as e:
        logger.error(f"Erro ao buscar agendamentos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar agendamentos")

# Rota adicional para perfil do cliente (evitando conflitos)
@app.get("/test-client-profile")
def get_client_profile_api(db: Session = Depends(get_db), cliente = Depends(verificar_token)):
    """
    Endpoint alternativo para buscar perfil do cliente.
    Evita conflitos de rotas no router de clientes.
    """
    try:
        from . import schemas

        pontos_fidelidade = getattr(cliente, 'pontos_fidelidade', None)
        if pontos_fidelidade is None:
            pontos_fidelidade = 0

        response_data = {
            "id": cliente.id or 0,
            "nome": cliente.nome or "Cliente",
            "email": cliente.email,
            "telefone": cliente.telefone,
            "pontos_fidelidade": pontos_fidelidade,
            "salon_id": cliente.salon_id
        }

        # Validar com schema
        validated_data = schemas.ClientePerfil(**response_data)
        return validated_data

    except Exception as e:
        logger.error(f"Erro ao buscar perfil do cliente: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar perfil")

app.include_router(services_router, prefix="/services", tags=["Serviços"])
# Endpoints: /services/, /services/public, /services/{id}, etc.

app.include_router(professionals_router, prefix="/professionals", tags=["Profissionais"])
# Endpoints: /professionals/, /professionals/{id}, /professionals/available/{service_id}

app.include_router(appointments_router, prefix="/appointments", tags=["Agendamentos"])
# Endpoints: /appointments/, /appointments/public, /appointments/{id}/status, etc.

app.include_router(reports_router, prefix="/reports", tags=["Relatórios"])
# Endpoints: /reports/dashboard, /reports/revenue/*, /reports/clients/*, etc.

app.include_router(business_hours_router, prefix="", tags=["Horários de Funcionamento"])
# Endpoints: /empresa/{id}/horarios, /empresa/{id}/horarios/disponiveis

app.include_router(salons_router, prefix="/salons", tags=["Salões"])
# Endpoints: /salons/public/{salon_id}

app.include_router(monitoring_router, prefix="", tags=["Monitoramento"])
# Endpoints: /health, /metrics, /status

# COMANDO PARA EXECUTAR O SERVIDOR (comentado para referência)
'''
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
'''