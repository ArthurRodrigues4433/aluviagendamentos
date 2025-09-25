from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from .. import models, schemas
from ..config import bcrypt_context
from ..dependencies import verificar_token
from datetime import timedelta
from ..routes.auth import criar_token

router = APIRouter()

# ========== PERFIL E FIDELIDADE ==========

@router.get("/profile", response_model=schemas.ClientePerfil)
def get_client_profile(db: Session = Depends(get_db), cliente: models.Cliente = Depends(verificar_token)):
    """
    Retorna perfil do cliente logado com pontos de fidelidade.
    Requer autenticação de cliente (role: "cliente").
    """
    print(f"[CLIENTE ME] Cliente encontrado: ID={cliente.id}, Nome={cliente.nome}")
    print(f"[CLIENTE ME] Pontos fidelidade: {getattr(cliente, 'pontos_fidelidade', 'N/A')}")
    print(f"[CLIENTE ME] Email: {cliente.email}, Telefone: {cliente.telefone}, Salon_id: {cliente.salon_id}")

    # Retornar dados básicos do cliente
    try:
        pontos_fidelidade = getattr(cliente, 'pontos_fidelidade', None)
        if pontos_fidelidade is None:
            pontos_fidelidade = 0

        response_data = {
            "id": cliente.id or 0,
            "nome": cliente.nome or "Cliente",
            "email": cliente.email,
            "telefone": cliente.telefone,
            "pontos_fidelidade": pontos_fidelidade,
            "salon_id": cliente.salon_id
        }

        print(f"[CLIENTE ME] Dados antes da validação Pydantic: {response_data}")

        # Tentar criar o schema para ver se há erro de validação
        try:
            validated_data = schemas.ClientePerfil(**response_data)
            print(f"[CLIENTE ME] Validação Pydantic OK: {validated_data}")
            return validated_data
        except Exception as validation_error:
            print(f"[CLIENTE ME] Erro de validação Pydantic: {str(validation_error)}")
            print(f"[CLIENTE ME] Tipos dos dados: id={type(response_data['id'])}, nome={type(response_data['nome'])}, email={type(response_data['email'])}, telefone={type(response_data['telefone'])}, pontos_fidelidade={type(response_data['pontos_fidelidade'])}, salon_id={type(response_data['salon_id'])}")
            raise validation_error

    except Exception as e:
        print(f"[CLIENTE ME] Erro ao processar dados do cliente: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar dados do cliente")

@router.get("/me", response_model=schemas.ClientePerfil)
def get_client_me(db: Session = Depends(get_db), cliente: models.Cliente = Depends(verificar_token)):
    """
    Retorna perfil do cliente logado (alias para /profile).
    Requer autenticação de cliente (role: "cliente").
    """
    print(f"[CLIENTE ME] Cliente encontrado: ID={cliente.id}, Nome={cliente.nome}")
    print(f"[CLIENTE ME] Pontos fidelidade: {getattr(cliente, 'pontos_fidelidade', 'N/A')}")
    print(f"[CLIENTE ME] Email: {cliente.email}, Telefone: {cliente.telefone}, Salon_id: {cliente.salon_id}")

    # Retornar dados básicos do cliente
    try:
        pontos_fidelidade = getattr(cliente, 'pontos_fidelidade', None)
        if pontos_fidelidade is None:
            pontos_fidelidade = 0

        response_data = {
            "id": cliente.id or 0,
            "nome": cliente.nome or "Cliente",
            "email": cliente.email,
            "telefone": cliente.telefone,
            "pontos_fidelidade": pontos_fidelidade,
            "salon_id": cliente.salon_id
        }

        print(f"[CLIENTE ME] Dados antes da validação Pydantic: {response_data}")

        # Tentar criar o schema para ver se há erro de validação
        try:
            validated_data = schemas.ClientePerfil(**response_data)
            print(f"[CLIENTE ME] Validação Pydantic OK: {validated_data}")
            return validated_data
        except Exception as validation_error:
            print(f"[CLIENTE ME] Erro de validação Pydantic: {str(validation_error)}")
            print(f"[CLIENTE ME] Tipos dos dados: id={type(response_data['id'])}, nome={type(response_data['nome'])}, email={type(response_data['email'])}, telefone={type(response_data['telefone'])}, pontos_fidelidade={type(response_data['pontos_fidelidade'])}, salon_id={type(response_data['salon_id'])}")
            raise validation_error

    except Exception as e:
        print(f"[CLIENTE ME] Erro ao processar dados do cliente: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar dados do cliente")

