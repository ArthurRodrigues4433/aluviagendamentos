from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from ..database import get_db
from .. import models, schemas
from ..dependencies import verificar_token
from ..models import Usuario

router = APIRouter()

@router.get("/dashboard", response_model=schemas.RelatorioDashboard)
def get_dashboard_report(db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Retorna estatísticas gerais para o dashboard do salão"""
    try:
        # Contagem total de clientes
        total_clientes = db.query(models.Cliente).filter(models.Cliente.salon_id == usuario.id).count()

        # Contagem total de serviços
        total_servicos = db.query(models.Servico).filter(models.Servico.salon_id == usuario.id).count()

        # Contagem total de agendamentos ativos (apenas status 'agendado')
        total_agendamentos = db.query(models.Agendamento).filter(
            models.Agendamento.salon_id == usuario.id,
            models.Agendamento.status == "agendado"
        ).count()

        # Faturamento total - tratamento seguro para valores None
        faturamento_query = db.query(func.sum(models.Agendamento.price)).filter(
            models.Agendamento.salon_id == usuario.id,
            models.Agendamento.status == "concluido"
        ).scalar()

        # Garante que faturamento_total seja sempre um número
        if faturamento_query is None:
            faturamento_total = 0.0
        else:
            try:
                faturamento_total = float(faturamento_query)
            except (ValueError, TypeError):
                faturamento_total = 0.0

        # Agendamentos de hoje (apenas status 'agendado')
        hoje = datetime.now().date()
        agendamentos_hoje = db.query(models.Agendamento).filter(
            models.Agendamento.salon_id == usuario.id,
            func.date(models.Agendamento.appointment_datetime) == hoje,
            models.Agendamento.status == "agendado"
        ).count()

        # Novos clientes no mês atual - tratamento seguro para campo created_at
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        novos_clientes_mes = db.query(models.Cliente).filter(
            models.Cliente.salon_id == usuario.id,
            extract('month', models.Cliente.created_at) == mes_atual,
            extract('year', models.Cliente.created_at) == ano_atual
        ).count()

        return {
            "total_clientes": total_clientes,
            "total_servicos": total_servicos,
            "total_agendamentos": total_agendamentos,
            "faturamento_total": faturamento_total,
            "agendamentos_hoje": agendamentos_hoje,
            "novos_clientes_mes": novos_clientes_mes
        }

    except Exception as e:
        # Log do erro para debug
        print(f"Erro ao gerar relatório do dashboard para usuário {usuario.id}: {str(e)}")

        # Retorna dados padrão em caso de erro
        return {
            "total_clientes": 0,
            "total_servicos": 0,
            "total_agendamentos": 0,
            "faturamento_total": 0.0,
            "agendamentos_hoje": 0,
            "novos_clientes_mes": 0
        }

@router.get("/revenue/daily")
def get_daily_revenue(days: int = 7, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Retorna faturamento diário dos últimos N dias - apenas se houver dados"""
    try:
        data_inicio = datetime.now() - timedelta(days=days)

        # Primeiro, verificar se há agendamentos concluídos no período
        has_data = db.query(models.Agendamento).filter(
            models.Agendamento.salon_id == usuario.id,
            models.Agendamento.status == "concluido",
            models.Agendamento.data_hora >= data_inicio
        ).count() > 0

        if not has_data:
            return {
                "success": False,
                "message": "Não há dados de faturamento para gerar relatório no período selecionado"
            }

        # Query para faturamento diário
        resultados = db.query(
            func.date(models.Agendamento.data_hora).label('data'),
            func.sum(models.Agendamento.valor).label('faturamento')
        ).filter(
            models.Agendamento.salon_id == usuario.id,
            models.Agendamento.status == "concluido",
            models.Agendamento.data_hora >= data_inicio
        ).group_by(func.date(models.Agendamento.data_hora)).all()

        # Trata conversão segura de valores
        data_list = []
        for r in resultados:
            try:
                # Trata conversão segura do faturamento
                faturamento = r[1]
                if faturamento is None:
                    faturamento = 0.0
                else:
                    faturamento = float(faturamento)

                data_list.append({
                    "data": str(r[0]),
                    "faturamento": faturamento
                })
            except (ValueError, TypeError) as e:
                print(f"Erro ao converter faturamento para linha {r}: {e}")
                data_list.append({
                    "data": str(r[0]),
                    "faturamento": 0.0
                })

        return {
            "success": True,
            "data": data_list
        }

    except Exception as e:
        print(f"Erro ao gerar relatório de faturamento diário: {str(e)}")
        return {
            "success": False,
            "message": "Erro interno ao gerar relatório de faturamento"
        }

@router.get("/appointments/status")
def get_appointments_by_status(db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Retorna contagem de agendamentos por status"""
    try:
        resultados = db.query(
            models.Agendamento.status,
            func.count(models.Agendamento.id).label('quantidade')
        ).filter(
            models.Agendamento.salon_id == usuario.id
        ).group_by(models.Agendamento.status).all()

        # Trata lista vazia retornando dicionário com status padrão
        if not resultados:
            return {"mensagem": "Nenhum agendamento encontrado"}

        return {r[0]: int(r[1] or 0) for r in resultados}

    except Exception as e:
        print(f"Erro ao gerar relatório de agendamentos por status: {str(e)}")
        return {"erro": "Erro interno ao gerar relatório"}

@router.get("/services/popular")
def get_popular_services(limit: int = 5, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Retorna os serviços mais populares"""
    try:
        resultados = db.query(
            models.Servico.nome,
            func.count(models.Agendamento.id).label('quantidade')
        ).join(models.Agendamento).filter(
            models.Servico.salon_id == usuario.id,
            models.Agendamento.status == "concluido"
        ).group_by(models.Servico.id, models.Servico.nome).order_by(
            func.count(models.Agendamento.id).desc()
        ).limit(limit).all()

        # Trata lista vazia
        if not resultados:
            return [{"mensagem": "Nenhum serviço encontrado ou nenhum agendamento concluído"}]

        return [{"servico": r[0], "quantidade": int(r[1] or 0)} for r in resultados]

    except Exception as e:
        print(f"Erro ao gerar relatório de serviços populares: {str(e)}")
        return [{"erro": "Erro interno ao gerar relatório", "quantidade": 0}]

@router.get("/revenue/monthly")
def get_monthly_revenue(db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Retorna faturamento mensal dos últimos 12 meses"""
    try:
        # Query para faturamento mensal
        resultados = db.query(
            func.extract('year', models.Agendamento.data_hora).label('ano'),
            func.extract('month', models.Agendamento.data_hora).label('mes'),
            func.sum(models.Agendamento.valor).label('faturamento')
        ).filter(
            models.Agendamento.salon_id == usuario.id,
            models.Agendamento.status == "concluido"
        ).group_by(
            func.extract('year', models.Agendamento.data_hora),
            func.extract('month', models.Agendamento.data_hora)
        ).order_by(
            func.extract('year', models.Agendamento.data_hora).desc(),
            func.extract('month', models.Agendamento.data_hora).desc()
        ).limit(12).all()

        # Trata lista vazia
        if not resultados:
            return [{"mensagem": "Nenhum dado de faturamento mensal encontrado"}]

        # Trata conversão segura de valores
        return [{"ano": int(r[0]), "mes": int(r[1]), "faturamento": float(r[2] or 0)} for r in resultados]

    except Exception as e:
        print(f"Erro ao gerar relatório de faturamento mensal: {str(e)}")
        return [{"erro": "Erro interno ao gerar relatório", "faturamento": 0.0}]

@router.get("/clients/new")
def get_new_clients_report(period: str = "month", db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """
    Retorna relatório de novos clientes por período - apenas se houver dados.
    period: 'day', 'week', 'month'
    """
    try:
        # Definir período
        if period == "day":
            start_date = datetime.now() - timedelta(days=30)
            group_by = func.date(models.Cliente.created_at)
        elif period == "week":
            start_date = datetime.now() - timedelta(weeks=12)
            group_by = func.extract('week', models.Cliente.created_at)
        else:  # month
            start_date = datetime.now() - timedelta(days=365)
            group_by = func.extract('month', models.Cliente.created_at)

        # Primeiro, verificar se há clientes no estabelecimento
        has_clients = db.query(models.Cliente).filter(
            models.Cliente.salon_id == usuario.id
        ).count() > 0

        if not has_clients:
            return {
                "success": False,
                "message": "Não há clientes cadastrados para gerar relatório"
            }

        # Query para novos clientes por período
        resultados = db.query(
            group_by.label('periodo'),
            func.count(models.Cliente.id).label('novos_clientes')
        ).filter(
            models.Cliente.salon_id == usuario.id
        ).group_by(group_by).order_by(group_by.desc()).limit(12).all()

        # Trata lista vazia
        if not resultados:
            return {
                "success": False,
                "message": "Nenhum novo cliente encontrado no período selecionado"
            }

        return {
            "success": True,
            "data": [{"periodo": str(r[0]), "novos_clientes": int(r[1] or 0)} for r in resultados]
        }

    except Exception as e:
        print(f"Erro ao gerar relatório de novos clientes: {str(e)}")
        return {
            "success": False,
            "message": "Erro interno ao gerar relatório de novos clientes"
        }

@router.get("/performance")
def get_performance_report(db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Retorna métricas de performance do estabelecimento - apenas se houver dados"""
    try:
        hoje = datetime.now().date()
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year

        # Primeiro, verificar se há dados básicos (clientes ou agendamentos)
        has_clients = db.query(models.Cliente).filter(models.Cliente.salon_id == usuario.id).count() > 0
        has_appointments = db.query(models.Agendamento).filter(models.Agendamento.salon_id == usuario.id).count() > 0

        if not has_clients and not has_appointments:
            return {
                "success": False,
                "message": "Não há dados suficientes para gerar relatório de performance"
            }

        # Agendamentos hoje (apenas status 'agendado')
        agendamentos_hoje_query = db.query(func.count(models.Agendamento.id)).filter(
            models.Agendamento.salon_id == usuario.id,
            func.date(models.Agendamento.data_hora) == hoje,
            models.Agendamento.status == "agendado"
        ).scalar()
        agendamentos_hoje = int(agendamentos_hoje_query) if agendamentos_hoje_query is not None else 0

        # Faturamento mensal - tratamento seguro
        faturamento_query = db.query(func.sum(models.Agendamento.valor)).filter(
            models.Agendamento.salon_id == usuario.id,
            models.Agendamento.status == "concluido",
            func.extract('month', models.Agendamento.data_hora) == mes_atual,
            func.extract('year', models.Agendamento.data_hora) == ano_atual
        ).scalar()

        if faturamento_query is None:
            faturamento_mensal = 0.0
        else:
            try:
                faturamento_mensal = float(faturamento_query)
            except (ValueError, TypeError):
                faturamento_mensal = 0.0

        # Total de profissionais
        total_profissionais_query = db.query(func.count(models.Profissional.id)).filter(
            models.Profissional.salon_id == usuario.id,
            models.Profissional.ativo == True
        ).scalar()
        total_profissionais = int(total_profissionais_query) if total_profissionais_query is not None else 1

        # Novos clientes este mês
        novos_clientes_query = db.query(func.count(models.Cliente.id)).filter(
            models.Cliente.salon_id == usuario.id,
            func.extract('month', models.Cliente.created_at) == mes_atual,
            func.extract('year', models.Cliente.created_at) == ano_atual
        ).scalar()
        novos_clientes_mes = int(novos_clientes_query) if novos_clientes_query is not None else 0

        # Calcula taxa de ocupação de forma segura
        if total_profissionais > 0:
            taxa_ocupacao = min(100, (agendamentos_hoje / total_profissionais) * 100)
        else:
            taxa_ocupacao = 0

        return {
            "success": True,
            "data": {
                "agendamentos_hoje": agendamentos_hoje,
                "faturamento_mensal": faturamento_mensal,
                "novos_clientes_mes": novos_clientes_mes,
                "total_profissionais": total_profissionais,
                "taxa_ocupacao_estimada": taxa_ocupacao
            }
        }

    except Exception as e:
        print(f"Erro ao gerar relatório de performance: {str(e)}")
        return {
            "success": False,
            "message": "Erro interno ao gerar relatório de performance"
        }