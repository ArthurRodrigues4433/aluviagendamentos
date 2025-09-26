# ================================
# Aluvi - Sistema de Agendamentos
# Dockerfile Multi-stage para produção
# ================================

# Stage 1: Builder
FROM python:3.11-slim as builder

# Instalar dependências de build
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar e instalar requirements
WORKDIR /app
COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime

# Instalar runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar ambiente virtual do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Criar diretórios necessários
RUN mkdir -p /app /app/data /app/logs && \
    chown -R appuser:appuser /app

# Definir diretório de trabalho
WORKDIR /app

# Copiar código fonte
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser run.py ./
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser migrations/ ./migrations/

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    PYTHONPATH=/app

# Criar volume para dados persistentes
VOLUME ["/app/data"]

# Expor porta
EXPOSE 8000

# Health check melhorado
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Trocar para usuário não-root
USER appuser

# Comando de inicialização
CMD ["python", "run.py"]