# ========== ESTATÍSTICAS DO CLIENTE ==========

@router.get("/stats")
def get_client_stats(db: Session = Depends(get_db), usuario = Depends(verificar_token)):
    """
    Retorna estatísticas do cliente para o dashboard.
    Inclui: total agendamentos, pontos de fidelidade, próximos agendamentos.
    Requer autenticação de cliente (role: "cliente").
    """
    try:
        # Verificar se é um cliente baseado no role
        user_role = getattr(usuario, 'role', None)
        if user_role != "cliente":
            raise HTTPException(status_code=403, detail="Acesso negado - apenas clientes")

        # Buscar cliente pelo ID do usuário
        cliente = db.query(models.Cliente).filter(models.Cliente.id == usuario.id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        # Total de agendamentos realizados (concluídos)
        total_appointments = db.query(models.Agendamento).filter(
            models.Agendamento.client_id == cliente.id,
            models.Agendamento.status == "concluido"
        ).count()

        # Pontos de fidelidade
        loyalty_points = getattr(cliente, 'pontos_fidelidade', 0) or 0

        # Próximos agendamentos (futuros, não cancelados)
        from datetime import datetime
        now = datetime.now()
        upcoming_appointments = db.query(models.Agendamento).filter(
            models.Agendamento.client_id == cliente.id,
            models.Agendamento.appointment_datetime > now,
            models.Agendamento.status.in_(["agendado", "confirmed", "pending"])
        ).count()

        return {
            "total_appointments": total_appointments,
            "loyalty_points": loyalty_points,
            "upcoming_appointments": upcoming_appointments
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CLIENT STATS] Erro ao buscar estatísticas: {str(e)}")
        # Retorna valores padrão em caso de erro para não quebrar o dashboard
        return {
            "total_appointments": 0,
            "loyalty_points": 0,
            "upcoming_appointments": 0
        }

@router.get("/dashboard-data")
def get_client_dashboard_data(db: Session = Depends(get_db), cliente: models.Cliente = Depends(verificar_token)):
    """
    Retorna TODOS os dados necessários para o dashboard do cliente em uma única requisição.
    Otimiza performance reduzindo múltiplas chamadas de API.
    Inclui: perfil, estatísticas, agendamentos, histórico.

    Validações de segurança:
    - Verifica se usuário é cliente (feito pela dependência verificar_token)
    - Garante que cliente existe
    - Filtra todos os dados pelo salon_id do cliente (isolamento de dados)
    """
    print(f"[DASHBOARD-DATA] Função chamada para cliente ID={cliente.id if cliente else 'None'}, salon_id={cliente.salon_id if cliente else 'None'}")
    try:

        # Verificar se cliente tem salon_id válido
        salon_id = cliente.salon_id  # type: ignore
        if not salon_id:  # type: ignore
            raise HTTPException(status_code=400, detail="Cliente não está associado a nenhum salão")

        # 1. DADOS DO PERFIL
        profile_data = {
            "id": cliente.id,
            "nome": cliente.nome,
            "email": cliente.email,
            "telefone": cliente.telefone,
            "pontos_fidelidade": getattr(cliente, 'pontos_fidelidade', 0) or 0,
            "salon_id": cliente.salon_id
        }

        # 2. ESTATÍSTICAS
        from datetime import datetime
        now = datetime.now()

        print(f"[DASHBOARD-DATA] Calculando estatísticas para cliente {cliente.id}, salon_id {cliente.salon_id}")

        # Debug: verificar todos os agendamentos do cliente
        all_client_appointments = db.query(models.Agendamento).filter(
            models.Agendamento.client_id == cliente.id
        ).all()
        print(f"[DASHBOARD-DATA] DEBUG - Todos os agendamentos do cliente {cliente.id}: {len(all_client_appointments)}")
        for apt in all_client_appointments:
            print(f"[DASHBOARD-DATA] DEBUG - Agendamento ID {apt.id}: status='{apt.status}', data='{apt.appointment_datetime}'")

        total_appointments = db.query(models.Agendamento).filter(
            models.Agendamento.client_id == cliente.id,
            models.Agendamento.status == "concluido"
        ).count()
        print(f"[DASHBOARD-DATA] Total de agendamentos concluídos: {total_appointments}")

        loyalty_points = getattr(cliente, 'pontos_fidelidade', 0) or 0
        print(f"[DASHBOARD-DATA] Pontos de fidelidade: {loyalty_points}")

        upcoming_appointments_count = db.query(models.Agendamento).filter(
            models.Agendamento.client_id == cliente.id,
            models.Agendamento.appointment_datetime > now,
            models.Agendamento.status.in_(["agendado", "confirmed", "pending"])
        ).count()
        print(f"[DASHBOARD-DATA] Próximos agendamentos: {upcoming_appointments_count}")

        stats_data = {
            "total_appointments": total_appointments,
            "loyalty_points": loyalty_points,
            "upcoming_appointments": upcoming_appointments_count
        }

        # 3. PRÓXIMOS AGENDAMENTOS (com detalhes completos)
        upcoming_appointments = db.query(models.Agendamento).filter(
            models.Agendamento.client_id == cliente.id,
            models.Agendamento.appointment_datetime > now,
            models.Agendamento.status.in_(["agendado", "confirmed", "pending"])
        ).order_by(models.Agendamento.appointment_datetime).all()

        print(f"[DASHBOARD-DATA] Encontrados {len(upcoming_appointments)} próximos agendamentos")

        # Carregar dados relacionados
        upcoming_list = []
        for apt in upcoming_appointments:
            # Carregar serviço
            servico = None
            if apt.servico_id:
                servico = db.query(models.Servico).filter(models.Servico.id == apt.servico_id).first()

            # Carregar profissional
            profissional = None
            if apt.profissional_id:
                profissional = db.query(models.Profissional).filter(models.Profissional.id == apt.profissional_id).first()

            upcoming_list.append({
                "id": apt.id,
                "data_hora": apt.data_hora.isoformat(),
                "status": apt.status,
                "valor": float(apt.valor) if apt.valor else None, #type: ignore
                "servico": {
                    "id": servico.id if servico else None,
                    "nome": servico.nome if servico else "N/A"
                } if servico else None,
                "profissional": {
                    "id": profissional.id if profissional else None,
                    "nome": profissional.nome if profissional else "N/A"
                } if profissional else None
            })

        # 4. AGENDAMENTOS PENDENTES
        pending_appointments = db.query(models.Agendamento).filter(
            models.Agendamento.client_id == cliente.id,
            models.Agendamento.status == "pending"
        ).order_by(models.Agendamento.appointment_datetime).all()

        print(f"[DASHBOARD-DATA] Encontrados {len(pending_appointments)} agendamentos pendentes")

        pending_list = []
        for apt in pending_appointments:
            servico = None
            if apt.servico_id:
                servico = db.query(models.Servico).filter(models.Servico.id == apt.servico_id).first()

            profissional = None
            if apt.profissional_id:
                profissional = db.query(models.Profissional).filter(models.Profissional.id == apt.profissional_id).first()

            pending_list.append({
                "id": apt.id,
                "data_hora": apt.data_hora.isoformat(),
                "valor": float(apt.valor) if apt.valor else None, #type: ignore
                "servico": {
                    "id": servico.id if servico else None,
                    "nome": servico.nome if servico else "N/A"
                } if servico else None,
                "profissional": {
                    "id": profissional.id if profissional else None,
                    "nome": profissional.nome if profissional else "N/A"
                } if profissional else None
            })

        # 5. HISTÓRICO DE SERVIÇOS (últimos 10)
        completed_appointments = db.query(models.Agendamento).filter(
            models.Agendamento.client_id == cliente.id,
            models.Agendamento.status == "concluido"
        ).order_by(models.Agendamento.appointment_datetime.desc()).limit(10).all()

        print(f"[DASHBOARD-DATA] Encontrados {len(completed_appointments)} agendamentos concluídos no histórico")

        history_list = []
        for apt in completed_appointments:
            servico = None
            if apt.servico_id:
                servico = db.query(models.Servico).filter(models.Servico.id == apt.servico_id).first()

            profissional = None
            if apt.profissional_id:
                profissional = db.query(models.Profissional).filter(models.Profissional.id == apt.profissional_id).first()

            history_list.append({
                "id": apt.id,
                "data_hora": apt.data_hora.isoformat(),
                "valor": float(apt.valor) if apt.valor else None, #type: ignore
                "servico": {
                    "id": servico.id if servico else None,
                    "nome": servico.nome if servico else "N/A"
                } if servico else None,
                "profissional": {
                    "id": profissional.id if profissional else None,
                    "nome": profissional.nome if profissional else "N/A"
                } if profissional else None
            })

        # 6. RETORNAR TUDO JUNTO
        return {
            "profile": profile_data,
            "stats": stats_data,
            "upcoming_appointments": upcoming_list,
            "pending_appointments": pending_list,
            "service_history": history_list,
            "last_updated": datetime.now().isoformat(),
            "cache_version": hash(str(datetime.now().timestamp()))  # Para controle de cache
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CLIENT DASHBOARD DATA] Erro ao buscar dados do dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar dados do dashboard")

# AUTENTICAÇÃO DE CLIENTES
def autenticar_cliente(email: str, senha: str, session: Session):
    """Autentica cliente por email e senha"""
    cliente = session.query(models.Cliente).filter(models.Cliente.email == email).first()
    if not cliente:
        return False
    elif not cliente.senha:  # type: ignore
        return False
    elif not bcrypt_context.verify(senha, cliente.senha):  # type: ignore
        return False
    return cliente

def verificar_cliente_token(token_data = Depends(verificar_token)):
    """Verifica se o token é de um cliente"""
    # Verificar se é um cliente baseado no ID (clientes têm IDs diferentes dos donos)
    cliente = token_data
    if hasattr(cliente, 'senha') and cliente.senha:  # Se tem senha, é cliente
        return cliente
    raise HTTPException(status_code=403, detail="Acesso negado - apenas clientes")

@router.get("/", response_model=list[schemas.ClienteSchema])
def get_clients(db: Session = Depends(get_db), usuario = Depends(verificar_token)):
    """
    Retorna apenas clientes que já realizaram agendamentos confirmados na empresa.
    Filtra pelo salon_id do usuário autenticado e requer pelo menos 1 agendamento confirmado.
    """
    try:
        # Query que retorna apenas clientes com agendamentos confirmados
        # Usa subquery para filtrar apenas clientes ativos
        clients = db.query(models.Cliente).filter(
            models.Cliente.salon_id == usuario.id,  # Filtrar pelo salão do usuário
            models.Cliente.id.in_(
                db.query(models.Agendamento.client_id).filter(
                    models.Agendamento.status == "concluido",
                    models.Agendamento.salon_id == usuario.id  # Garantir que agendamentos são do mesmo salão
                )
            )
        ).distinct().all()  # distinct() para evitar duplicatas se cliente tem múltiplos agendamentos

        return clients

    except Exception as e:
        print(f"Erro ao buscar clientes com agendamentos para usuario {usuario.id}: {str(e)}")
        # Em caso de erro, retornar lista vazia em vez de erro 500
        return []

# ========== AGENDAMENTOS DO CLIENTE ==========

@router.get("/my/appointments")
def get_client_appointments(client_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Retorna agendamentos do cliente especificado ou todos os agendamentos se client_id não for fornecido.
    """
    try:
        # Construir query base
        query = db.query(models.Agendamento)

        # Filtrar por client_id se fornecido
        if client_id:
            query = query.filter(models.Agendamento.client_id == client_id)

        # Buscar agendamentos
        appointments = query.all()

        # Carregar dados relacionados para cada agendamento
        for appointment in appointments:
            try:
                # Carregar serviço
                if appointment.servico_id:
                    appointment.servico = db.query(models.Servico).filter(
                        models.Servico.id == appointment.servico_id
                    ).first()

                # Carregar profissional
                if appointment.profissional_id:
                    appointment.profissional = db.query(models.Profissional).filter(
                        models.Profissional.id == appointment.profissional_id
                    ).first()

                # Carregar cliente
                if appointment.client_id:
                    appointment.cliente = db.query(models.Cliente).filter(
                        models.Cliente.id == appointment.client_id
                    ).first()

            except Exception as e:
                print(f"Erro ao carregar dados relacionados para agendamento {appointment.id}: {str(e)}")
                # Define valores padrão
                appointment.servico = None
                appointment.profissional = None
                appointment.cliente = None

        return appointments

    except Exception as e:
        print(f"Erro ao buscar agendamentos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar agendamentos")

@router.post("/", response_model=schemas.ClienteSchema)
def create_client(client: schemas.ClienteCreate, db: Session = Depends(get_db)):
    db_client = models.Cliente(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client
    """
    Retorna agendamentos do cliente especificado ou todos os agendamentos se client_id não for fornecido.
    """
    try:
        # Construir query base
        query = db.query(models.Agendamento)

        # Filtrar por client_id se fornecido
        if client_id:
            query = query.filter(models.Agendamento.cliente_id == client_id)

        # Buscar agendamentos
        appointments = query.all()

        # Carregar dados relacionados para cada agendamento
        for appointment in appointments:
            try:
                # Carregar serviço
                if appointment.servico_id:
                    appointment.servico = db.query(models.Servico).filter(
                        models.Servico.id == appointment.servico_id
                    ).first()

                # Carregar profissional
                if appointment.profissional_id:
                    appointment.profissional = db.query(models.Profissional).filter(
                        models.Profissional.id == appointment.profissional_id
                    ).first()

                # Carregar cliente
                if appointment.cliente_id:
                    appointment.cliente = db.query(models.Cliente).filter(
                        models.Cliente.id == appointment.cliente_id
                    ).first()

            except Exception as e:
                print(f"Erro ao carregar dados relacionados para agendamento {appointment.id}: {str(e)}")
                # Define valores padrão
                appointment.servico = None
                appointment.profissional = None
                appointment.cliente = None

        return appointments

    except Exception as e:
        print(f"Erro ao buscar agendamentos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar agendamentos")


@router.get("/{client_id:path}", response_model=schemas.ClienteSchema)
def get_client(client_id: str, db: Session = Depends(get_db)):
    # Verificar se client_id é um número válido
    try:
        client_id_int = int(client_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    client = db.query(models.Cliente).filter(models.Cliente.id == client_id_int).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client

@router.put("/{client_id}", response_model=schemas.ClienteSchema)
def update_client(client_id: int, client_update: schemas.ClienteUpdate, db: Session = Depends(get_db)):
    client = db.query(models.Cliente).filter(models.Cliente.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    for key, value in client_update.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client

@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(models.Cliente).filter(models.Cliente.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(client)
    db.commit()
    return {"message": "Cliente deletado com sucesso"}


# ========== AUTENTICAÇÃO DE CLIENTES ==========

@router.post("/register")
def register_client(client_data: schemas.ClienteRegister, db: Session = Depends(get_db)):
    """
    Registra um novo cliente com senha hash.
    Retorna resposta padronizada com sucesso ou erro.
    """
    try:
        # Verificar se estabelecimento existe
        salon = db.query(models.Usuario).filter(models.Usuario.id == client_data.salon_id).first()
        if not salon:
            return {
                "success": False,
                "error": "Estabelecimento não encontrado"
            }

        # Verificar se e-mail já existe
        existing_client = db.query(models.Cliente).filter(
            models.Cliente.email == client_data.email,
            models.Cliente.salon_id == client_data.salon_id
        ).first()
        if existing_client:
            return {
                "success": False,
                "error": "E-mail já cadastrado para este estabelecimento"
            }

        # Verificar se telefone já existe
        existing_phone = db.query(models.Cliente).filter(
            models.Cliente.telefone == client_data.telefone
        ).first()
        if existing_phone:
            return {
                "success": False,
                "error": "Telefone já cadastrado no sistema"
            }

        # Hash da senha
        hashed_password = bcrypt_context.hash(client_data.senha)

        # Criar cliente
        new_client = models.Cliente(
            nome=client_data.nome,
            email=client_data.email,
            telefone=client_data.telefone,
            senha=hashed_password,
            pontos_fidelidade=0,  # Inicia com 0 pontos
            salon_id=client_data.salon_id
        )

        db.add(new_client)
        db.commit()
        db.refresh(new_client)

        # Gerar tokens
        access_token = criar_token(new_client.id, role="cliente")
        refresh_token = criar_token(new_client.id, role="cliente", duracao_token=timedelta(days=1))

        return {
            "success": True,
            "client_id": new_client.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": "cliente"
        }

    except Exception as e:
        db.rollback()  # Importante: fazer rollback em caso de erro
        print(f"Erro no registro de cliente: {str(e)}")  # Log para debug

        # Verificar se é erro de constraint UNIQUE
        if "UNIQUE constraint failed" in str(e):
            if "clientes.telefone" in str(e):
                return {
                    "success": False,
                    "error": "Telefone já cadastrado no sistema"
                }
            elif "clientes.email" in str(e):
                return {
                    "success": False,
                    "error": "E-mail já cadastrado para este estabelecimento"
                }

        # Para outros erros, retornar mensagem genérica
        return {
            "success": False,
            "error": "Erro interno do servidor. Tente novamente."
        }

@router.post("/login", response_model=schemas.TokenResponse)
def login_client(login_data: schemas.ClienteLogin, db: Session = Depends(get_db)):
    """
    Login de cliente.
    Retorna JWT com role "cliente".
    """
    try:
        print(f"[LOGIN] Tentativa de login para email: {login_data.email}")  # Log para debug

        # Verificar se email foi fornecido
        if not login_data.email or not login_data.senha:
            print("[LOGIN] Email ou senha não fornecidos")
            raise HTTPException(status_code=400, detail="Email e senha são obrigatórios")

        # Buscar cliente por email
        cliente = db.query(models.Cliente).filter(models.Cliente.email == login_data.email).first()
        if not cliente:
            print(f"[LOGIN] Cliente não encontrado para email: {login_data.email}")
            raise HTTPException(status_code=401, detail="Email ou senha inválidos")

        # Verificar se cliente tem senha
        if not cliente.senha:  # type: ignore
            print(f"[LOGIN] Cliente {login_data.email} não tem senha cadastrada")
            raise HTTPException(status_code=401, detail="Email ou senha inválidos")

        print(f"[LOGIN] Cliente encontrado: ID={cliente.id}, Email={cliente.email}")

        # Verificar senha usando bcrypt
        try:
            senha_valida = bcrypt_context.verify(login_data.senha, cliente.senha)  # type: ignore
            print(f"[LOGIN] Verificação de senha: {'sucesso' if senha_valida else 'falhou'}")
        except Exception as e:
            print(f"[LOGIN] Erro na verificação de senha: {str(e)}")
            raise HTTPException(status_code=500, detail="Erro interno do servidor. Tente novamente.")

        if not senha_valida:
            print(f"[LOGIN] Senha inválida para cliente: {login_data.email}")
            raise HTTPException(status_code=401, detail="Email ou senha inválidos")

        # Gerar tokens
        try:
            access_token = criar_token(cliente.id, role="cliente")
            refresh_token = criar_token(cliente.id, role="cliente", duracao_token=timedelta(days=1))
            print(f"[LOGIN] Tokens gerados com sucesso para cliente ID: {cliente.id}")
        except Exception as e:
            print(f"[LOGIN] Erro ao gerar tokens: {str(e)}")
            raise HTTPException(status_code=500, detail="Erro interno do servidor. Tente novamente.")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": "cliente"
        }

    except HTTPException:
        # Re-lançar exceções HTTP já tratadas
        raise
    except Exception as e:
        print(f"[LOGIN] Erro inesperado: {str(e)}")
        db.rollback()  # Importante: fazer rollback em caso de erro
        raise HTTPException(status_code=500, detail="Erro interno do servidor. Tente novamente.")



@router.post("/{client_id}/add_points")
def add_loyalty_points(client_id: int, points: int, db: Session = Depends(get_db), usuario: models.Usuario = Depends(verificar_token)):
    """
    Adiciona pontos de fidelidade ao cliente.
    Apenas donos podem adicionar pontos.
    """
    if usuario.admin != True and str(usuario.id) != str(client_id):  # Verificação simples
        raise HTTPException(status_code=403, detail="Apenas donos podem gerenciar pontos")

    cliente = db.query(models.Cliente).filter(models.Cliente.id == client_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    pontos_atuais = getattr(cliente, 'pontos_fidelidade', 0)
    setattr(cliente, 'pontos_fidelidade', pontos_atuais + points)
    db.commit()
    db.refresh(cliente)

    return {
        "message": f"{points} pontos adicionados com sucesso",
        "total_pontos": cliente.pontos_fidelidade
    }

@router.post("/{client_id}/redeem_points")
def redeem_loyalty_points(client_id: int, points: int, db: Session = Depends(get_db), cliente: models.Cliente = Depends(verificar_token)):
    """
    Resgata pontos de fidelidade do cliente.
    Cada 100 pontos = R$ 10,00 de desconto.
    Cliente deve ter pontos suficientes.
    """
    try:
        # Verificar se cliente está acessando seus próprios pontos
        if cliente.id != client_id:  # type: ignore
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Validar pontos
        if points <= 0:
            raise HTTPException(status_code=400, detail="Quantidade de pontos deve ser maior que zero")

        if cliente.pontos_fidelidade < points:  # type: ignore
            raise HTTPException(status_code=400, detail="Pontos insuficientes")

        # Calcular desconto (cada 100 pontos = R$ 10,00)
        discount_value = (points // 100) * 10.00

        # Registrar resgate no log de auditoria
        from ..models import AuditLog
        log_entry = AuditLog(
            acao="resgate_pontos",
            usuario_id=cliente.salon_id,  # Salão onde o cliente está
            salon_id=cliente.salon_id,
            detalhes=f"Cliente {cliente.nome} resgatou {points} pontos (R$ {discount_value:.2f} de desconto)"
        )
        db.add(log_entry)

        # Atualizar pontos do cliente
        pontos_antes = cliente.pontos_fidelidade
        cliente.pontos_fidelidade = pontos_antes - points

        db.commit()
        db.refresh(cliente)

        return {
            "success": True,
            "message": f"Pontos resgatados com sucesso! Valor do desconto: R$ {discount_value:.2f}",
            "points_redeemed": points,
            "discount_value": discount_value,
            "remaining_points": cliente.pontos_fidelidade
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Erro ao resgatar pontos do cliente {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao resgatar pontos")
