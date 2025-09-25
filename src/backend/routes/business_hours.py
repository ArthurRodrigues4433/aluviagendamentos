from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..dependencies import verificar_token
from ..models import Usuario

router = APIRouter()

@router.get("/empresa/{empresa_id}/horarios")
def get_business_hours(empresa_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Retorna os horários de funcionamento da empresa"""
    try:
        # Verificar se o usuário tem permissão (dono da empresa ou admin)
        if usuario.id != empresa_id and not usuario.admin:  # type: ignore
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Buscar horários da empresa
        horarios = db.query(models.HorarioFuncionamento).filter(
            models.HorarioFuncionamento.salon_id == empresa_id
        ).first()

        if not horarios:
            # Retornar horários padrão se não existir
            return {
                "empresa_id": empresa_id,
                "segunda": {"abertura": "08:00", "fechamento": "18:00"},
                "terca": {"abertura": "08:00", "fechamento": "18:00"},
                "quarta": {"abertura": "08:00", "fechamento": "18:00"},
                "quinta": {"abertura": "08:00", "fechamento": "18:00"},
                "sexta": {"abertura": "08:00", "fechamento": "18:00"},
                "sabado": {"abertura": "08:00", "fechamento": "18:00"},
                "domingo": {"abertura": None, "fechamento": None}
            }

        # Retornar horários formatados
        return {
            "empresa_id": empresa_id,
            "segunda": {
                "abertura": horarios.monday_open,
                "fechamento": horarios.monday_close
            },
            "terca": {
                "abertura": horarios.tuesday_open,
                "fechamento": horarios.tuesday_close
            },
            "quarta": {
                "abertura": horarios.wednesday_open,
                "fechamento": horarios.wednesday_close
            },
            "quinta": {
                "abertura": horarios.thursday_open,
                "fechamento": horarios.thursday_close
            },
            "sexta": {
                "abertura": horarios.friday_open,
                "fechamento": horarios.friday_close
            },
            "sabado": {
                "abertura": horarios.saturday_open,
                "fechamento": horarios.saturday_close
            },
            "domingo": {
                "abertura": horarios.sunday_open,
                "fechamento": horarios.sunday_close
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao buscar horários da empresa {empresa_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar horários")

@router.put("/empresa/{empresa_id}/horarios")
async def update_business_hours(empresa_id: int, request: Request, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Atualiza os horários de funcionamento da empresa (somente dono)"""
    try:
        # Verificar se a empresa existe
        empresa = db.query(models.Usuario).filter(models.Usuario.id == empresa_id).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

        # Verificar se o usuário é o dono da empresa
        if usuario.id != empresa_id:  # type: ignore
            raise HTTPException(status_code=403, detail="Apenas o dono da empresa pode alterar os horários")

        # Obter dados do corpo da requisição
        horarios_data = await request.json()

        # Validar formato do payload (lista de objetos)
        if not isinstance(horarios_data, list):
            raise HTTPException(status_code=400, detail="Payload deve ser uma lista de horários")

        # Converter lista para dict
        horarios_dict = {}
        for item in horarios_data:
            if not isinstance(item, dict) or 'dia' not in item:
                raise HTTPException(status_code=400, detail="Cada item deve ser um objeto com 'dia', 'abertura' e 'fechamento'")
            dia = item['dia']
            abertura = item.get('abertura')
            fechamento = item.get('fechamento')
            horarios_dict[dia] = {'abertura': abertura, 'fechamento': fechamento}

        # Buscar ou criar registro de horários
        horarios = db.query(models.HorarioFuncionamento).filter(
            models.HorarioFuncionamento.salon_id == empresa_id
        ).first()

        if not horarios:
            # Criar novo registro com todos os campos
            print(f"Criando novo registro de horarios para empresa {empresa_id}")
            horarios = models.HorarioFuncionamento(salon_id=empresa_id)
            db.add(horarios)
            try:
                db.flush()  # Força a criação do registro no banco
                print(f"Registro criado com sucesso para empresa {empresa_id}")
            except Exception as create_error:
                print(f"Erro ao criar registro: {str(create_error)}")
                raise HTTPException(status_code=500, detail="Erro ao criar registro de horarios")

        # Validar formato dos horários (HH:MM)
        dias_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']

        for dia in dias_semana:
            if dia in horarios_dict:
                abertura = horarios_dict[dia].get('abertura')
                fechamento = horarios_dict[dia].get('fechamento')

                # Validar formato se horário foi fornecido
                if abertura and not validar_formato_horario(abertura):
                    raise HTTPException(status_code=400, detail=f"Formato inválido para horário de abertura de {dia}. Use HH:MM")
                if fechamento and not validar_formato_horario(fechamento):
                    raise HTTPException(status_code=400, detail=f"Formato inválido para horário de fechamento de {dia}. Use HH:MM")

                # Validar lógica (abertura antes do fechamento)
                if abertura and fechamento:
                    if abertura >= fechamento:
                        raise HTTPException(status_code=400, detail=f"Horário de abertura deve ser anterior ao fechamento em {dia}")

                # Mapear nomes em português para nomes em inglês
                dia_mapping = {
                    'segunda': 'monday',
                    'terca': 'tuesday',
                    'quarta': 'wednesday',
                    'quinta': 'thursday',
                    'sexta': 'friday',
                    'sabado': 'saturday',
                    'domingo': 'sunday'
                }

                dia_english = dia_mapping.get(dia, dia)

                # Atualizar campos
                try:
                    setattr(horarios, f"{dia_english}_open", abertura)
                    setattr(horarios, f"{dia_english}_close", fechamento)
                    print(f"Atualizado {dia}: abertura={abertura}, fechamento={fechamento}")
                except Exception as field_error:
                    print(f"Erro ao atualizar campo {dia}: {str(field_error)}")
                    raise HTTPException(status_code=500, detail=f"Erro ao atualizar campo {dia}")

        # Domingo - tratamento especial (pode ser null)
        if 'domingo' in horarios_dict:
            domingo_data = horarios_dict['domingo']
            if domingo_data is None:
                # Domingo fechado
                try:
                    setattr(horarios, "sunday_open", None)
                    setattr(horarios, "sunday_close", None)
                    print("Atualizado domingo: fechado")
                except Exception as field_error:
                    print(f"Erro ao atualizar campo domingo: {str(field_error)}")
                    raise HTTPException(status_code=500, detail="Erro ao atualizar campo domingo")
            else:
                # Domingo com horários
                abertura = domingo_data.get('abertura')
                fechamento = domingo_data.get('fechamento')

                # Validar formato se horário foi fornecido
                if abertura and not validar_formato_horario(abertura):
                    raise HTTPException(status_code=400, detail="Formato inválido para horário de abertura do domingo. Use HH:MM")
                if fechamento and not validar_formato_horario(fechamento):
                    raise HTTPException(status_code=400, detail="Formato inválido para horário de fechamento do domingo. Use HH:MM")

                # Validar lógica (abertura antes do fechamento)
                if abertura and fechamento:
                    if abertura >= fechamento:
                        raise HTTPException(status_code=400, detail="Horário de abertura deve ser anterior ao fechamento no domingo")

                try:
                    setattr(horarios, "sunday_open", abertura)
                    setattr(horarios, "sunday_close", fechamento)
                    print(f"Atualizado domingo: abertura={abertura}, fechamento={fechamento}")
                except Exception as field_error:
                    print(f"Erro ao atualizar campo domingo: {str(field_error)}")
                    raise HTTPException(status_code=500, detail="Erro ao atualizar campo domingo")

        try:
            db.commit()
            db.refresh(horarios)
            print("Commit realizado com sucesso")

            return {
                "success": True,
                "message": "Horários de funcionamento atualizados com sucesso"
            }
        except Exception as commit_error:
            print(f"Erro no commit: {str(commit_error)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Erro ao salvar alterações no banco de dados")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Erro ao atualizar horários da empresa {empresa_id}: {str(e)}")
        print(f"Tipo do erro: {type(e)}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar horários")

def validar_formato_horario(horario: str) -> bool:
    """Valida se o horário está no formato HH:MM"""
    try:
        if not horario or len(horario) != 5:
            return False

        hora, minuto = horario.split(':')
        hora = int(hora)
        minuto = int(minuto)

        return 0 <= hora <= 23 and 0 <= minuto <= 59
    except (ValueError, AttributeError):
        return False

@router.get("/empresa/{empresa_id}/horarios/disponiveis")
def get_available_hours_for_date(empresa_id: int, date: str, db: Session = Depends(get_db)):
    """Retorna horários disponíveis para uma data específica considerando horário de funcionamento"""
    try:
        from datetime import datetime

        # Validar data
        try:
            appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {
                "success": False,
                "message": "Formato de data inválido. Use YYYY-MM-DD"
            }

        # Verificar se data é futura ou hoje
        today = datetime.now().date()
        if appointment_date < today:
            return {
                "success": False,
                "message": "Não é possível verificar horários para datas passadas"
            }

        # Buscar horários da empresa
        horarios = db.query(models.HorarioFuncionamento).filter(
            models.HorarioFuncionamento.salon_id == empresa_id
        ).first()

        if not horarios:
            return {
                "success": False,
                "message": "Horários de funcionamento não configurados para esta empresa"
            }

        # Determinar dia da semana
        dias_semana = {
            0: 'monday', 1: 'tuesday', 2: 'wednesday', 3: 'thursday',
            4: 'friday', 5: 'saturday', 6: 'sunday'
        }
        dia_semana = dias_semana[appointment_date.weekday()]

        # Buscar horário de funcionamento do dia
        abertura_attr = f"{dia_semana}_open"
        fechamento_attr = f"{dia_semana}_close"

        abertura = getattr(horarios, abertura_attr)
        fechamento = getattr(horarios, fechamento_attr)

        if not abertura or not fechamento:
            return {
                "success": False,
                "message": f"A empresa não funciona às {dia_semana}s"
            }

        # Gerar horários disponíveis dentro do horário de funcionamento
        available_times = []
        abertura_hora, abertura_min = map(int, abertura.split(':'))
        fechamento_hora, fechamento_min = map(int, fechamento.split(':'))

        current_hour = abertura_hora
        current_min = abertura_min

        while current_hour < fechamento_hora or (current_hour == fechamento_hora and current_min < fechamento_min):
            time_str = f"{current_hour:02d}:{current_min:02d}"
            available_times.append(time_str)

            # Adicionar 30 minutos
            current_min += 30
            if current_min >= 60:
                current_hour += 1
                current_min = 0

        return {
            "success": True,
            "data": available_times,
            "dia_semana": dia_semana,
            "horario_funcionamento": {
                "abertura": abertura,
                "fechamento": fechamento
            }
        }

    except Exception as e:
        print(f"Erro ao buscar horários disponíveis para empresa {empresa_id}: {str(e)}")
        return {
            "success": False,
            "message": "Erro interno ao buscar horários disponíveis"
        }