from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import Optional
from ..database import get_db
from .. import models, schemas
from ..dependencies import verificar_token
from ..models import Usuario
from ..core.logging import get_logger

router = APIRouter()
logger = get_logger("appointments")

def verificar_conflito_horario(db: Session, servico_id: int, data_hora: datetime, profissional_id: Optional[int] = None, appointment_id: Optional[int] = None):
    """
    Verifica se há conflito de horário considerando o profissional.
    Retorna o agendamento conflitante se houver, None caso contrário.
    """
    try:
        # Se não há profissional especificado, não há como verificar conflito
        if not profissional_id:
            logger.info("Nenhum profissional especificado - pulando validação de conflito")
            return None

        logger.info(f"Verificando conflitos para profissional {profissional_id} em {data_hora}")

        # DEBUG: Ver todos os agendamentos do profissional
        print(f"DEBUG: Verificando conflitos para profissional {profissional_id} em {data_hora}")
        all_appointments = db.query(models.Agendamento).filter(
            models.Agendamento.professional_id == profissional_id
        ).all()
        print(f"DEBUG: Total de agendamentos para profissional {profissional_id}: {len(all_appointments)}")
        logger.info(f"Total de agendamentos para profissional {profissional_id}: {len(all_appointments)}")
        for apt in all_appointments:
            logger.info(f"  Agendamento ID={apt.id}, datetime={apt.appointment_datetime}, status={apt.status}, salon_id={apt.salon_id}")

        # Buscar agendamentos existentes para o mesmo profissional na mesma data/hora
        # Considera apenas agendamentos ativos (não cancelados)
        logger.info(f"Buscando conflitos exatos: prof_id={profissional_id}, datetime={data_hora}")
        query = db.query(models.Agendamento).filter(
            models.Agendamento.professional_id == profissional_id,
            models.Agendamento.appointment_datetime == data_hora
        )

        # Log da query SQL para debug
        logger.info(f"Query SQL: {query}")

        conflitos = query.all()
        logger.info(f"Encontrados {len(conflitos)} agendamentos para profissional {profissional_id} em {data_hora}")

        for conflito in conflitos:
            logger.info(f"Agendamento encontrado: ID={conflito.id}, status={conflito.status}, salon_id={conflito.salon_id}")

        # Filtrar apenas agendamentos ativos
        conflito = None
        for apt in conflitos:
            if apt.status in ["agendado", "confirmado", "pending", "SCHEDULED"]:
                conflito = apt
                break

        # Excluir o próprio agendamento se estiver sendo atualizado
        if conflito and appointment_id and conflito.id == appointment_id:
            logger.info(f"Excluindo próprio agendamento {appointment_id} da validação")
            conflito = None

        if conflito:
            logger.warning(f"Conflito de horário detectado: profissional {profissional_id} já tem agendamento {conflito.id} em {data_hora}")
            return conflito
        else:
            logger.info(f"Nenhum conflito encontrado para profissional {profissional_id} em {data_hora}")
            return None

    except Exception as e:
        logger.error(f"Erro ao verificar conflito de horário: {str(e)}")
        import traceback
        traceback.print_exc()
        # Em caso de erro, permitir o agendamento para não bloquear usuários
        return None

