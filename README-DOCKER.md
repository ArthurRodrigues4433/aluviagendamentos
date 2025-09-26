# 🚀 Aluvi - Ambiente Docker Completo

Sistema de Agendamentos SaaS com infraestrutura completa em Docker.

## 📋 Visão Geral da Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx (80)    │    │ Backend API     │    │   PostgreSQL    │
│   - SPA Frontend│◄──►│   FastAPI       │◄──►│   Database      │
│   - Load Balance│    │   (8000)        │    │   (5432)        │
│   - SSL Ready   │    │   - Metrics     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │   Prometheus    │    │     Grafana     │
│   Cache (6379)  │    │   Metrics       │    │   Dashboards    │
│                 │    │   (9090)        │    │   (3000)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Loki       │    │   Promtail      │    │   Node Exporter │
│   Log Storage   │    │   Log Shipping  │    │   System Metrics│
│   (3100)        │    │                 │    │   (9100)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Pré-requisitos

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: Para clonar o repositório
- **4GB RAM** mínimo recomendado

## 🚀 Início Rápido

### 1. Clone e Configure

```bash
# Clone o repositório
git clone <seu-repositorio>
cd aluvi-projeto

# Copie o arquivo de ambiente
cp .env.example .env

# Edite as variáveis de ambiente (opcional)
nano .env
```

### 2. Inicie Todos os Serviços

```bash
# Desenvolvimento (com rebuild)
docker-compose up --build

# Produção (background)
docker-compose up -d

# Com logs
docker-compose up -d && docker-compose logs -f
```

### 3. Acesse a Aplicação

- **Frontend**: http://localhost
- **API Docs**: http://localhost/api/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Banco**: localhost:5432 (aluvi_user/aluvi_password_2024)

## 📊 Serviços Disponíveis

### 🖥️ Frontend (Nginx)
- **Porta**: 80
- **Arquivos**: `src/frontend/`
- **PWA**: Manifest e Service Worker incluídos
- **SSL**: Pronto para HTTPS

### 🔧 Backend API (FastAPI)
- **Porta**: 8000
- **Documentação**: `/api/docs`
- **Métricas**: `/metrics`
- **Health Check**: `/health`

### 🗄️ Banco de Dados (PostgreSQL)
- **Porta**: 5432
- **Usuário**: aluvi_user
- **Senha**: aluvi_password_2024
- **Database**: aluvi
- **Volume**: `postgres_data`

### ⚡ Cache (Redis)
- **Porta**: 6379
- **Senha**: aluvi_cache_2024
- **Volume**: `redis_data`

### 📈 Monitoramento

#### Prometheus
- **Porta**: 9090
- **Métricas**: API, DB, Redis, Nginx
- **Config**: `monitoring/prometheus.yml`

#### Grafana
- **Porta**: 3000
- **Usuário**: admin
- **Senha**: admin (mude em produção!)
- **Dashboards**: Auto-provisionados

#### Loki + Promtail
- **Loki**: 3100 (interface de logs)
- **Logs**: Centralizados de todos os serviços

## 🔧 Comandos Úteis

### Gerenciamento Básico

```bash
# Ver status dos serviços
docker-compose ps

# Ver logs
docker-compose logs -f [serviço]

# Parar tudo
docker-compose down

# Limpar volumes
docker-compose down -v
```

### Desenvolvimento

```bash
# Rebuild apenas backend
docker-compose up --build backend

# Executar testes
docker-compose exec backend pytest

# Acessar shell do container
docker-compose exec backend bash

# Ver logs do banco
docker-compose logs db
```

### Produção

```bash
# Deploy em produção
docker-compose -f docker-compose.yml up -d

# Backup do banco
docker-compose exec db pg_dump -U aluvi_user aluvi > backup.sql

# Restore do banco
docker-compose exec -T db psql -U aluvi_user aluvi < backup.sql
```

### Monitoramento

```bash
# Ver métricas no Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Health check da API
curl http://localhost/health

# Status do banco
docker-compose exec db pg_isready -U aluvi_user -d aluvi
```

## 🔒 Segurança

### Variáveis de Ambiente
```bash
# Gere uma chave secreta segura
openssl rand -hex 32

# Configure no .env
SECRET_KEY=sua-chave-super-secreta-aqui
```

### SSL/HTTPS (Opcional)
```bash
# Coloque certificados em nginx/ssl/
# cert.pem e key.pem

# Reinicie nginx
docker-compose restart nginx
```

### Backup Automático
```bash
# Script de backup (adicione ao crontab)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec db pg_dump -U aluvi_user aluvi > backup_$DATE.sql
```

## 🐛 Troubleshooting

### Problemas Comuns

**Portas ocupadas:**
```bash
# Verifique portas em uso
netstat -tulpn | grep :80
netstat -tulpn | grep :8000

# Mude portas no docker-compose.yml
ports:
  - "8080:80"    # Muda nginx para 8080
  - "8001:8000"  # Muda API para 8001
```

**Banco não conecta:**
```bash
# Verifique se o container está saudável
docker-compose ps db

# Veja logs do banco
docker-compose logs db

# Reset do banco
docker-compose down -v && docker-compose up -d db
```

**Frontend não carrega:**
```bash
# Verifique arquivos estáticos
docker-compose exec nginx ls -la /var/www/html

# Logs do nginx
docker-compose logs nginx
```

### Debug Avançado

```bash
# Ver todos os logs
docker-compose logs

# Inspecionar container
docker-compose exec backend sh

# Ver uso de recursos
docker stats

# Limpar tudo (CUIDADO!)
docker system prune -a --volumes
```

## 📈 Escalabilidade

### Load Balancing
```yaml
# Adicione ao docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

### Banco de Dados
```yaml
# Para produção, considere:
# - Connection pooling (PgBouncer)
# - Read replicas
# - Backup automático
# - Monitoring avançado
```

## 🚀 Deploy em Produção

### 1. Servidor
```bash
# Instale Docker e Docker Compose
curl -fsSL https://get.docker.com | sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configuração
```bash
# Clone e configure
git clone <repo>
cd aluvi-projeto
cp .env.example .env

# Configure produção
nano .env
# DATABASE_URL=postgresql://user:pass@prod-db:5432/aluvi
# SECRET_KEY=chave-producao-super-secreta
```

### 3. Deploy
```bash
# Build e deploy
docker-compose up --build -d

# Configure nginx reverso (se necessário)
# Configure SSL com Let's Encrypt
```

### 4. Monitoramento
```bash
# Configure alertas no Grafana
# Configure backups automáticos
# Configure log rotation
```

## 📚 Documentação Adicional

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

## 🤝 Suporte

Para problemas específicos:

1. **Verifique logs**: `docker-compose logs [serviço]`
2. **Health checks**: `curl http://localhost/health`
3. **Documentação**: README.md e comentários no código
4. **Issues**: Abra uma issue no repositório

---

**🎉 Pronto! Seu ambiente Docker está configurado e rodando!**

Acesse http://localhost e comece a usar seu sistema de agendamentos! 🚀