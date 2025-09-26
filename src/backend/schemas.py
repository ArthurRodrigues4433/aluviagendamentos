from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, Field
from typing import Optional, List
from datetime import datetime, date
from .models.enums import AppointmentStatus

class UsuarioSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    email: str
    senha: str
    ativo: Optional[bool] = True
    admin: Optional[bool] = False
    mensalidade_pago: Optional[bool] = False
    data_vencimento_mensalidade: Optional[date] = None
    senha_temporaria: Optional[bool] = True
    primeiro_login: Optional[bool] = True

class SalonCreateAdmin(BaseModel):
    """Schema para criação de salão pelo administrador"""
    nome: str
    email: Optional[str] = None  # Se não fornecido, será gerado automaticamente

class LoginSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    senha: str

class ChangePasswordSchema(BaseModel):
    """Schema para troca de senha"""
    senha_atual: str
    nova_senha: str

# Esquemas para Cliente
class ClienteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    salon_id: int

class ClienteCreate(BaseModel):
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    salon_id: int
    criado_em: Optional[datetime] = None

class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None

# Esquemas para autenticação de clientes
class ClienteRegister(BaseModel):
    """Schema para registro de cliente"""
    nome: str
    email: str
    telefone: Optional[str] = None
    senha: str
    salon_id: int

class ClienteLogin(BaseModel):
    """Schema para login de cliente"""
    email: str
    senha: str

class ClientePerfil(BaseModel):
    """Schema para perfil do cliente"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    pontos_fidelidade: int
    salon_id: Optional[int] = None

class TokenResponse(BaseModel):
    """Schema para resposta de token"""
    access_token: str
    refresh_token: str
    token_type: str
    role: str  # "cliente" ou "dono"

# Esquemas para Profissional
class ProfissionalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    especialidade: Optional[str] = None
    foto: Optional[str] = None
    salon_id: int
    ativo: bool

class ProfissionalCreate(BaseModel):
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    especialidade: Optional[str] = None
    foto: Optional[str] = None
    salon_id: int

class ProfissionalCreateInput(BaseModel):
    """Schema para criação de profissional sem salon_id - determinado automaticamente pelo backend"""
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    especialidade: Optional[str] = None
    foto: Optional[str] = None

class ProfissionalUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    especialidade: Optional[str] = None
    foto: Optional[str] = None
    ativo: Optional[bool] = None

# Esquemas para Serviço
class ServicoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: Optional[str] = None
    duracao_minutos: int
    preco: float
    pontos_fidelidade: int
    salon_id: int

class ServicoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    descricao: Optional[str] = Field(None, max_length=1000)
    duracao_minutos: int = Field(gt=0, le=480)  # Maior que 0, máximo 8 horas
    preco: float = Field(gt=0)
    pontos_fidelidade: int = Field(ge=0, default=0)  # Não negativo
    salon_id: int = Field(gt=0)

class ServicoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    duracao_minutos: Optional[int] = None
    preco: Optional[float] = None
    pontos_fidelidade: Optional[int] = None

# Esquemas para Agendamento
class AgendamentoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    service_id: int
    professional_id: Optional[int] = None
    salon_id: int
    data_hora: datetime
    status: str
    valor: float
    cliente: Optional[ClienteSchema] = None
    servico: Optional[ServicoSchema] = None
    profissional: Optional[ProfissionalSchema] = None

class AgendamentoCreate(BaseModel):
    client_id: int = Field(gt=0)
    service_id: int = Field(gt=0)
    professional_id: Optional[int] = Field(None, gt=0)
    salon_id: int = Field(gt=0)
    data_hora: datetime
    valor: float = Field(gt=0)

    # Configuração para aceitar strings ISO e converter para datetime
    model_config = ConfigDict(coerce_numbers_to_str=True)

    @field_validator('data_hora', mode='before')
    @classmethod
    def parse_data_hora(cls, v):
        if isinstance(v, str):
            try:
                # Tentar parsear string ISO
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('Formato de data/hora inválido. Use ISO format.')
        return v

class AgendamentoCreateCliente(BaseModel):
    """Schema para criação de agendamento por cliente - client_id é determinado pelo token"""
    service_id: int
    professional_id: Optional[int] = None
    salon_id: int
    data_hora: datetime
    valor: float

    # Configuração para aceitar strings ISO e converter para datetime
    model_config = ConfigDict(coerce_numbers_to_str=True)

    @field_validator('data_hora', mode='before')
    @classmethod
    def parse_data_hora(cls, v):
        if isinstance(v, str):
            try:
                # Tentar parsear string ISO
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('Formato de data/hora inválido. Use ISO format.')
        return v

class AgendamentoUpdate(BaseModel):
    client_id: Optional[int] = None
    service_id: Optional[int] = None
    professional_id: Optional[int] = None
    data_hora: Optional[datetime] = None
    status: Optional[str] = None
    valor: Optional[float] = None

class AgendamentoStatusUpdate(BaseModel):
    """Schema para atualização apenas do status do agendamento"""
    status: str

# Esquema para agendamento público (com criação automática de cliente)
class AgendamentoPublicoCreate(BaseModel):
    nome_cliente: str
    email_cliente: Optional[str] = None
    telefone_cliente: Optional[str] = None
    service_id: int
    professional_id: Optional[int] = None
    salon_id: int
    data_hora: datetime

# Esquemas para Salão (público)
class SalonInfo(BaseModel):
    """Schema para informações públicas do salão"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    telefone: Optional[str] = None
    logo: Optional[str] = None  # URL do logo
    endereco: Optional[str] = None

# Esquemas para atualização de mensalidade
class SubscriptionUpdate(BaseModel):
    """Schema para atualização de status de mensalidade"""
    mensalidade_pago: bool
    data_vencimento: Optional[date] = None

# Esquemas para Relatórios
class RelatorioDashboard(BaseModel):
    total_clientes: int
    total_servicos: int
    total_agendamentos: int
    faturamento_total: float
    agendamentos_hoje: int
    novos_clientes_mes: int
