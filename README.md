# Aluvi - Sistema de Agendamento para Salões de Beleza

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLite/PostgreSQL](https://img.shields.io/badge/Database-SQLite/PostgreSQL-orange.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Sistema completo de agendamento para salões de beleza com arquitetura modular, testes automatizados e preparado para produção.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Scripts Disponíveis](#-scripts-disponíveis)
- [Testes](#-testes)
- [Deploy](#-deploy)
- [Monitoramento](#-monitoramento)
- [Segurança](#-segurança)
- [Documentação da API](#-documentação-da-api)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

## 🎯 Visão Geral

O Aluvi é um sistema SaaS completo para gestão de salões de beleza, oferecendo:

- **Agendamento online** com confirmação automática
- **Gestão de clientes** com programa de fidelidade
- **Controle de profissionais** e serviços
- **Relatórios e analytics** para donos
- **Sistema multi-salão** com isolamento de dados
- **Interface responsiva** para desktop e mobile

## ✨ Funcionalidades

### 👤 Para Clientes
- ✅ Agendamento online 24/7
- ✅ Visualização de serviços e preços
- ✅ Histórico de agendamentos
- ✅ Programa de fidelidade
- ✅ Cancelamento e reagendamento

### 💇 Para Profissionais
- ✅ Visualização da agenda diária
- ✅ Confirmação de presença
- ✅ Gestão de horários de trabalho
- ✅ Histórico de atendimentos

### 👨‍💼 Para Donos de Salão
- ✅ Dashboard com estatísticas
- ✅ Gestão completa de clientes
- ✅ Controle de serviços e preços
- ✅ Relatórios de faturamento
- ✅ Gestão de profissionais
- ✅ Configuração de horários

### 👑 Para Administradores
- ✅ Gestão de múltiplos salões
- ✅ Criação de contas de donos
- ✅ Monitoramento do sistema
- ✅ Relatórios globais
- ✅ Configurações do sistema

## 🏗️ Arquitetura

```
src/
├── backend/           # Backend Python/FastAPI
│   ├── core/         # Configurações e database
│   ├── models/       # Modelos SQLAlchemy
│   ├── routes/       # Endpoints da API
│   ├── services/     # Lógica de negócio
│   └── utils/        # Utilitários
├── frontend/         # Frontend JavaScript
│   ├── services/     # Serviços frontend
│   ├── components/   # Componentes reutilizáveis
│   └── pages/        # Páginas HTML
└── tests/           # Testes automatizados
```

### Arquitetura Backend

- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para banco de dados
- **Pydantic**: Validação de dados
- **JWT**: Autenticação stateless
- **SQLite/PostgreSQL**: Suporte a múltiplos bancos

### Arquitetura Frontend

- **Vanilla JavaScript**: Sem frameworks pesados
- **ES6 Modules**: Modularização moderna
- **CSS Grid/Flexbox**: Layout responsivo
- **Componentes reutilizáveis**: Modal, notificações, tabelas

## 📁 Estrutura do Projeto

```
aluvi/
├── .gitignore                    # Arquivos ignorados pelo Git
├── .env                         # Variáveis de ambiente (não versionado)
├── README.md                    # Este arquivo
├── requirements.txt             # Dependências Python
├── requirements-test.txt        # Dependências de teste
├── pytest.ini                   # Configuração do pytest
├── run.py                       # Script de inicialização
├── aluvi.db                     # Banco SQLite (desenvolvimento)
├── data/                        # Dados e backups
│   ├── .env                     # Variáveis de ambiente locais
│   └── aluvi_backup_*.db        # Backups automáticos
├── docs/                        # Documentação
│   ├── API.md                   # Documentação da API
│   └── DEPLOY.md                # Guia de deploy
├── migrations/                  # Scripts de migração
├── scripts/                     # Scripts utilitários
│   ├── __init__.py
│   ├── check_admin_users.py     # Verificar usuários admin
│   ├── check_appointments.py    # Verificar agendamentos
│   ├── check_users.py           # Verificar usuários
│   ├── clear_database.py        # Limpar banco de dados
│   ├── create_admin_test.py     # Criar admin de teste
│   ├── create_test_appointment.py # Criar agendamento teste
│   ├── create_test_appointments.py # Criar múltiplos agendamentos
│   ├── create_test_data.py      # Criar dados de teste
│   ├── create_test_user.py      # Criar usuário teste
│   ├── migrate_add_points.py    # Migração de pontos
│   ├── migrate_add_salon_fields.py # Migração campos salão
│   ├── migrate_database.py      # Executar migrações
│   ├── run-tests.py             # Executar testes
│   ├── set_admin_password.py    # Definir senha admin
│   └── update_past_appointments.py # Atualizar agendamentos passados
├── src/
│   ├── backend/                 # Código backend Python
│   │   ├── __init__.py
│   │   ├── config.py            # Configurações da aplicação
│   │   ├── database.py          # Conexão com banco
│   │   ├── dependencies.py      # Dependências FastAPI
│   │   ├── main.py              # Aplicação principal
│   │   ├── models.py            # Modelos de dados (legado)
│   │   ├── schemas.py           # Schemas Pydantic
│   │   ├── core/                # Configurações core
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # Configurações centrais
│   │   │   ├── database.py      # Gerenciador de banco
│   │   │   ├── logging.py       # Sistema de logging
│   │   │   └── monitoring.py    # Monitoramento e health checks
│   │   ├── models/              # Modelos SQLAlchemy
│   │   │   ├── __init__.py
│   │   │   ├── appointment.py   # Modelo de agendamento
│   │   │   ├── audit.py         # Modelo de auditoria
│   │   │   ├── base.py          # Modelos base
│   │   │   ├── business_hours.py # Horários comerciais
│   │   │   ├── client.py        # Modelo de cliente
│   │   │   ├── enums.py         # Enums do sistema
│   │   │   ├── professional.py  # Modelo de profissional
│   │   │   ├── service.py       # Modelo de serviço
│   │   │   └── user.py          # Modelo de usuário
│   │   ├── routes/              # Endpoints da API
│   │   │   ├── __init__.py
│   │   │   ├── appointments.py  # Rotas de agendamentos
│   │   │   ├── auth.py          # Rotas de autenticação
│   │   │   ├── business_hours.py # Rotas de horários
│   │   │   ├── clients.py       # Rotas de clientes
│   │   │   ├── monitoring.py    # Rotas de monitoramento
│   │   │   ├── professionals.py # Rotas de profissionais
│   │   │   ├── reports.py       # Rotas de relatórios
│   │   │   ├── salons.py        # Rotas de salões
│   │   │   └── services.py      # Rotas de serviços
│   │   ├── services/            # Lógica de negócio
│   │   │   ├── __init__.py
│   │   │   └── auth_service.py  # Serviço de autenticação
│   │   └── utils/               # Utilitários (se existir)
│   ├── frontend/                # Código frontend
│   │   ├── app.js               # Aplicação principal frontend
│   │   ├── assets/              # Assets estáticos
│   │   │   ├── style.css        # Estilos adicionais
│   │   │   └── styles.css       # Estilos principais
│   │   ├── components/          # Componentes reutilizáveis
│   │   │   ├── __init__.js
│   │   │   ├── modal.js         # Componente modal
│   │   │   └── notification-manager.js # Gerenciador notificações
│   │   ├── pages/               # Páginas HTML
│   │   │   ├── change-password.html # Alterar senha
│   │   │   ├── dashboard-admin.html # Dashboard admin
│   │   │   ├── dashboard-cliente.html # Dashboard cliente
│   │   │   ├── dashboard-dono.html # Dashboard dono
│   │   │   ├── index.html       # Página inicial
│   │   │   ├── login.html       # Login
│   │   │   ├── register.html    # Registro
│   │   │   └── salon-selection.html # Seleção de salão
│   │   ├── services/            # Serviços frontend
│   │   │   ├── __init__.js
│   │   │   ├── api-service.js   # Serviço de API
│   │   │   ├── auth-guard.js    # Guarda de autenticação
│   │   │   ├── config.js        # Configurações frontend
│   │   │   ├── formatter.js     # Utilitários de formatação
│   │   │   ├── salon-manager.js # Gerenciador de salão
│   │   │   └── ui-utils.js      # Utilitários de UI
│   │   └── utils/               # Utilitários frontend
│   └── tests/                   # Testes
│       ├── __init__.py
│       ├── conftest.py          # Configuração de testes
│       ├── test_auth_service.py # Testes auth
│       ├── test_models.py       # Testes modelos
│       └── frontend/            # Testes frontend
│           ├── test_tabs.js
│           ├── test-login.js
│           └── TESTE_HORARIOS.md
└── tests/                      # Testes adicionais
    ├── __init__.py
    └── ... (outros arquivos de teste)
```

## 🛠️ Tecnologias

### Backend
- **Python 3.9+**
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Pydantic** - Validação
- **JWT** - Autenticação
- **SQLite/PostgreSQL** - Banco de dados

### Frontend
- **JavaScript ES6+**
- **HTML5/CSS3**
- **Fetch API** - Requisições HTTP
- **LocalStorage/SessionStorage** - Armazenamento local

### Desenvolvimento
- **pytest** - Testes
- **Black** - Formatação de código
- **Flake8** - Linting
- **pre-commit** - Hooks de git

## 🚀 Instalação

### Pré-requisitos

- Python 3.9 ou superior
- Node.js 16+ (opcional, para desenvolvimento frontend)
- PostgreSQL (opcional, para produção)

### Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/your-org/aluvi.git
cd aluvi

# Instale as dependências
pip install -r requirements.txt

# Para desenvolvimento, instale também os testes
pip install -r requirements-test.txt
```

### Configuração do Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite as configurações
nano .env
```

## ⚙️ Configuração

### Variáveis de Ambiente

```env
# Aplicação
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-here

# Banco de dados
DATABASE_URL=sqlite:///./aluvi.db
# Para produção: DATABASE_URL=postgresql://user:pass@localhost/aluvi

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Configuração do Banco

```bash
# Para desenvolvimento (SQLite)
export DATABASE_URL="sqlite:///./aluvi.db"

# Para produção (PostgreSQL)
export DATABASE_URL="postgresql://user:password@localhost/aluvi_prod"
```

## 🎮 Uso

### Iniciando o Servidor

```bash
# Desenvolvimento
python -m uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000

# Produção
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Acessando a Aplicação

- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Primeiro Uso

1. Acesse http://localhost:8000
2. Crie uma conta de administrador
3. Configure seu salão
4. Adicione serviços e profissionais
5. Comece a aceitar agendamentos!

## 🔧 Scripts Disponíveis

O projeto inclui vários scripts utilitários na pasta `scripts/` para facilitar o desenvolvimento e manutenção:

### Scripts de Banco de Dados
```bash
# Limpar banco de dados completamente
python scripts/clear_database.py

# Executar migrações do banco
python scripts/migrate_database.py

# Adicionar campos de pontos aos clientes
python scripts/migrate_add_points.py

# Adicionar campos específicos do salão
python scripts/migrate_add_salon_fields.py
```

### Scripts de Dados de Teste
```bash
# Criar dados de teste básicos
python scripts/create_test_data.py

# Criar usuário de teste
python scripts/create_test_user.py

# Criar agendamento de teste
python scripts/create_test_appointment.py

# Criar múltiplos agendamentos de teste
python scripts/create_test_appointments.py

# Criar admin de teste
python scripts/create_admin_test.py
```

### Scripts de Verificação
```bash
# Verificar usuários administradores
python scripts/check_admin_users.py

# Verificar usuários do sistema
python scripts/check_users.py

# Verificar agendamentos
python scripts/check_appointments.py
```

### Scripts de Segurança
```bash
# Definir senha do administrador
python scripts/set_admin_password.py

# Verificar segurança multi-salão
python scripts/test_multi_salon_security.py
```

### Scripts de Manutenção
```bash
# Limpar agendamentos antigos sem presença
python scripts/cleanup_old_no_shows.py

# Atualizar agendamentos passados
python scripts/update_past_appointments.py
```

### Como Executar Scripts

```bash
# Tornar scripts executáveis (Linux/Mac)
chmod +x scripts/*.py

# Executar script específico
python scripts/nome_do_script.py

# Ou usando o run.py principal
python run.py
```

## 🧪 Testes

### Executando Testes

```bash
# Todos os testes
python scripts/run-tests.py all

# Apenas testes unitários
python scripts/run-tests.py unit

# Testes com cobertura
python scripts/run-tests.py all --coverage

# Testes de integração
python scripts/run-tests.py integration

# Relatório de cobertura
python scripts/run-tests.py coverage
```

### Estrutura de Testes

```
tests/
├── conftest.py           # Configuração e fixtures
├── test_auth_service.py  # Testes do serviço de auth
├── test_models.py        # Testes dos modelos
└── test_api_*.py         # Testes dos endpoints
```

## 🚢 Deploy

### Docker

```bash
# Build da imagem
docker build -t aluvi .

# Executar container
docker run -p 8000:8000 -e DATABASE_URL="sqlite:///./aluvi.db" aluvi
```

### Docker Compose

```yaml
version: '3.8'
services:
  aluvi:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/aluvi
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=aluvi
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

### Produção com Gunicorn

```bash
# Instalar gunicorn
pip install gunicorn

# Executar com gunicorn
gunicorn src.backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📊 Monitoramento

### Health Checks

O sistema inclui endpoints de monitoramento para verificar a saúde da aplicação:

```bash
# Status geral do sistema
curl http://localhost:8000/health

# Status do banco de dados
curl http://localhost:8000/health/database

# Status dos recursos do sistema
curl http://localhost:8000/health/system
```

### Métricas

```bash
# Métricas detalhadas (requer autenticação admin)
curl -H "Authorization: Bearer <token>" http://localhost:8000/metrics
```

### Logs

Os logs são estruturados e incluem:
- Logs de aplicação (`logs/aluvi.log`)
- Logs de erro (`logs/error.log`)
- Logs de auditoria (ações importantes do sistema)

### Monitoramento em Tempo Real

- **Uptime**: Tempo de atividade do sistema
- **Requisições**: Contador de requests por endpoint
- **Erros**: Taxa de erro e tipos de erro
- **Performance**: Tempos de resposta médios
- **Recursos**: CPU, memória e disco

## 🔒 Segurança

### Autenticação e Autorização

- **JWT Tokens**: Autenticação stateless com refresh tokens
- **Blacklist de Tokens**: Invalidação de tokens após logout
- **Roles Hierárquicos**: Admin > Owner > Client
- **Isolamento Multi-tenant**: Dados segregados por salão

### Recursos de Segurança

- **Hash de Senhas**: bcrypt com salt automático
- **CORS**: Configurado para domínios específicos
- **Rate Limiting**: Proteção contra abuso (implementação futura)
- **Auditoria**: Log completo de todas as ações
- **Validação de Dados**: Pydantic para entrada/saída

### Boas Práticas de Segurança

1. **Senhas Fortes**: Mínimo 6 caracteres, força mudança no primeiro login
2. **Tokens Expiráveis**: Access tokens curtos, refresh tokens longos
3. **HTTPS**: Sempre use SSL em produção
4. **Variáveis de Ambiente**: Nunca commite secrets
5. **Atualizações**: Mantenha dependências atualizadas

### Verificações de Segurança

```bash
# Verificar isolamento multi-salão
python scripts/test_multi_salon_security.py

# Verificar usuários administradores
python scripts/check_admin_users.py
```

## 📚 Documentação da API

### Autenticação

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "senha": "password"
}
```

### Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/auth/login` | Login de usuário |
| GET | `/auth/me` | Dados do usuário logado |
| GET | `/appointments` | Lista agendamentos |
| POST | `/appointments` | Criar agendamento |
| GET | `/services` | Lista serviços |
| GET | `/professionals` | Lista profissionais |
| GET | `/reports/dashboard` | Estatísticas dashboard |

### Documentação Interativa

Acesse http://localhost:8000/docs para a documentação interativa da API com Swagger UI.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código

- **Backend**: Black + Flake8
- **Frontend**: ESLint + Prettier
- **Commits**: Conventional Commits
- **Testes**: pytest com cobertura > 80%

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🙏 Agradecimentos

- FastAPI por ser um framework incrível
- SQLAlchemy pela flexibilidade
- Comunidade open source

---

**Feito com ❤️ para salões de beleza em todo o Brasil**