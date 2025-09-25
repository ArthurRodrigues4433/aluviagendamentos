# Documentação da API - Aluvi

## Visão Geral

A API do Aluvi segue os princípios REST e utiliza JSON para comunicação. Todos os endpoints requerem autenticação JWT, exceto os marcados como públicos.

**Base URL**: `http://localhost:8000/api/v1`

## Autenticação

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "senha": "password123"
}
```

**Resposta de Sucesso (200)**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "role": "dono"
}
```

**Resposta de Erro (401)**:
```json
{
  "detail": "Email ou senha inválidos"
}
```

### Refresh Token

```http
GET /auth/refresh
Authorization: Bearer <refresh_token>
```

### Logout

```http
POST /auth/logout
Authorization: Bearer <access_token>
```

### Dados do Usuário

```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Resposta**:
```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao@salao.com",
  "ativo": true,
  "admin": false,
  "mensalidade_pago": true
}
```

## Agendamentos

### Listar Agendamentos

```http
GET /appointments
Authorization: Bearer <access_token>
```

**Parâmetros de Query**:
- `status` (opcional): Filtrar por status
- `date_from` (opcional): Data inicial (YYYY-MM-DD)
- `date_to` (opcional): Data final (YYYY-MM-DD)
- `client_id` (opcional): ID do cliente

**Resposta**:
```json
[
  {
    "id": 1,
    "client_id": 1,
    "service_id": 1,
    "professional_id": 1,
    "salon_id": 1,
    "appointment_datetime": "2024-01-15T14:30:00",
    "price": 50.0,
    "status": "scheduled",
    "created_at": "2024-01-10T10:00:00",
    "updated_at": "2024-01-10T10:00:00",
    "client": {
      "id": 1,
      "nome": "Maria Santos",
      "email": "maria@email.com",
      "telefone": "11999999999"
    },
    "service": {
      "id": 1,
      "nome": "Corte de Cabelo",
      "preco": 50.0,
      "duracao_minutos": 60
    },
    "professional": {
      "id": 1,
      "nome": "Ana Costa",
      "especialidade": "Cabeleireira"
    }
  }
]
```

### Criar Agendamento

```http
POST /appointments
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "client_id": 1,
  "service_id": 1,
  "professional_id": 1,
  "appointment_datetime": "2024-01-15T14:30:00",
  "price": 50.0
}
```

### Atualizar Status do Agendamento

```http
PUT /appointments/{id}/status
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "confirmed"
}
```

**Status válidos**:
- `scheduled` - Agendado
- `confirmed` - Confirmado
- `completed` - Concluído
- `cancelled` - Cancelado
- `no_show` - Não compareceu

### Agendamento Público (Sem Login)

```http
POST /appointments/public
Content-Type: application/json

