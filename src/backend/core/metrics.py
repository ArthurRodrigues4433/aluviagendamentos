"""
Métricas Prometheus para monitoramento da aplicação.
Fornece métricas de performance, uso e saúde do sistema.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
from typing import Callable
import functools


# Métricas de HTTP
http_requests_total = Counter(
    'http_requests_total',
    'Total de requisições HTTP',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Duração das requisições HTTP em segundos',
    ['method', 'endpoint']
)

# Métricas de Banco de Dados
db_connections_active = Gauge(
    'db_connections_active',
    'Número de conexões ativas do banco de dados'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Duração das queries do banco de dados',
    ['operation']
)

# Métricas de Negócio
appointments_created_total = Counter(
    'appointments_created_total',
    'Total de agendamentos criados',
    ['salon_id']
)

appointments_completed_total = Counter(
    'appointments_completed_total',
    'Total de agendamentos concluídos',
    ['salon_id']
)

clients_registered_total = Counter(
    'clients_registered_total',
    'Total de clientes registrados',
    ['salon_id']
)

# Métricas de Sistema
memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Uso de memória em bytes'
)

cpu_usage_percent = Gauge(
    'cpu_usage_percent',
    'Uso de CPU em porcentagem'
)

# Métricas de Cache (quando implementado)
cache_hits_total = Counter(
    'cache_hits_total',
    'Total de hits no cache'
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total de misses no cache'
)


def metrics_middleware(request, call_next):
    """
    Middleware para coletar métricas de HTTP.
    """
    start_time = time.time()

    response = call_next(request)

    # Coleta métricas da requisição
    duration = time.time() - start_time

    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response


def track_db_query(operation: str):
    """
    Decorador para rastrear queries do banco de dados.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                db_query_duration_seconds.labels(operation=operation).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(operation=f"{operation}_error").observe(duration)
                raise e
        return wrapper
    return decorator


def get_metrics():
    """
    Endpoint para expor métricas Prometheus.
    """
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


def update_system_metrics():
    """
    Atualiza métricas do sistema (memória, CPU).
    Deve ser chamado periodicamente.
    """
    import psutil
    import os

    # Memória
    process = psutil.Process(os.getpid())
    memory_usage_bytes.set(process.memory_info().rss)

    # CPU (último minuto)
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_usage_percent.set(cpu_percent)


# Funções utilitárias para incrementar contadores de negócio
def increment_appointment_created(salon_id: int):
    """Incrementa contador de agendamentos criados."""
    appointments_created_total.labels(salon_id=salon_id).inc()


def increment_appointment_completed(salon_id: int):
    """Incrementa contador de agendamentos concluídos."""
    appointments_completed_total.labels(salon_id=salon_id).inc()


def increment_client_registered(salon_id: int):
    """Incrementa contador de clientes registrados."""
    clients_registered_total.labels(salon_id=salon_id).inc()


def increment_cache_hit():
    """Incrementa contador de cache hits."""
    cache_hits_total.inc()


def increment_cache_miss():
    """Incrementa contador de cache misses."""
    cache_misses_total.inc()