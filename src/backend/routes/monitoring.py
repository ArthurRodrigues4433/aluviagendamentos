"""
Rotas de monitoramento e observabilidade para o backend Aluvi.
Inclui health checks, métricas e status do sistema.
"""

from fastapi import APIRouter, Depends
from ..core.monitoring import get_health_status, get_metrics, health_checker
from ..dependencies import verificar_token

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Endpoint público de verificação de saúde do sistema.
    Retorna status de saúde de todos os componentes.
    """
    return get_health_status()


@router.get("/health/database")
async def database_health():
    """
    Verificação específica da saúde do banco de dados.
    """
    return health_checker.check_database()


@router.get("/health/system")
async def system_health():
    """
    Verificação específica da saúde dos recursos do sistema.
    """
    return health_checker.check_system_resources()


@router.get("/metrics")
async def get_system_metrics(admin_user = Depends(verificar_token)):
    """
    Endpoint protegido para métricas detalhadas do sistema.
    Requer autenticação de administrador.
    """
    return get_metrics()


@router.get("/status")
async def system_status():
    """
    Status geral do sistema com informações básicas.
    """
    health = get_health_status()
    return {
        "service": "Aluvi Backend",
        "version": "1.0.0",
        "status": health["status"],
        "uptime": health["uptime"],
        "timestamp": health["timestamp"]
    }