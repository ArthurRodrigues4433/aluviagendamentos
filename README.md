# Aluvi API - Sistema de Agendamentos para Salões

[![CI/CD Pipeline](https://github.com/your-org/aluvi-api/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/your-org/aluvi-api/actions/workflows/ci-cd.yml)
[![Coverage](https://codecov.io/gh/your-org/aluvi-api/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/aluvi-api)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sistema completo de agendamentos para salões de beleza com arquitetura robusta, monitoramento avançado e CI/CD automatizado.

## 🚀 Funcionalidades

### 👥 **Gestão de Usuários**
- Cadastro e autenticação de donos de salão
- Sistema de administradores
- Controle de permissões baseado em papéis

### 🏪 **Salões**
- Gerenciamento completo de informações do salão
- Configuração de horários de funcionamento
- Personalização de cards de apresentação

### 👨‍💼 **Clientes**
- Cadastro de clientes (anônimos ou registrados)
- Programa de fidelidade com pontos
- Histórico completo de agendamentos

### ✂️ **Serviços**
- Catálogo completo de serviços
- Definição de preços e durações
- Controle de pontos de fidelidade

### 👩‍💼 **Profissionais**
- Cadastro da equipe do salão
- Especialidades e disponibilidade
- Associação com serviços

### 📅 **Agendamentos**
- Sistema completo de reservas
- Validação automática de conflitos
- Controle de ciclo de vida dos agendamentos
- Notificações e lembretes

## 🛠️ **Tecnologias**

- **Backend**: FastAPI (Python 3.11)
- **Banco de Dados**: SQLite (dev) / PostgreSQL (prod)
- **Cache**: Redis
- **Monitoramento**: Prometheus + Grafana
- **Containerização**: Docker
- **CI/CD**: GitHub Actions
- **Testes**: pytest + coverage
- **Documentação**: OpenAPI/Swagger

## 📦 **Instalação**

### Pré-requisitos
- Python 3.11+
- Docker & Docker Compose
- Redis (opcional, para cache)

### Desenvolvimento Local

1. **Clone o repositório**
   ```bash
   git clone https://github.com/your-org/aluvi-api.git
   cd aluvi-api
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. **Execute com Docker Compose (Recomendado)**
   ```bash
   docker-compose up -d
   ```

4. **Ou execute localmente**
   ```bash
   # Com SQLite (desenvolvimento)
   export ENVIRONMENT=development
   uvicorn src.backend.main:app --reload

   # Com PostgreSQL (produção)
   export DATABASE_URL=postgresql://user:password@localhost/aluvi
   export REDIS_ENABLED=true
   export REDIS_URL=redis://localhost:6379/0
   uvicorn src.backend.main:app --host 0.0.0.0 --port 8000
   ```

## 🧪 **Testes**

```bash
# Executar todos os testes
pytest

# Com coverage
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/test_appointment_service.py -v

# Testes de integração
pytest -m integration
```

## 📚 **Documentação da API**

A documentação completa está disponível em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principais

#### Autenticação
- `POST /auth/login` - Login de usuário
- `POST /auth/register` - Registro de novo salão

#### Agendamentos
- `GET /appointments/` - Listar agendamentos
- `POST /appointments/` - Criar agendamento
- `PUT /appointments/{id}/status` - Atualizar status

#### Clientes
- `GET /clients/` - Listar clientes
- `POST /clients/` - Criar cliente
- `POST /clients/register` - Registro de cliente

#### Serviços
- `GET /services/` - Listar serviços
- `POST /services/` - Criar serviço

## 🔧 **Configuração**

### Variáveis de Ambiente

```bash
# Ambiente
ENVIRONMENT=development|production

# Banco de Dados
DATABASE_URL=sqlite:///./aluvi.db
# ou
DATABASE_URL=postgresql://user:password@localhost/aluvi

# Redis (Cache)
REDIS_ENABLED=true|false
REDIS_URL=redis://localhost:6379/0

# Segurança
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 📊 **Monitoramento**

### Prometheus Metrics
- **Endpoint**: `/metrics`
- **Métricas disponíveis**:
  - `http_requests_total` - Total de requisições HTTP
  - `http_request_duration_seconds` - Duração das requisições
  - `db_query_duration_seconds` - Duração das queries
  - `appointments_created_total` - Agendamentos criados
  - `cache_hits_total` - Hits do cache

### Health Checks
- **Endpoint**: `/health`
- Verifica conectividade com banco e Redis

### Grafana Dashboards
Acesse: http://localhost:3000 (admin/admin)

## 🚀 **Deploy**

### Desenvolvimento
```bash
docker-compose up -d
```

### Produção
```bash
# Build da imagem
docker build -t aluvi-api .

# Executar
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  aluvi-api
```

## 🔒 **Segurança**

- ✅ Autenticação JWT com refresh tokens
- ✅ Controle de acesso baseado em papéis
- ✅ Validações de entrada robustas
- ✅ Logs de auditoria completos
- ✅ CORS configurado adequadamente
- ✅ Headers de segurança

## 📈 **Performance**

- ✅ **Eager Loading** - Eliminação de N+1 queries
- ✅ **Cache Redis** - Dados frequentes em cache
- ✅ **Índices otimizados** - Consultas rápidas
- ✅ **Transações seguras** - Rollback automático
- ✅ **Paginacão** - Controle de memória

## 🧪 **Qualidade de Código**

- ✅ **Testes unitários** - Cobertura > 80%
- ✅ **Linting** - flake8, black, isort
- ✅ **Type checking** - mypy
- ✅ **Security scanning** - bandit, safety
- ✅ **CI/CD** - GitHub Actions

## 🤝 **Contribuição**

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 **Suporte**

- **Email**: suporte@aluvi.com
- **Docs**: https://docs.aluvi.com
- **Issues**: [GitHub Issues](https://github.com/your-org/aluvi-api/issues)

---

**Aluvi** - Transformando a gestão de salões de beleza! ✨