@router.get("/", response_model=list[schemas.AgendamentoSchema])
def get_appointments(db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Retorna lista de agendamentos filtrados por usuário logado"""
    try:
        # Verificar se é cliente ou dono/admin
        user_role = getattr(usuario, 'role', None)

        if user_role == "cliente":
            # Para clientes: filtrar apenas seus próprios agendamentos
            print(f"[APPOINTMENTS] Cliente {usuario.id} buscando seus agendamentos")
            appointments = db.query(models.Agendamento).filter(models.Agendamento.client_id == usuario.id).all()
        else:
            # Para donos/admins: filtrar por salão
            user_salon_id = usuario.id if hasattr(usuario, 'is_admin') else getattr(usuario, 'salon_id', usuario.id)
            print(f"[APPOINTMENTS] Dono/Admin buscando agendamentos do salão {user_salon_id}")
            appointments = db.query(models.Agendamento).filter(models.Agendamento.salon_id == user_salon_id).all()

        print(f"[APPOINTMENTS] Encontrados {len(appointments)} agendamentos válidos")

        # Se não há agendamentos, retornar lista vazia
        if not appointments:
            print("[APPOINTMENTS] Nenhum agendamento encontrado")
            return []

        # Carregar dados relacionados restantes (serviço e profissional)
        for appointment in appointments:
            try:
                print(f"[APPOINTMENTS] Carregando dados para agendamento {appointment.id}")

                # Cliente já foi carregado pelo JOIN
                print(f"[APPOINTMENTS] Cliente já carregado: {appointment.client is not None}")

                # Carregar serviço se existir
                if appointment.service_id:
                    appointment.service = db.query(models.Servico).filter(models.Servico.id == appointment.service_id).first()
                    print(f"[APPOINTMENTS] Serviço carregado: {appointment.service is not None}")

                # Carregar profissional se existir
                if appointment.professional_id:
                    appointment.professional = db.query(models.Profissional).filter(models.Profissional.id == appointment.professional_id).first()
                    print(f"[APPOINTMENTS] Profissional carregado: {appointment.professional is not None}")

            except Exception as e:
                # Log detalhado do erro
                logger.error(f"[APPOINTMENTS] Erro ao carregar dados relacionados para agendamento {appointment.id}: {str(e)}")
                import traceback
                traceback.print_exc()

                # Define valores padrão para evitar erros
                if not hasattr(appointment, 'client') or appointment.client is None:
                    appointment.client = None
                if not hasattr(appointment, 'service') or appointment.service is None:
                    appointment.service = None
                if not hasattr(appointment, 'professional') or appointment.professional is None:
                    appointment.professional = None

        print(f"[APPOINTMENTS] Retornando {len(appointments)} agendamentos processados")

        # Converter para dicionários para evitar problemas de serialização
        result = []
        for appointment in appointments:
            try:
                # Converter cliente para dict (sempre existe devido ao JOIN)
                cliente_dict = None
                if appointment.client:
                    cliente_dict = {
                        "id": appointment.client.id,
                        "nome": appointment.client.nome,
                        "email": appointment.client.email,
                        "telefone": appointment.client.telefone,
                        "pontos_fidelidade": appointment.client.pontos_fidelidade or 0,
                        "salon_id": appointment.client.salon_id
                    }

                # Converter serviço para dict se existir
                servico_dict = None
                if appointment.service:
                    servico_dict = {
                        "id": appointment.service.id,
                        "nome": appointment.service.nome,
                        "descricao": appointment.service.descricao,
                        "duracao_minutos": appointment.service.duracao_minutos,
                        "preco": appointment.service.preco,
                        "pontos_fidelidade": appointment.service.pontos_fidelidade,
                        "salon_id": appointment.service.salon_id
                    }

                # Converter profissional para dict se existir
                profissional_dict = None
                if appointment.professional:
                    profissional_dict = {
                        "id": appointment.professional.id,
                        "nome": appointment.professional.nome,
                        "email": appointment.professional.email,
                        "telefone": appointment.professional.telefone,
                        "especialidade": appointment.professional.especialidade,
                        "salon_id": appointment.professional.salon_id,
                        "ativo": appointment.professional.ativo
                    }

                appointment_dict = {
                    "id": appointment.id,
                    "client_id": appointment.client_id,
                    "service_id": appointment.service_id,
                    "professional_id": appointment.professional_id,
                    "salon_id": appointment.salon_id,
                    "data_hora": appointment.data_hora,
                    "status": appointment.status.value,
                    "valor": float(appointment.valor), #type: ignore
                    "cliente": cliente_dict,
                    "servico": servico_dict,
                    "profissional": profissional_dict
                }
                result.append(appointment_dict)

            except Exception as e:
                logger.error(f"[APPOINTMENTS] Erro ao converter agendamento {appointment.id} para dict: {str(e)}")
                continue  # Pula este agendamento problemático

        print(f"[APPOINTMENTS] Retornando {len(result)} agendamentos convertidos com sucesso")
        return result

    except Exception as e:
        # Log detalhado do erro geral
        logger.error(f"[APPOINTMENTS] Erro crítico ao buscar agendamentos para usuário {usuario.id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Retorna lista vazia em caso de erro para evitar 500 no frontend
        return []

@router.post("/", response_model=schemas.AgendamentoSchema)
def create_appointment(appointment: schemas.AgendamentoCreate, db: Session = Depends(get_db), usuario = Depends(verificar_token)):
    """Cria novo agendamento com validações seguras"""
    try:
        # Verificar se o agendamento pertence ao salão do usuário
        # Para donos: usuario.id é o ID do salão
        # Para clientes: usuario.salon_id é o ID do salão
        user_salon_id = usuario.id if hasattr(usuario, 'is_admin') else getattr(usuario, 'salon_id', usuario.id)

        logger.info(f"[CREATE_APPOINTMENT] Usuário: ID={usuario.id}, type={type(usuario)}, has_is_admin={hasattr(usuario, 'is_admin')}, salon_id={getattr(usuario, 'salon_id', 'N/A')}")
        logger.info(f"[CREATE_APPOINTMENT] user_salon_id={user_salon_id}, appointment.salon_id={appointment.salon_id}")

        # Clientes podem agendar em qualquer salão, donos/admins apenas no seu
        if hasattr(usuario, 'is_admin') and appointment.salon_id != user_salon_id:
            logger.warning(f"[CREATE_APPOINTMENT] Authorization failed: user_salon_id={user_salon_id} != appointment.salon_id={appointment.salon_id}")
            raise HTTPException(status_code=403, detail="Não autorizado a criar agendamento para outro salão")

        # Verificar se cliente existe (com tratamento seguro)
        try:
            cliente = db.query(models.Cliente).filter(models.Cliente.id == appointment.client_id).first()
            if not cliente:
                raise HTTPException(status_code=404, detail="Cliente não encontrado")
        except Exception as e:
            logger.error(f"Erro ao buscar cliente {appointment.client_id}: {str(e)}")
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        # Verificar se serviço existe (com tratamento seguro)
        try:
            servico = db.query(models.Servico).filter(models.Servico.id == appointment.service_id).first()
            if not servico:
                raise HTTPException(status_code=404, detail="Serviço não encontrado")
        except Exception as e:
            logger.error(f"Erro ao buscar serviço {appointment.service_id}: {str(e)}")
            raise HTTPException(status_code=404, detail="Serviço não encontrado")

        # Verificar profissional se especificado
        profissional = None
        if appointment.professional_id:
            try:
                profissional = db.query(models.Profissional).filter(models.Profissional.id == appointment.professional_id).first()
                if not profissional:
                    raise HTTPException(status_code=404, detail="Profissional não encontrado")
            except Exception as e:
                logger.error(f"Erro ao buscar profissional {appointment.professional_id}: {str(e)}")
                raise HTTPException(status_code=404, detail="Profissional não encontrado")

        # Verificar se cliente já tem agendamentos ativos na mesma empresa
        # Cliente só pode ter um agendamento ativo por empresa
        try:
            from datetime import datetime
            now = datetime.now()

            # Buscar agendamentos ativos do cliente no mesmo salão
            active_appointments = db.query(models.Agendamento).filter(
                models.Agendamento.client_id == appointment.client_id,
                models.Agendamento.salon_id == appointment.salon_id,
                models.Agendamento.appointment_datetime > now,  # Futuros
                models.Agendamento.status.in_(["agendado", "confirmado", "pending"])
            ).count()

            logger.info(f"Cliente {appointment.client_id} tem {active_appointments} agendamentos ativos no salão {appointment.salon_id}")

            if active_appointments > 0:
                raise HTTPException(
                    status_code=409,
                    detail="Você já possui um agendamento ativo nesta empresa. Aguarde a conclusão ou cancele o agendamento anterior para fazer um novo."
                )

        except HTTPException:
            raise  # Re-lança HTTPExceptions
        except Exception as e:
            logger.error(f"Erro ao verificar agendamentos ativos do cliente {appointment.client_id}: {str(e)}")
            # Continua sem verificar se houver erro na validação

        # Verificar conflito de horário (com tratamento seguro)
        try:
            conflito = verificar_conflito_horario(db, appointment.service_id, appointment.data_hora, appointment.professional_id)
            if conflito:
                raise HTTPException(status_code=409, detail="Conflito de horário detectado")
        except HTTPException:
            raise  # Re-lança HTTPExceptions
        except Exception as e:
            logger.error(f"Erro ao verificar conflito de horário: {str(e)}")
            # Continua sem verificar conflito se houver erro na validação

        # Criar agendamento
        db_appointment = models.Agendamento(**appointment.model_dump())
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)

        # Carregar dados relacionados para resposta
        db_appointment.cliente = cliente
        db_appointment.servico = servico
        if appointment.professional_id:
            db_appointment.profissional = profissional

        return db_appointment

    except HTTPException:
        # Re-lança HTTPExceptions (validações de negócio)
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao criar agendamento: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/{appointment_id}", response_model=schemas.AgendamentoSchema)
def get_appointment(appointment_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Busca agendamento específico com tratamento seguro de relacionamentos"""
    try:
        appointment = db.query(models.Agendamento).filter(
            models.Agendamento.id == appointment_id,
            models.Agendamento.salon_id == usuario.id
        ).first()

        if not appointment:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado")

        # Carregar dados relacionados de forma segura
        try:
            if appointment.cliente_id:
                appointment.cliente = db.query(models.Cliente).filter(models.Cliente.id == appointment.cliente_id).first()

            if appointment.servico_id:
                appointment.servico = db.query(models.Servico).filter(models.Servico.id == appointment.servico_id).first()

            if appointment.profissional_id:
                appointment.profissional = db.query(models.Profissional).filter(models.Profissional.id == appointment.profissional_id).first()

        except Exception as e:
            logger.error(f"Erro ao carregar dados relacionados para agendamento {appointment_id}: {str(e)}")
            # Define valores padrão
            appointment.cliente = None
            appointment.servico = None
            appointment.profissional = None

        return appointment

    except HTTPException:
        # Re-lança HTTPExceptions (como 404)
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar agendamento {appointment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar agendamento")

@router.put("/{appointment_id}", response_model=schemas.AgendamentoSchema)
def update_appointment(appointment_id: int, appointment_update: schemas.AgendamentoUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    appointment = db.query(models.Agendamento).filter(
        models.Agendamento.id == appointment_id,
        models.Agendamento.salon_id == usuario.id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    # TODO: Implementar validação de conflitos de horário
    # Por enquanto, permitir atualização sem validação

    for key, value in appointment_update.model_dump(exclude_unset=True).items():
        setattr(appointment, key, value)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.delete("/{appointment_id}")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    appointment = db.query(models.Agendamento).filter(
        models.Agendamento.id == appointment_id,
        models.Agendamento.salon_id == usuario.id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    db.delete(appointment)
    db.commit()
    return {"message": "Agendamento deletado com sucesso"}

@router.put("/{appointment_id}/status")
def update_appointment_status(appointment_id: int, status_update: schemas.AgendamentoStatusUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Atualiza status do agendamento com tratamento seguro"""
    try:

        # Validar status
        if status_update.status not in ["agendado", "cancelado", "concluido", "nao_compareceu"]:
            raise HTTPException(status_code=400, detail="Status inválido")

        # Buscar agendamento com filtro apropriado por role
        user_role = getattr(usuario, 'role', None)

        try:
            if user_role == "cliente":
                # Cliente só pode alterar seus próprios agendamentos
                appointment = db.query(models.Agendamento).filter(
                    models.Agendamento.id == appointment_id,
                    models.Agendamento.client_id == usuario.id
                ).first()
            else:
                # Donos/admins podem alterar agendamentos do salão
                user_salon_id = usuario.id if hasattr(usuario, 'is_admin') else getattr(usuario, 'salon_id', usuario.id)
                appointment = db.query(models.Agendamento).filter(
                    models.Agendamento.id == appointment_id,
                    models.Agendamento.salon_id == user_salon_id
                ).first()

            if not appointment:
                raise HTTPException(status_code=404, detail="Agendamento não encontrado")
        except Exception as e:
            logger.error(f"Erro ao buscar agendamento {appointment_id}: {str(e)}")
            raise HTTPException(status_code=404, detail="Agendamento não encontrado")

        # Carregar cliente se necessário para pontos de fidelidade
        cliente = None
        if appointment.cliente_id:
            try:
                cliente = db.query(models.Cliente).filter(models.Cliente.id == appointment.cliente_id).first()
            except Exception as e:
                logger.error(f"Erro ao carregar cliente {appointment.cliente_id}: {str(e)}")

        # Atualizar status usando setattr para evitar problemas de tipo
        setattr(appointment, 'status', status_update.status)

        # Se o agendamento foi concluído, adicionar pontos de fidelidade ao cliente
        if status_update.status == "concluido" and cliente:
            try:
                # Buscar pontos do serviço
                servico = db.query(models.Servico).filter(models.Servico.id == appointment.servico_id).first()
                pontos_ganhos = servico.pontos_fidelidade if servico else 0

                if pontos_ganhos > 0:  # type: ignore
                    # Cliente pode acumular pontos (independente de ter senha)
                    pontos_atuais = getattr(cliente, 'pontos_fidelidade', 0) or 0
                    setattr(cliente, 'pontos_fidelidade', pontos_atuais + pontos_ganhos)
                    logger.info(f"[FIDELIDADE] Cliente {cliente.id} ganhou {pontos_ganhos} pontos. Total: {pontos_atuais + pontos_ganhos}")
                else:
                    logger.info(f"[FIDELIDADE] Serviço {appointment.servico_id} não concede pontos ou pontos = 0")
            except Exception as e:
                logger.error(f"Erro ao atualizar pontos de fidelidade: {str(e)}")
                # Continua sem atualizar pontos se houver erro

        # Commit das mudanças
        try:
            db.commit()
            db.refresh(appointment)
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao salvar alterações no banco: {str(e)}")
            raise HTTPException(status_code=500, detail="Erro interno ao atualizar status")

        return {"message": f"Status atualizado para {status_update.status}"}

    except HTTPException:
        # Re-lança HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao atualizar status do agendamento {appointment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
