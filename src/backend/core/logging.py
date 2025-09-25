"""
Sistema de logging estruturado para o backend Aluvi.
Configura logging com diferentes níveis, formatadores e handlers.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .config import logging as logging_config


class AluviLogger:
    """Logger personalizado para o sistema Aluvi."""

    def __init__(self, name: str = "aluvi"):
        self.logger = logging.getLogger(name)
        self._configured = False

    def configure(self, level: Optional[str] = None, log_file: Optional[str] = None):
        """Configurar o logger com nível e arquivo de log especificados."""
        if self._configured:
            return

        # Usar configurações padrão se não especificadas
        level = level or logging_config.LEVEL
        log_file = log_file or logging_config.LOG_FILE

        # Converter string de nível para constante logging
        numeric_level = getattr(logging, level.upper(), logging.INFO)

        # Configurar logger
        self.logger.setLevel(numeric_level)

        # Remover handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Formato estruturado para logs
        formatter = logging.Formatter(logging_config.FORMAT)

        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Handler para arquivo (com rotação)
        try:
            # Criar diretório de logs se não existir
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        except Exception as e:
            # Se não conseguir criar handler de arquivo, continuar sem ele
            self.logger.warning(f"Não foi possível configurar logging para arquivo: {e}")

        # Handler específico para erros
        try:
            error_log_path = Path(logging_config.ERROR_LOG_FILE)
            error_log_path.parent.mkdir(parents=True, exist_ok=True)

            error_handler = logging.handlers.RotatingFileHandler(
                logging_config.ERROR_LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=3
            )
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
                'Arquivo: %(filename)s:%(lineno)d\n'
                'Função: %(funcName)s\n'
                'Processo: %(process)d Thread: %(thread)d\n'
                '---\n'
            )
            error_handler.setFormatter(error_formatter)
            self.logger.addHandler(error_handler)

        except Exception as e:
            self.logger.warning(f"Não foi possível configurar logging de erros: {e}")

        self._configured = True
        self.logger.info(f"Logger configurado com nível {level}")

    def get_logger(self) -> logging.Logger:
        """Retornar instância do logger configurado."""
        if not self._configured:
            self.configure()
        return self.logger


# Instância global do logger
logger_instance = AluviLogger()

# Função de conveniência para obter logger
def get_logger(name: str = "aluvi") -> logging.Logger:
    """Obter logger configurado para o módulo especificado."""
    if name != "aluvi":
        # Criar logger filho para módulos específicos
        child_logger = AluviLogger(name)
        child_logger.configure()
        return child_logger.get_logger()
    else:
        return logger_instance.get_logger()


# Configurar logger padrão na importação
logger_instance.configure()