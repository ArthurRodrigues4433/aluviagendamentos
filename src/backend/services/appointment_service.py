"""
Serviço para gerenciamento de agendamentos.
Centraliza toda a lógica de negócio relacionada a agendamentos.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from .. import models, schemas
from ..core.logging import get_logger

logger = get_logger("appointment_service")


class AppointmentService:
    """Serviço para operações com agendamentos."""

    def __init__(self, db: Session):
        self.db = db

    def get_appointments_for_user(self, user) -> List[schemas.AgendamentoSchema]:
        """
        Busca agendamentos para um usuário específico.
        Clientes veem apenas seus agendamentos, donos/admins veem do salão.
        """
        user_role = getattr(user, 'role', None)

        # Query base com eager loading
        base_query = self.db.query(models.Agendamento).options(
            joinedload(models.Agendamento.client),
            joinedload(models.Agendamento.service),
            joinedload(models.Agendamento.professional)
        )

        if user_role == "cliente":
            # Para clientes: filtrar apenas seus próprios agendamentos
            logger.info(f"Cliente {user.id} buscando seus agendamentos")
            appointments = base_query.filter(models.Agendamento.client_id == user.id).all()
        else:
            # Para donos/admins: filtrar por salão
            user_salon_id = user.id if hasattr(user, 'is_admin') else getattr(user, 'salon_id', user.id)
            logger.info(f"Dono/Admin buscando agendamentos do salão {user_salon_id}")
            appointments = base_query.filter(models.Agendamento.salon_id == user_salon_id).all()

        logger.info(f"Encontrados {len(appointments)} agendamentos")

        # Garantir que relacionamentos estejam acessíveis
        for appointment in appointments:
            if not hasattr(appointment, 'client'):
                appointment.client = None
            if not hasattr(appointment, 'service'):
                appointment.service = None
            if not hasattr(appointment, 'professional'):
                appointment.professional = None

        # Converter usando Pydantic
        try:
            return [schemas.AgendamentoSchema.from_orm(apt) for apt in appointments]
        except Exception as e:
            logger.error(f"Erro na conversão dos agendamentos: {str(e)}", exc_info=True)
            return []

    def create_appointment(self, appointment_data: schemas.AgendamentoCreate, user) -> models.Agendamento:
        """
        Cria um novo agendamento com validações completas.
        """
        # Verificar permissões
        user_salon_id = user.id if hasattr(user, 'is_admin') else getattr(user, 'salon_id', user.id)
        if not hasattr(user, 'is_admin') and appointment_data.salon_id != user_salon_id:
            raise ValueError("Não autorizado a criar agendamento para outro salão")

        # Validar entidades relacionadas
        self._validate_related_entities(appointment_data)

        # Verificar conflitos de horário
        if self._check_schedule_conflict(appointment_data):
            raise ValueError("Conflito de horário detectado")

        # Verificar limite de agendamentos ativos do cliente
        if self._check_client_active_limit(appointment_data):
            raise ValueError("Cliente já possui agendamento ativo nesta empresa")

        # Criar agendamento em transação
        return self._create_appointment_transaction(appointment_data)

    def _validate_related_entities(self, data: schemas.AgendamentoCreate):
        """Valida se cliente, serviço e profissional existem."""
        # Cliente
        client = self.db.query(models.Cliente).filter(models.Cliente.id == data.client_id).first()
        if not client:
            raise ValueError("Cliente não encontrado")

        # Serviço
        service = self.db.query(models.Servico).filter(models.Servico.id == data.service_id).first()
        if not service:
            raise ValueError("Serviço não encontrado")

        # Profissional (se especificado)
        if data.professional_id:
            professional = self.db.query(models.Profissional).filter(
                models.Profissional.id == data.professional_id
            ).first()
            if not professional:
                raise ValueError("Profissional não encontrado")

    def _check_schedule_conflict(self, data: schemas.AgendamentoCreate) -> bool:
        """Verifica se há conflito de horário."""
        if not data.professional_id:
            return False  # Sem profissional, sem conflito possível

        conflict = self.db.query(models.Agendamento).filter(
            models.Agendamento.professional_id == data.professional_id,
            models.Agendamento.appointment_datetime == data.data_hora,
            models.Agendamento.status.in_(["agendado", "confirmado", "pending", "SCHEDULED"])
        ).first()

        return conflict is not None

    def _check_client_active_limit(self, data: schemas.AgendamentoCreate) -> bool:
        """Verifica se cliente já tem agendamento ativo no salão."""
        now = datetime.now()
        active_count = self.db.query(models.Agendamento).filter(
            models.Agendamento.client_id == data.client_id,
            models.Agendamento.salon_id == data.salon_id,
            models.Agendamento.appointment_datetime > now,
            models.Agendamento.status.in_(["agendado", "confirmado", "pending", "SCHEDULED"])
        ).count()

        return active_count > 0

    def _create_appointment_transaction(self, data: schemas.AgendamentoCreate) -> models.Agendamento:
        """Cria agendamento dentro de uma transação."""
        try:
            with self.db.begin():
                # Criar agendamento
                db_appointment = models.Agendamento(**data.model_dump())
                self.db.add(db_appointment)
                self.db.flush()  # Para obter o ID

                # Carregar dados relacionados
                db_appointment.client = self.db.query(models.Cliente).get(data.client_id)
                db_appointment.service = self.db.query(models.Servico).get(data.service_id)
                if data.professional_id:
                    db_appointment.professional = self.db.query(models.Profissional).get(data.professional_id)

                self.db.commit()
                return db_appointment

        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar agendamento: {str(e)}", exc_info=True)
            raise

    def update_appointment_status(self, appointment_id: int, new_status: str, user) -> bool:
        """
        Atualiza status do agendamento com regras de negócio.
        """
        # Buscar agendamento
        appointment = self._get_appointment_for_user(appointment_id, user)
        if not appointment:
            raise ValueError("Agendamento não encontrado")

        # Validar status
        valid_statuses = ["agendado", "cancelado", "concluido", "nao_compareceu"]
        if new_status not in valid_statuses:
            raise ValueError("Status inválido")

        # Atualizar status e processar regras de negócio
        try:
            with self.db.begin():
                appointment.status = new_status

                # Se concluído, adicionar pontos de fidelidade
                if new_status == "concluido" and appointment.client:
                    service = self.db.query(models.Servico).get(appointment.service_id)
                    if service and service.pontos_fidelidade > 0:
                        appointment.client.pontos_fidelidade += service.pontos_fidelidade
                        logger.info(f"Cliente {appointment.client.id} ganhou {service.pontos_fidelidade} pontos")

                self.db.commit()
                return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar status: {str(e)}", exc_info=True)
            raise

    def _get_appointment_for_user(self, appointment_id: int, user) -> Optional[models.Agendamento]:
        """Busca agendamento considerando permissões do usuário."""
        user_role = getattr(user, 'role', None)

        if user_role == "cliente":
            return self.db.query(models.Agendamento).filter(
                models.Agendamento.id == appointment_id,
                models.Agendamento.client_id == user.id
            ).first()
        else:
            user_salon_id = user.id if hasattr(user, 'is_admin') else getattr(user, 'salon_id', user.id)
            return self.db.query(models.Agendamento).filter(
                models.Agendamento.id == appointment_id,
                models.Agendamento.salon_id == user_salon_id
            ).first()