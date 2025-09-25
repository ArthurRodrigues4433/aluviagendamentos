from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import secrets
import shutil
from pathlib import Path
from ..database import get_db
from .. import models, schemas
from ..dependencies import verificar_token
from ..models import Usuario
from ..core.config import filesystem

router = APIRouter()

@router.get("/", response_model=list[schemas.ProfissionalSchema])
def get_professionals(db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """
    Lista todos os profissionais do estabelecimento logado.
    Retorna apenas profissionais ativos por padrão.
    """
    try:
        print(f"[PROFESSIONALS] Buscando profissionais para salon_id={usuario.id}")

        professionals = db.query(models.Profissional).filter(
            models.Profissional.salon_id == usuario.id,
            models.Profissional.ativo == True
        ).all()

        print(f"[PROFESSIONALS] Encontrados {len(professionals)} profissionais ativos")

        return professionals

    except Exception as e:
        print(f"[PROFESSIONALS] Erro ao buscar profissionais para usuário {usuario.id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

@router.post("/", response_model=schemas.ProfissionalSchema)
def create_professional(
    nome: str = Form(...),
    email: Optional[str] = Form(None),
    telefone: Optional[str] = Form(None),
    especialidade: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(verificar_token)
):
    """
    Cria um novo profissional para o estabelecimento do usuário logado.
    O salon_id é determinado automaticamente pelo backend baseado no usuário autenticado.
    Aceita upload de foto do profissional.
    """
    try:
        # Verificar se já existe profissional com mesmo email no estabelecimento
        if email:
            existing = db.query(models.Profissional).filter(
                models.Profissional.email == email,
                models.Profissional.salon_id == usuario.id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Já existe profissional com este e-mail neste estabelecimento")

        # Processar upload da foto se fornecida
        foto_path = None
        if foto:
            # Validar tipo do arquivo
            if foto.content_type and not foto.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="A foto deve ser um arquivo de imagem válido")

            # Gerar nome único para o arquivo
            filename = foto.filename or "foto.jpg"
            file_extension = os.path.splitext(filename)[1] or ".jpg"
            unique_filename = f"professional_{usuario.id}_{uuid.uuid4().hex}{file_extension}"
            foto_path = f"uploads/professionals/{unique_filename}"

            # Salvar arquivo
            file_path = os.path.join(os.getcwd(), foto_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as buffer:
                content = foto.file.read()
                buffer.write(content)

        # Criar dados do profissional
        professional_data = {
            'nome': nome,
            'email': email,
            'telefone': telefone,
            'especialidade': especialidade,
            'foto': foto_path,
            'salon_id': usuario.id,  # Define automaticamente o estabelecimento
            'ativo': True  # Novos profissionais começam ativos
        }

        # Criar e salvar o profissional
        db_professional = models.Profissional(**professional_data)
        db.add(db_professional)
        db.commit()
        db.refresh(db_professional)

        return db_professional

    except HTTPException:
        # Re-lança exceções HTTP (como validação de e-mail duplicado)
        raise
    except Exception as e:
        db.rollback()
        print(f"Erro ao criar profissional: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar profissional")

@router.get("/{professional_id}", response_model=schemas.ProfissionalSchema)
def get_professional(professional_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """
    Busca um profissional específico pelo ID.
    Verifica se o profissional pertence ao estabelecimento do usuário.
    """
    professional = db.query(models.Profissional).filter(
        models.Profissional.id == professional_id,
        models.Profissional.salon_id == usuario.id
    ).first()
    if not professional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return professional

@router.put("/{professional_id}", response_model=schemas.ProfissionalSchema)
def update_professional(professional_id: int, professional_update: schemas.ProfissionalUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """
    Atualiza dados de um profissional.
    Permite desativar/reativar profissional através do campo 'ativo'.
    """
    professional = db.query(models.Profissional).filter(
        models.Profissional.id == professional_id,
        models.Profissional.salon_id == usuario.id
    ).first()
    if not professional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    # Verificar se email já existe em outro profissional
    if professional_update.email and professional_update.email != professional.email:
        existing = db.query(models.Profissional).filter(
            models.Profissional.email == professional_update.email,
            models.Profissional.salon_id == usuario.id,
            models.Profissional.id != professional_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Já existe profissional com este e-mail")

    for key, value in professional_update.model_dump(exclude_unset=True).items():
        setattr(professional, key, value)
    db.commit()
    db.refresh(professional)
    return professional

@router.delete("/{professional_id}")
def delete_professional(professional_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """
    Remove um profissional do estabelecimento.
    Verifica se não há agendamentos futuros com este profissional.
    """
    professional = db.query(models.Profissional).filter(
        models.Profissional.id == professional_id,
        models.Profissional.salon_id == usuario.id
    ).first()
    if not professional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    # Verificar se há agendamentos futuros
    from datetime import datetime
    future_appointments = db.query(models.Agendamento).filter(
        models.Agendamento.profissional_id == professional_id,
        models.Agendamento.appointment_datetime > datetime.now(),
        models.Agendamento.status.in_(["agendado", "confirmado"])
    ).count()

    if future_appointments > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir profissional com {future_appointments} agendamento(s) futuro(s)"
        )

    db.delete(professional)
    db.commit()
    return {"message": "Profissional removido com sucesso"}

@router.get("/public/{salon_id}")
def get_public_professionals(salon_id: int, db: Session = Depends(get_db)):
    """
    Lista todos os profissionais ativos de um estabelecimento específico.
    Endpoint público - usado pelo frontend do cliente para mostrar lista atualizada.
    """
    try:
        print(f"[PROFESSIONALS] Buscando profissionais públicos para salon_id={salon_id}")

        professionals = db.query(models.Profissional).filter(
            models.Profissional.salon_id == salon_id,
            models.Profissional.ativo == True
        ).all()

        print(f"[PROFESSIONALS] Encontrados {len(professionals)} profissionais ativos para salão {salon_id}")

        return {
            "success": True,
            "data": [{
                "id": p.id,
                "nome": p.nome,
                "email": p.email,
                "telefone": p.telefone,
                "especialidade": p.especialidade or "Geral"
            } for p in professionals]
        }

    except Exception as e:
        print(f"[PROFESSIONALS] Erro ao buscar profissionais públicos para salão {salon_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": "Erro interno ao buscar profissionais"
        }

@router.get("/available/{service_id}")
def get_available_professionals(service_id: int, db: Session = Depends(get_db)):
    """
    Lista profissionais disponíveis para um serviço específico.
    Endpoint público - não requer autenticação.
    """
    try:
        # Buscar serviço para obter salon_id
        service = db.query(models.Servico).filter(models.Servico.id == service_id).first()
        if not service:
            return {
                "success": False,
                "message": "Serviço não encontrado"
            }

        # Buscar profissionais que podem realizar o serviço específico
        professionals = db.query(models.Profissional).join(
            models.ServicoProfissional,
            models.Profissional.id == models.ServicoProfissional.profissional_id
        ).filter(
            models.ServicoProfissional.servico_id == service_id,
            models.Profissional.salon_id == service.salon_id,
            models.Profissional.ativo == True
        ).all()

        # Trata lista vazia
        if not professionals:
            return {
                "success": False,
                "message": "Nenhum barbeiro disponível para este serviço"
            }

        return {
            "success": True,
            "data": [{"id": p.id, "nome": p.nome, "especialidade": p.especialidade or "Geral"} for p in professionals]
        }

    except Exception as e:
        print(f"Erro ao buscar profissionais disponíveis: {str(e)}")
        return {
            "success": False,
            "message": "Erro interno ao buscar barbeiros disponíveis"
        }

@router.get("/available-times/{professional_id}")
def get_available_times(professional_id: int, date: str, service_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Lista horários disponíveis para um profissional em uma data específica.
    Endpoint público - não requer autenticação.
    """
    try:
        from datetime import datetime, time

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
                "message": "Não é possível agendar para datas passadas"
            }

        # Buscar profissional
        professional = db.query(models.Profissional).filter(
            models.Profissional.id == professional_id,
            models.Profissional.ativo == True
        ).first()

        if not professional:
            return {
                "success": False,
                "message": "Barbeiro não encontrado ou inativo"
            }

        # Buscar duração do serviço se informado
        service_duration = 60  # Padrão 60 minutos
        if service_id:
            service = db.query(models.Servico).filter(models.Servico.id == service_id).first()
            if service:
                service_duration = service.duracao_minutos or 60

        # Buscar horário de funcionamento da empresa
        try:
            from .business_hours import get_available_hours_for_date
            business_hours_result = get_available_hours_for_date(professional.salon_id, date, db)

            if business_hours_result.get('success'):
                # Usar horários do funcionamento da empresa
                available_times = business_hours_result['data']
            else:
                # Fallback para horários padrão se não conseguir buscar
                available_times = [
                    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30",
                    "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
                    "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
                    "17:00", "17:30"
                ]
        except Exception as e:
            print(f"Erro ao buscar horário de funcionamento: {e}")
            # Fallback para horários padrão
            available_times = [
                "08:00", "08:30", "09:00", "09:30", "10:00", "10:30",
                "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
                "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
                "17:00", "17:30"
            ]

        # Buscar agendamentos existentes para esta data e profissional
        try:
            print(f"[DEBUG] Buscando agendamentos para profissional {professional_id}, data {appointment_date}")
            existing_appointments = db.query(models.Agendamento).filter(
                models.Agendamento.profissional_id == professional_id,
                models.Agendamento.appointment_datetime >= datetime.combine(appointment_date, time.min),
                models.Agendamento.appointment_datetime < datetime.combine(appointment_date, time.max),
                models.Agendamento.status.in_(["SCHEDULED", "CONFIRMED"])
            ).all()
            print(f"[DEBUG] Encontrados {len(existing_appointments)} agendamentos existentes")
            for apt in existing_appointments:
                print(f"[DEBUG] Agendamento ID {apt.id}: {apt.appointment_datetime}, status: {apt.status}")
        except Exception as e:
            print(f"Erro ao buscar agendamentos existentes: {e}")
            existing_appointments = []

        # Calcular horários ocupados
        occupied_times = set()
        for appointment in existing_appointments:
            try:
                appointment_time = appointment.data_hora.time()
                time_str = appointment_time.strftime("%H:%M")
                occupied_times.add(time_str)

                # Bloquear horários subsequentes baseado na duração
                # Simplificado: bloquear apenas o horário exato por enquanto
                # TODO: implementar bloqueio baseado na duração do serviço

            except Exception as e:
                print(f"Erro ao processar agendamento {appointment.id}: {e}")
                continue

        # Filtrar horários disponíveis e criar lista de ocupados
        final_available_times = []
        final_occupied_times = []
        for time_slot in available_times:
            if time_slot not in occupied_times:
                final_available_times.append(time_slot)
            else:
                final_occupied_times.append(time_slot)

        # Trata lista vazia de disponíveis
        if not final_available_times:
            return {
                "success": False,
                "message": "Nenhum horário disponível para este barbeiro neste dia",
                "data": {
                    "available": [],
                    "occupied": final_occupied_times
                }
            }

        print(f"[AVAILABLE-TIMES] Retornando para profissional {professional_id}, data {date}:")
        print(f"[AVAILABLE-TIMES] Available: {final_available_times}")
        print(f"[AVAILABLE-TIMES] Occupied: {final_occupied_times}")

        return {
            "success": True,
            "data": {
                "available": final_available_times,
                "occupied": final_occupied_times
            }
        }

    except Exception as e:
        print(f"Erro ao buscar horários disponíveis: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": "Erro interno ao buscar horários disponíveis"
        }

@router.post("/{professional_id}/upload-foto")
async def upload_professional_photo(
    professional_id: int,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Faz upload da foto de um profissional.
    Apenas o dono do salão pode fazer upload da foto dos seus profissionais.
    """
    try:
        print(f"[UPLOAD_PHOTO] Usuário {current_user.id} fazendo upload de foto para profissional {professional_id}")

        # Verificar se profissional pertence ao estabelecimento do usuário
        professional = db.query(models.Profissional).filter(
            models.Profissional.id == professional_id,
            models.Profissional.salon_id == current_user.id
        ).first()

        if not professional:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")

        # Validar tipo de arquivo
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido. Use apenas imagens (JPEG, PNG, GIF, WebP)")

        # Validar tamanho do arquivo (máximo 2MB)
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > 2 * 1024 * 1024:  # 2MB
            raise HTTPException(status_code=400, detail="Arquivo muito grande. Tamanho máximo: 2MB")

        # Criar diretório se não existir
        upload_dir = Path("uploads/professionals")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Gerar nome único para o arquivo
        filename = file.filename or "foto.jpg"
        file_extension = Path(filename).suffix.lower()
        if not file_extension:
            file_extension = ".jpg"  # Extensão padrão

        unique_filename = f"professional_{professional_id}_{secrets.token_hex(8)}{file_extension}"
        file_path = upload_dir / unique_filename

        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Atualizar caminho da foto no banco de dados
        foto_url = f"/uploads/professionals/{unique_filename}"
        professional.foto = foto_url
        db.commit()

        print(f"[UPLOAD_PHOTO] Foto do profissional {professional_id} atualizada com sucesso: {foto_url}")

        return {
            "success": True,
            "message": "Foto atualizada com sucesso",
            "foto_url": foto_url,
            "file_size": file_size,
            "file_name": unique_filename
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[UPLOAD_PHOTO] Erro ao fazer upload da foto para profissional {professional_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao fazer upload da foto")

@router.get("/public/services/{professional_id}")
def get_public_professional_services(professional_id: int, db: Session = Depends(get_db)):
    """
    Lista todos os serviços que um profissional pode realizar.
    Endpoint público - usado pelo frontend do cliente.
    """
    try:
        print(f"[DEBUG] Buscando serviços para profissional {professional_id}")

        # Verificar se profissional existe e está ativo
        professional = db.query(models.Profissional).filter(
            models.Profissional.id == professional_id,
            models.Profissional.ativo == True
        ).first()

        if not professional:
            print(f"[DEBUG] Profissional {professional_id} não encontrado ou inativo")
            return {
                "success": False,
                "message": "Profissional não encontrado ou inativo"
            }

        print(f"[DEBUG] Profissional encontrado: {professional.nome}")

        # Buscar associações
        associations = db.query(models.ServicoProfissional).filter(
            models.ServicoProfissional.profissional_id == professional_id
        ).all()

        print(f"[DEBUG] Encontradas {len(associations)} associações")

        services = []
        for assoc in associations:
            service = db.query(models.Servico).filter(models.Servico.id == assoc.servico_id).first()
            if service:
                services.append({
                    "id": service.id,
                    "nome": service.nome,
                    "descricao": service.descricao,
                    "duracao_minutos": service.duracao_minutos,
                    "preco": float(service.preco)
                })
                print(f"[DEBUG] Serviço adicionado: {service.nome}")

        result = {
            "success": True,
            "professional": {
                "id": professional.id,
                "nome": professional.nome,
                "especialidade": professional.especialidade or "Geral"
            },
            "services": services
        }

        print(f"[DEBUG] Retornando {len(services)} serviços")
        return result

    except Exception as e:
        print(f"Erro ao buscar serviços públicos do profissional {professional_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": "Erro interno ao buscar serviços"
        }


# ========== ASSOCIAÇÃO PROFISSIONAL-SERVIÇO ==========

@router.get("/{professional_id}/services")
def get_professional_services(professional_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """
    Lista todos os serviços que um profissional pode realizar.
    """
    try:
        # Verificar se profissional pertence ao estabelecimento
        professional = db.query(models.Profissional).filter(
            models.Profissional.id == professional_id,
            models.Profissional.salon_id == usuario.id
        ).first()

        if not professional:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")

        # Buscar associações
        associations = db.query(models.ServicoProfissional).filter(
            models.ServicoProfissional.profissional_id == professional_id
        ).all()

        services = []
        for assoc in associations:
            service = db.query(models.Servico).filter(models.Servico.id == assoc.servico_id).first()
            if service:
                services.append({
                    "id": service.id,
                    "nome": service.nome,
                    "descricao": service.descricao,
                    "duracao_minutos": service.duracao_minutos,
                    "preco": float(service.preco)
                })

        return {
            "success": True,
            "professional": {
                "id": professional.id,
                "nome": professional.nome
            },
            "services": services
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao buscar serviços do profissional {professional_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar serviços")

@router.post("/{professional_id}/services")
def associate_professional_services(professional_id: int, service_ids: list[int], db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """
    Associa serviços a um profissional.
    Remove associações existentes e cria novas.
    """
    try:
        # Verificar se profissional pertence ao estabelecimento
        professional = db.query(models.Profissional).filter(
            models.Profissional.id == professional_id,
            models.Profissional.salon_id == usuario.id
        ).first()

        if not professional:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")

        # Verificar se todos os serviços existem e pertencem ao estabelecimento
        for service_id in service_ids:
            service = db.query(models.Servico).filter(
                models.Servico.id == service_id,
                models.Servico.salon_id == usuario.id
            ).first()
            if not service:
                raise HTTPException(status_code=404, detail=f"Serviço {service_id} não encontrado")

        # Remover associações existentes
        db.query(models.ServicoProfissional).filter(
            models.ServicoProfissional.profissional_id == professional_id
        ).delete()

        # Criar novas associações
        for service_id in service_ids:
            association = models.ServicoProfissional(
                profissional_id=professional_id,
                servico_id=service_id,
                salon_id=usuario.id
            )
            db.add(association)

        db.commit()

        return {
            "success": True,
            "message": f"Associados {len(service_ids)} serviços ao profissional {professional.nome}",
            "associated_services": len(service_ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Erro ao associar serviços ao profissional {professional_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao associar serviços")

@router.delete("/{professional_id}/services/{service_id}")
def remove_professional_service_association(professional_id: int, service_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """
    Remove a associação entre um profissional e um serviço específico.
    """
    try:
        # Verificar se profissional pertence ao estabelecimento
        professional = db.query(models.Profissional).filter(
            models.Profissional.id == professional_id,
            models.Profissional.salon_id == usuario.id
        ).first()

        if not professional:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")

        # Remover associação específica
        deleted = db.query(models.ServicoProfissional).filter(
            models.ServicoProfissional.profissional_id == professional_id,
            models.ServicoProfissional.servico_id == service_id
        ).delete()

        if deleted == 0:
            raise HTTPException(status_code=404, detail="Associação não encontrada")

        db.commit()

        return {
            "success": True,
            "message": "Associação removida com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Erro ao remover associação profissional-serviço: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao remover associação")