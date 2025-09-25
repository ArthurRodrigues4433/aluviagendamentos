"""
Sistema de monitoramento e observabilidade para o backend Aluvi.
Inclui health checks, métricas básicas e alertas.
"""

import time
import psutil
from typing import Dict, Any
from datetime import datetime, timedelta

from .database import db_manager
from .logging import get_logger

logger = get_logger("monitoring")


class HealthChecker:
    """Verificador de saúde do sistema."""

    def __init__(self):
        self.start_time = time.time()
        self.last_health_check = None
        self.health_status = {}

    def check_database(self) -> Dict[str, Any]:
        """Verificar saúde do banco de dados."""
        try:
            start_time = time.time()
            is_healthy = db_manager.health_check()
            response_time = time.time() - start_time

            status = {
                "healthy": is_healthy,
                "response_time": round(response_time * 1000, 2),  # ms
                "timestamp": datetime.now().isoformat()
            }

            if not is_healthy:
                logger.error("Verificação de saúde do banco falhou")
                status["error"] = "Conexão com banco de dados falhou"

            return status

        except Exception as e:
            logger.error(f"Erro na verificação de saúde do banco: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def check_system_resources(self) -> Dict[str, Any]:
        """Verificar recursos do sistema."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao verificar recursos do sistema: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_uptime(self) -> str:
        """Obter tempo de atividade do sistema."""
        uptime_seconds = time.time() - self.start_time
        uptime = timedelta(seconds=int(uptime_seconds))

        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s"

    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Verificação completa de saúde do sistema."""
        self.last_health_check = datetime.now()

        health_data = {
            "timestamp": self.last_health_check.isoformat(),
            "uptime": self.get_uptime(),
            "status": "healthy",
            "checks": {}
        }

        # Verificar banco de dados
        db_health = self.check_database()
        health_data["checks"]["database"] = db_health

        # Verificar recursos do sistema
        system_health = self.check_system_resources()
        health_data["checks"]["system"] = system_health

        # Determinar status geral
        all_healthy = all(
            check.get("healthy", False) if isinstance(check, dict) and "healthy" in check
            else True  # Para checks que não têm campo healthy
            for check in health_data["checks"].values()
        )

        if not all_healthy:
            health_data["status"] = "unhealthy"
            logger.warning("Sistema com problemas de saúde detectados")

        self.health_status = health_data
        return health_data


class MetricsCollector:
    """Coletor de métricas básicas do sistema."""

    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_by_endpoint": {},
            "errors_total": 0,
            "errors_by_type": {},
            "response_times": [],
            "active_connections": 0
        }
        self.start_time = time.time()

    def increment_request(self, endpoint: str = ""):
        """Incrementar contador de requisições."""
        self.metrics["requests_total"] += 1
        if endpoint:
            if endpoint not in self.metrics["requests_by_endpoint"]:
                self.metrics["requests_by_endpoint"][endpoint] = 0
            self.metrics["requests_by_endpoint"][endpoint] += 1

    def increment_error(self, error_type: str = "unknown"):
        """Incrementar contador de erros."""
        self.metrics["errors_total"] += 1
        if error_type not in self.metrics["errors_by_type"]:
            self.metrics["errors_by_type"][error_type] = 0
        self.metrics["errors_by_type"][error_type] += 1

    def record_response_time(self, response_time: float):
        """Registrar tempo de resposta."""
        self.metrics["response_times"].append(response_time)
        # Manter apenas os últimos 1000 tempos de resposta
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

    def set_active_connections(self, count: int):
        """Definir número de conexões ativas."""
        self.metrics["active_connections"] = count

    def get_summary(self) -> Dict[str, Any]:
        """Obter resumo das métricas."""
        response_times = self.metrics["response_times"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            "uptime_seconds": time.time() - self.start_time,
            "requests_total": self.metrics["requests_total"],
            "requests_per_second": self.metrics["requests_total"] / max(time.time() - self.start_time, 1),
            "errors_total": self.metrics["errors_total"],
            "error_rate": self.metrics["errors_total"] / max(self.metrics["requests_total"], 1),
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "active_connections": self.metrics["active_connections"],
            "top_endpoints": sorted(
                self.metrics["requests_by_endpoint"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "timestamp": datetime.now().isoformat()
        }


# Instâncias globais
health_checker = HealthChecker()
metrics_collector = MetricsCollector()

# Funções de conveniência
def get_health_status() -> Dict[str, Any]:
    """Obter status de saúde atual."""
    return health_checker.comprehensive_health_check()

def get_metrics() -> Dict[str, Any]:
    """Obter métricas atuais."""
    return metrics_collector.get_summary()

def log_request(endpoint: str, response_time: float = 0.0):
    """Registrar uma requisição."""
    metrics_collector.increment_request(endpoint)
    if response_time > 0:
        metrics_collector.record_response_time(response_time)

def log_error(error_type: str = "unknown"):
    """Registrar um erro."""
    metrics_collector.increment_error(error_type)

# Middleware para monitoramento automático
class MonitoringMiddleware:
    """Middleware FastAPI para monitoramento automático."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        path = scope.get("path", "")

        # Processar requisição
        try:
            await self.app(scope, receive, send)
            # Sucesso - registrar requisição
            response_time = time.time() - start_time
            log_request(path, response_time)

        except Exception as e:
            # Erro - registrar erro
            response_time = time.time() - start_time
            log_request(path, response_time)
            log_error(type(e).__name__)
            raise