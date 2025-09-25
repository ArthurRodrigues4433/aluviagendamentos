# Guia de Deploy - Aluvi

Este documento descreve como fazer o deploy do sistema Aluvi em diferentes ambientes.

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Deploy com Docker](#deploy-com-docker)
- [Deploy Manual](#deploy-manual)
- [Configuração do Banco](#configuração-do-banco)
- [Configuração do Servidor Web](#configuração-do-servidor-web)
- [SSL/TLS](#ssltls)
- [Monitoramento](#monitoramento)
- [Backup](#backup)
- [Troubleshooting](#troubleshooting)

## Pré-requisitos

### Sistema Operacional
- Ubuntu 20.04+ ou CentOS 8+
- Windows Server 2019+ (não recomendado para produção)
- macOS (desenvolvimento apenas)

### Dependências
- Python 3.9+
- PostgreSQL 13+
- Redis (opcional, para cache)
- Nginx (reverso proxy)

### Recursos Mínimos
- **CPU**: 1 vCPU
- **RAM**: 1GB
- **Disco**: 10GB SSD
- **Rede**: 100Mbps

### Recursos Recomendados
- **CPU**: 2 vCPU
- **RAM**: 2GB
- **Disco**: 50GB SSD
- **Rede**: 1Gbps

## Configuração do Ambiente

### 1. Atualizar o Sistema

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2. Instalar Python

```bash
# Ubuntu/Debian
sudo apt install python3.9 python3.9-venv python3-pip -y

# CentOS/RHEL
sudo yum install python39 python39-pip -y
```

### 3. Instalar PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib -y
sudo systemctl enable postgresql
sudo systemctl start postgresql

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib -y
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 4. Configurar PostgreSQL

```bash
# Criar usuário e banco
sudo -u postgres psql

CREATE USER aluvi_user WITH PASSWORD 'strong_password_here';
CREATE DATABASE aluvi_prod OWNER aluvi_user;
GRANT ALL PRIVILEGES ON DATABASE aluvi_prod TO aluvi_user;
\q
```

### 5. Instalar Nginx

```bash
# Ubuntu/Debian
sudo apt install nginx -y

# CentOS/RHEL
sudo yum install nginx -y

sudo systemctl enable nginx
sudo systemctl start nginx
```

## Deploy com Docker

### Docker Compose (Recomendado)

1. **Arquivo docker-compose.yml**:

```yaml
version: '3.8'

services:
  aluvi:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://aluvi_user:password@db/aluvi_prod
      - SECRET_KEY=your-secret-key-here
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=aluvi_prod
      - POSTGRES_USER=aluvi_user
      - POSTGRES_PASSWORD=strong_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - aluvi
    restart: unless-stopped

volumes:
  postgres_data:
```

2. **Arquivo Dockerfile**:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY src/ ./src/
COPY scripts/ ./scripts/

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. **Arquivo nginx.conf**:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream aluvi_backend {
        server aluvi:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/ssl/certs/fullchain.pem;
        ssl_certificate_key /etc/ssl/certs/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # API
        location /api/ {
            proxy_pass http://aluvi_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static/ {
            proxy_pass http://aluvi_backend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Frontend SPA
        location / {
            proxy_pass http://aluvi_backend;
            try_files $uri $uri/ /index.html;
        }
    }
}
```

4. **Deploy**:

```bash
# Build e deploy
docker-compose up -d --build

# Verificar status
docker-compose ps

# Logs
docker-compose logs -f aluvi
```

## Deploy Manual

### 1. Clonar e Configurar

```bash
# Clonar repositório
git clone https://github.com/your-org/aluvi.git
cd aluvi

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

```bash
# Arquivo .env
APP_ENV=production
APP_DEBUG=false
DATABASE_URL=postgresql://aluvi_user:password@localhost/aluvi_prod
SECRET_KEY=your-very-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### 3. Executar Migrações

```bash
# Criar tabelas
python -c "from src.backend.core.database import db_manager; db_manager.create_tables()"
```

### 4. Configurar Gunicorn

**Arquivo /etc/systemd/system/aluvi.service**:

```ini
[Unit]
Description=Aluvi Application
After=network.target

[Service]
User=aluvi
Group=aluvi
WorkingDirectory=/path/to/aluvi
Environment="PATH=/path/to/aluvi/venv/bin"
ExecStart=/path/to/aluvi/venv/bin/gunicorn src.backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Recarregar systemd e iniciar serviço
sudo systemctl daemon-reload
sudo systemctl enable aluvi
sudo systemctl start aluvi
```

### 5. Configurar Nginx

**Arquivo /etc/nginx/sites-available/aluvi**:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/aluvi/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/aluvi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL/TLS

### Let's Encrypt (Recomendado)

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx -y

# Gerar certificado
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Renovação automática
sudo crontab -e
# Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Manual

```bash
# Copiar certificados
sudo cp fullchain.pem /etc/ssl/certs/
sudo cp privkey.pem /etc/ssl/private/

# Configurar nginx para SSL
# Ver exemplo no docker-compose.yml acima
```

## Monitoramento

### Health Checks

```bash
# Endpoint de health check
curl http://localhost:8000/health

# Resposta esperada
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### Logs

```bash
# Logs da aplicação
tail -f logs/aluvi.log

# Logs do nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Logs do systemd
journalctl -u aluvi -f
```

### Métricas

```bash
# Instalar prometheus + grafana
sudo apt install prometheus grafana -y

# Configurar exporters
# - node_exporter para métricas do sistema
# - postgres_exporter para métricas do banco
# - custom exporter para métricas da app
```

### Alertas

```bash
# Instalar alertmanager
sudo apt install prometheus-alertmanager -y

# Configurar alertas para:
# - CPU > 80%
# - RAM > 90%
# - Disco > 85%
# - Erros 5xx > 5%
# - Database indisponível
```

## Backup

### Banco de Dados

```bash
# Backup diário
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U aluvi_user -h localhost aluvi_prod > /backups/aluvi_$DATE.sql

# Compactar
gzip /backups/aluvi_$DATE.sql

# Manter apenas últimos 7 dias
find /backups -name "aluvi_*.sql.gz" -mtime +7 -delete
```

### Arquivos

```bash
# Backup de uploads e configurações
tar -czf /backups/uploads_$DATE.tar.gz /path/to/uploads/
tar -czf /backups/config_$DATE.tar.gz /path/to/config/
```

### Automação

```bash
# Crontab para backups
0 2 * * * /path/to/backup-script.sh

# Verificar integridade
0 3 * * * /path/to/verify-backup.sh
```

## Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com Banco

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Testar conexão
psql -U aluvi_user -d aluvi_prod -h localhost
```

#### 2. Aplicação Não Inicia

```bash
# Verificar logs da aplicação
journalctl -u aluvi -n 50

# Verificar variáveis de ambiente
sudo systemctl show aluvi | grep Environment

# Testar manualmente
cd /path/to/aluvi
source venv/bin/activate
python -c "from src.backend.main import app; print('App loaded successfully')"
```

#### 3. Nginx Erro 502

```bash
# Verificar se aplicação está respondendo
curl http://127.0.0.1:8000/health

# Verificar configuração nginx
sudo nginx -t

# Verificar logs nginx
sudo tail -f /var/log/nginx/error.log
```

#### 4. Alto Uso de CPU/Memória

```bash
# Verificar processos
top -p $(pgrep -f gunicorn)

# Verificar número de workers
ps aux | grep gunicorn

# Ajustar número de workers baseado na CPU
# workers = (2 * CPU) + 1
```

#### 5. Lentidão na Aplicação

```bash
# Verificar queries lentas no PostgreSQL
SELECT * FROM pg_stat_activity WHERE state = 'active';

# Verificar índices
SELECT * FROM pg_stat_user_indexes;

# Otimizar queries na aplicação
```

### Comandos Úteis

```bash
# Reiniciar serviços
sudo systemctl restart aluvi nginx postgresql

# Verificar status
sudo systemctl status aluvi nginx postgresql

# Logs em tempo real
journalctl -u aluvi -f

# Backup manual
pg_dump -U aluvi_user aluvi_prod > backup.sql

# Restore
psql -U aluvi_user aluvi_prod < backup.sql
```

## Escalabilidade

### Horizontal Scaling

```yaml
# docker-compose scale
services:
  aluvi:
    deploy:
      replicas: 3
    # Load balancer necessário
```

### Cache com Redis

```python
# Adicionar Redis para cache
import redis

redis_client = redis.Redis(host='redis', port=6379, db=0)

# Cache de queries frequentes
@app.get("/api/services")
@cache(expire=300)
async def get_services():
    return await service_service.get_all()
```

### CDN para Assets

```nginx
# Servir assets do CDN
location /static/ {
    proxy_pass https://cdn.your-domain.com;
    expires 1y;
}
```

## Segurança

### Checklist de Segurança

- [ ] SSL/TLS configurado
- [ ] Firewall ativo (UFW/iptables)
- [ ] Fail2ban instalado
- [ ] Usuário não-root para aplicação
- [ ] SECRET_KEY forte e única
- [ ] Headers de segurança no Nginx
- [ ] Rate limiting ativo
- [ ] Logs de auditoria habilitados
- [ ] Backups automáticos
- [ ] Monitoramento ativo

### Hardening do Servidor

```bash
# Desabilitar root login
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Configurar firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Instalar fail2ban
sudo apt install fail2ban -y
```

---

Para mais informações, consulte a documentação completa ou abra uma issue no repositório.