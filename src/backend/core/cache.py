"""
Sistema de cache Redis para otimização de performance.
Implementa cache para dados frequentes e sessões de autenticação.
"""

import redis
import json
import pickle
from typing import Any, Optional, Union
import os
from datetime import timedelta
from .logging import get_logger

logger = get_logger("cache")


class RedisCache:
    """Cliente Redis para cache de aplicação."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"

        if self.enabled:
            try:
                self.client = redis.from_url(self.redis_url, decode_responses=True)
                self.client.ping()  # Testa conexão
                logger.info("Redis conectado com sucesso")
            except redis.ConnectionError as e:
                logger.error(f"Falha ao conectar com Redis: {e}")
                self.enabled = False
        else:
            self.client = None
            logger.info("Redis desabilitado")

    def is_enabled(self) -> bool:
        """Verifica se o cache está habilitado."""
        return self.enabled and self.client is not None

    def get(self, key: str) -> Optional[Any]:
        """Busca valor do cache."""
        if not self.is_enabled():
            return None

        try:
            value = self.client.get(key)
            if value:
                # Tenta desserializar JSON primeiro, depois pickle
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        return pickle.loads(value.encode('latin1'))
                    except Exception:
                        return value
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar cache para chave {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Armazena valor no cache."""
        if not self.is_enabled():
            return False

        try:
            # Serializa o valor
            if isinstance(value, (dict, list, int, float, str, bool)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = pickle.dumps(value).decode('latin1')

            if ttl_seconds:
                return bool(self.client.setex(key, ttl_seconds, serialized_value))
            else:
                return bool(self.client.set(key, serialized_value))
        except Exception as e:
            logger.error(f"Erro ao armazenar cache para chave {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        if not self.is_enabled():
            return False

        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Erro ao deletar cache para chave {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Verifica se chave existe no cache."""
        if not self.is_enabled():
            return False

        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Erro ao verificar existência da chave {key}: {e}")
            return False

    def expire(self, key: str, ttl_seconds: int) -> bool:
        """Define tempo de vida para uma chave."""
        if not self.is_enabled():
            return False

        try:
            return bool(self.client.expire(key, ttl_seconds))
        except Exception as e:
            logger.error(f"Erro ao definir TTL para chave {key}: {e}")
            return False

    def flush_all(self) -> bool:
        """Limpa todo o cache (use com cuidado!)."""
        if not self.is_enabled():
            return False

        try:
            return bool(self.client.flushall())
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False


# Instância global do cache
cache = RedisCache()


# Funções utilitárias para cache de autenticação
def cache_user_session(user_id: int, token_data: dict, ttl_hours: int = 24):
    """Cache dados da sessão do usuário."""
    key = f"user_session:{user_id}"
    return cache.set(key, token_data, ttl_seconds=ttl_hours * 3600)


def get_cached_user_session(user_id: int) -> Optional[dict]:
    """Busca sessão do usuário no cache."""
    key = f"user_session:{user_id}"
    return cache.get(key)


def invalidate_user_session(user_id: int):
    """Invalida sessão do usuário no cache."""
    key = f"user_session:{user_id}"
    return cache.delete(key)


# Funções utilitárias para cache de dados frequentes
def cache_salon_services(salon_id: int, services: list, ttl_minutes: int = 30):
    """Cache lista de serviços do salão."""
    key = f"salon_services:{salon_id}"
    return cache.set(key, services, ttl_seconds=ttl_minutes * 60)


def get_cached_salon_services(salon_id: int) -> Optional[list]:
    """Busca serviços do salão no cache."""
    key = f"salon_services:{salon_id}"
    return cache.get(key)


def cache_salon_professionals(salon_id: int, professionals: list, ttl_minutes: int = 30):
    """Cache lista de profissionais do salão."""
    key = f"salon_professionals:{salon_id}"
    return cache.set(key, professionals, ttl_seconds=ttl_minutes * 60)


def get_cached_salon_professionals(salon_id: int) -> Optional[list]:
    """Busca profissionais do salão no cache."""
    key = f"salon_professionals:{salon_id}"
    return cache.get(key)


def cache_availability_check(salon_id: int, professional_id: Optional[int],
                           date: str, available_slots: list, ttl_minutes: int = 15):
    """Cache verificação de disponibilidade."""
    key = f"availability:{salon_id}:{professional_id or 'any'}:{date}"
    return cache.set(key, available_slots, ttl_seconds=ttl_minutes * 60)


def get_cached_availability(salon_id: int, professional_id: Optional[int], date: str) -> Optional[list]:
    """Busca disponibilidade no cache."""
    key = f"availability:{salon_id}:{professional_id or 'any'}:{date}"
    return cache.get(key)


# Decorador para cache de funções
def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorador para cache de funções.

    Args:
        ttl_seconds: Tempo de vida do cache em segundos
        key_prefix: Prefixo para a chave do cache
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not cache.is_enabled():
                return func(*args, **kwargs)

            # Gera chave baseada no nome da função e argumentos
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(arg) for arg in args if arg is not None])
            key_parts.extend([f"{k}:{v}" for k, v in kwargs.items() if v is not None])
            cache_key = ":".join(key_parts)

            # Tenta buscar do cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit para {cache_key}")
                return cached_result

            # Executa função e armazena no cache
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(cache_key, result, ttl_seconds)
                logger.debug(f"Cache set para {cache_key}")

            return result
        return wrapper
    return decorator


# Função de health check do Redis
def redis_health_check() -> dict:
    """Verifica saúde da conexão Redis."""
    if not cache.is_enabled():
        return {
            "status": "disabled",
            "message": "Redis não está habilitado"
        }

    try:
        cache.client.ping()
        return {
            "status": "healthy",
            "message": "Redis conectado"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Erro na conexão Redis: {str(e)}"
        }