{
  "nome_cliente": "João Silva",
  "email_cliente": "joao@email.com",
  "telefone_cliente": "11999999999",
  "servico_id": 1,
  "professional_id": 1,
  "data_hora": "2024-01-15T14:30:00"
}
```

## Serviços

### Listar Serviços

```http
GET /services
Authorization: Bearer <access_token>
```

**Resposta**:
```json
[
  {
    "id": 1,
    "nome": "Corte de Cabelo",
    "descricao": "Corte moderno com acabamento",
    "preco": 50.0,
    "duracao_minutos": 60,
    "loyalty_points": 10,
    "salon_id": 1,
    "ativo": true
  }
]
```

### Serviços Públicos

```http
GET /services/public
```

Retorna apenas serviços ativos e públicos.

### Criar Serviço

```http
POST /services
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "nome": "Manicure",
  "descricao": "Cuidados completos para unhas",
  "preco": 25.0,
  "duracao_minutos": 45,
  "loyalty_points": 5
}
```

## Profissionais

### Listar Profissionais

```http
GET /professionals
Authorization: Bearer <access_token>
```

### Profissionais Disponíveis

```http
GET /professionals/available/{service_id}
Authorization: Bearer <access_token>
```

Retorna profissionais que podem realizar um serviço específico.

### Criar Profissional

```http
POST /professionals
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "nome": "Carlos Silva",
  "email": "carlos@salao.com",
  "telefone": "11988888888",
  "especialidade": "Barbeiro",
  "is_active": true
}
```

## Clientes

### Listar Clientes

```http
GET /clients
Authorization: Bearer <access_token>
```

### Perfil do Cliente

```http
GET /clients/me
Authorization: Bearer <access_token>
```

### Criar Cliente

```http
POST /clients
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "nome": "Maria Santos",
  "email": "maria@email.com",
  "telefone": "11999999999",
  "salon_id": 1
}
```

### Adicionar Pontos de Fidelidade

```http
POST /clients/{id}/add_points
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "points": 10
}
```

### Resgatar Pontos

```http
POST /clients/{id}/redeem_points
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "points": 50
}
```

## Relatórios

### Dashboard Stats

```http
GET /reports/dashboard
Authorization: Bearer <access_token>
```

**Resposta**:
```json
{
  "total_clientes": 150,
  "total_servicos": 12,
  "total_agendamentos": 45,
  "faturamento_total": 2250.0,
  "agendamentos_hoje": 8,
  "faturamento_mes": 12500.0,
  "taxa_ocupacao": 75.5
}
```

### Relatório de Faturamento

```http
GET /reports/revenue/daily?period=daily
Authorization: Bearer <access_token>
```

**Períodos disponíveis**: `daily`, `weekly`, `monthly`

### Novos Clientes

```http
GET /reports/clients/new?period=monthly
Authorization: Bearer <access_token>
```

### Performance dos Profissionais

```http
GET /reports/performance?period=weekly
Authorization: Bearer <access_token>
```

## Horários de Funcionamento

### Obter Horários

```http
GET /business-hours
Authorization: Bearer <access_token>
```

**Resposta**:
```json
{
  "empresa_id": 1,
  "segunda": {
    "abertura": "08:00",
    "fechamento": "18:00"
  },
  "terca": {
    "abertura": "08:00",
    "fechamento": "18:00"
  },
  // ... outros dias
  "domingo": null  // fechado
}
```

### Atualizar Horários

```http
PUT /business-hours
Authorization: Bearer <access_token>
Content-Type: application/json

[
  {
    "dia": "segunda",
    "abertura": "08:00",
    "fechamento": "18:00"
  },
  {
    "dia": "terca",
    "abertura": "08:00",
    "fechamento": "18:00"
  }
  // ... outros dias
]
```

## Códigos de Status HTTP

- **200 OK**: Requisição bem-sucedida
- **201 Created**: Recurso criado com sucesso
- **400 Bad Request**: Dados inválidos
- **401 Unauthorized**: Token inválido ou ausente
- **403 Forbidden**: Acesso negado
- **404 Not Found**: Recurso não encontrado
- **422 Unprocessable Entity**: Validação falhou
- **500 Internal Server Error**: Erro interno do servidor

## Tratamento de Erros

Todos os erros seguem o formato:

```json
{
  "detail": "Descrição do erro",
  "errors": [
    {
      "field": "email",
      "message": "Email já cadastrado"
    }
  ]
}
```

## Rate Limiting

- **Autenticado**: 1000 requisições por hora
- **Não autenticado**: 100 requisições por hora
- **Login**: 5 tentativas por minuto por IP

## Versionamento

A API utiliza versionamento na URL:
- **v1**: `http://localhost:8000/api/v1/`

## Webhooks (Futuro)

O sistema suporta webhooks para eventos importantes:
- Novo agendamento
- Status alterado
- Pagamento confirmado
- Cliente criado

## SDKs e Bibliotecas

### JavaScript SDK

```javascript
import { ApiService } from './services/api-service.js';

const api = new ApiService();

// Login
const tokens = await api.login('user@example.com', 'password');

// Listar agendamentos
const appointments = await api.getAppointments();
```

### Python SDK (Futuro)

```python
from aluvi_sdk import AluviClient

client = AluviClient(api_key="your-api-key")
appointments = client.appointments.list()
```

## Suporte

Para suporte técnico:
- **Email**: suporte@aluvi.com.br
- **Documentação**: https://docs.aluvi.com.br
- **Issues**: https://github.com/your-org/aluvi/issues