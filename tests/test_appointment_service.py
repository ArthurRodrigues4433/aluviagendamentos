"""
Testes para AppointmentService.
"""

import pytest
from datetime import datetime, timedelta
from backend import models
from backend.services import AppointmentService
from backend import schemas


class TestAppointmentService:
    """Testes para o serviço de agendamentos."""

    def test_get_appointments_for_user_owner(self, db_session):
        """Testa busca de agendamentos para dono de salão."""
        # Criar dados de teste
        user = models.User(
            nome="Salão Teste",
            email="teste@salao.com",
            senha="hashed_password",
            ativo=True,
            admin=False
        )
        db_session.add(user)
        db_session.commit()

        client = models.Client(
            nome="João Silva",
            email="joao@email.com",
            telefone="11999999999",
            salon_id=user.id
        )
        db_session.add(client)

        service = models.Service(
            nome="Corte de Cabelo",
            duracao_minutos=60,
            preco=50.0,
            pontos_fidelidade=10,
            salon_id=user.id
        )
        db_session.add(service)

        appointment = models.Agendamento(
            client_id=client.id,
            service_id=service.id,
            salon_id=user.id,
            appointment_datetime=datetime.now() + timedelta(days=1),
            price=50.0,
            status="SCHEDULED"
        )
        db_session.add(appointment)
        db_session.commit()

        # Testar o serviço
        service_instance = AppointmentService(db_session)
        result = service_instance.get_appointments_for_user(user)

        assert len(result) == 1
        assert result[0].id == appointment.id
        assert result[0].cliente.id == client.id
        assert result[0].servico.id == service.id

    def test_get_appointments_for_user_client(self, db_session):
        """Testa busca de agendamentos para cliente."""
        # Criar dados de teste
        user = models.User(
            nome="Salão Teste",
            email="teste@salao.com",
            senha="hashed_password",
            ativo=True,
            admin=False
        )
        db_session.add(user)

        client = models.Client(
            nome="João Silva",
            email="joao@email.com",
            telefone="11999999999",
            salon_id=user.id
        )
        db_session.add(client)

        service = models.Service(
            nome="Corte de Cabelo",
            duracao_minutos=60,
            preco=50.0,
            pontos_fidelidade=10,
            salon_id=user.id
        )
        db_session.add(service)

        appointment = models.Agendamento(
            client_id=client.id,
            service_id=service.id,
            salon_id=user.id,
            appointment_datetime=datetime.now() + timedelta(days=1),
            price=50.0,
            status="SCHEDULED"
        )
        db_session.add(appointment)
        db_session.commit()

        # Configurar cliente como usuário autenticado
        client._auth_role = "cliente"

        # Testar o serviço
        service_instance = AppointmentService(db_session)
        result = service_instance.get_appointments_for_user(client)

        assert len(result) == 1
        assert result[0].id == appointment.id

    def test_create_appointment_success(self, db_session):
        """Testa criação de agendamento com sucesso."""
        # Criar dados de teste
        user = models.User(
            nome="Salão Teste",
            email="teste@salao.com",
            senha="hashed_password",
            ativo=True,
            admin=False
        )
        db_session.add(user)

        client = models.Client(
            nome="João Silva",
            email="joao@email.com",
            telefone="11999999999",
            salon_id=user.id
        )
        db_session.add(client)

        service = models.Service(
            nome="Corte de Cabelo",
            duracao_minutos=60,
            preco=50.0,
            pontos_fidelidade=10,
            salon_id=user.id
        )
        db_session.add(service)
        db_session.commit()

        # Dados do agendamento
        appointment_data = schemas.AgendamentoCreate(
            client_id=client.id,
            service_id=service.id,
            salon_id=user.id,
            data_hora=datetime.now() + timedelta(days=1),
            valor=50.0
        )

        # Testar criação
        service_instance = AppointmentService(db_session)
        result = service_instance.create_appointment(appointment_data, user)

        assert result is not None
        assert result.client_id == client.id
        assert result.service_id == service.id
        assert result.salon_id == user.id

    def test_create_appointment_client_not_found(self, db_session):
        """Testa erro quando cliente não existe."""
        user = models.User(
            nome="Salão Teste",
            email="teste@salao.com",
            senha="hashed_password",
            ativo=True,
            admin=False
        )
        db_session.add(user)
        db_session.commit()

        appointment_data = schemas.AgendamentoCreate(
            client_id=999,  # ID inexistente
            service_id=1,
            salon_id=user.id,
            data_hora=datetime.now() + timedelta(days=1),
            valor=50.0
        )

        service_instance = AppointmentService(db_session)

        with pytest.raises(ValueError, match="Cliente não encontrado"):
            service_instance.create_appointment(appointment_data, user)

    def test_create_appointment_service_not_found(self, db_session):
        """Testa erro quando serviço não existe."""
        user = models.User(
            nome="Salão Teste",
            email="teste@salao.com",
            senha="hashed_password",
            ativo=True,
            admin=False
        )
        db_session.add(user)

        client = models.Client(
            nome="João Silva",
            email="joao@email.com",
            telefone="11999999999",
            salon_id=user.id
        )
        db_session.add(client)
        db_session.commit()

        appointment_data = schemas.AgendamentoCreate(
            client_id=client.id,
            service_id=999,  # ID inexistente
            salon_id=user.id,
            data_hora=datetime.now() + timedelta(days=1),
            valor=50.0
        )

        service_instance = AppointmentService(db_session)

        with pytest.raises(ValueError, match="Serviço não encontrado"):
            service_instance.create_appointment(appointment_data, user)

    def test_check_schedule_conflict(self, db_session):
        """Testa detecção de conflito de horário."""
        # Criar dados de teste
        user = models.User(
            nome="Salão Teste",
            email="teste@salao.com",
            senha="hashed_password",
            ativo=True,
            admin=False
        )
        db_session.add(user)

        professional = models.Professional(
            nome="Maria Silva",
            email="maria@salao.com",
            salon_id=user.id,
            ativo=True
        )
        db_session.add(professional)
        db_session.commit()

        # Criar agendamento existente
        future_time = datetime.now() + timedelta(days=1)
        existing_appointment = models.Agendamento(
            client_id=1,
            service_id=1,
            professional_id=professional.id,
            salon_id=user.id,
            appointment_datetime=future_time,
            price=50.0,
            status="SCHEDULED"
        )
        db_session.add(existing_appointment)
        db_session.commit()

        # Testar conflito
        service_instance = AppointmentService(db_session)
        conflict_exists = service_instance._check_schedule_conflict(
            schemas.AgendamentoCreate(
                client_id=1,
                service_id=1,
                professional_id=professional.id,
                salon_id=user.id,
                data_hora=future_time,  # Mesmo horário
                valor=50.0
            )
        )

        assert conflict_exists is True

    def test_update_appointment_status(self, db_session):
        """Testa atualização de status do agendamento."""
        # Criar dados de teste
        user = models.User(
            nome="Salão Teste",
            email="teste@salao.com",
            senha="hashed_password",
            ativo=True,
            admin=False
        )
        db_session.add(user)

        client = models.Client(
            nome="João Silva",
            email="joao@email.com",
            telefone="11999999999",
            salon_id=user.id,
            pontos_fidelidade=0
        )
        db_session.add(client)

        service = models.Service(
            nome="Corte de Cabelo",
            duracao_minutos=60,
            preco=50.0,
            pontos_fidelidade=10,
            salon_id=user.id
        )
        db_session.add(service)

        appointment = models.Agendamento(
            client_id=client.id,
            service_id=service.id,
            salon_id=user.id,
            appointment_datetime=datetime.now() + timedelta(days=1),
            price=50.0,
            status="SCHEDULED"
        )
        db_session.add(appointment)
        db_session.commit()

        # Testar atualização de status
        service_instance = AppointmentService(db_session)
        success = service_instance.update_appointment_status(
            appointment.id, "concluido", user
        )

        assert success is True

        # Verificar se pontos foram adicionados
        updated_client = db_session.query(models.Client).get(client.id)
        assert updated_client.pontos_fidelidade == 10