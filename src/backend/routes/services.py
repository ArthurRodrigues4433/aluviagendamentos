from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..dependencies import verificar_token
from ..models import Usuario

router = APIRouter()

@router.get("/", response_model=list[schemas.ServicoSchema])
def get_services(db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """Retorna serviços do salão do usuário autenticado com logs detalhados"""
    try:
        print(f"[SERVICES] Buscando serviços para salon_id={usuario.id}")

        services = db.query(models.Servico).filter(models.Servico.salon_id == usuario.id).all()

        print(f"[SERVICES] Encontrados {len(services)} serviços para o salão {usuario.id}")

        if not services:
            print(f"[SERVICES] Nenhum serviço encontrado para o salão {usuario.id}")
            return []

        return services

    except Exception as e:
        print(f"[SERVICES] Erro ao buscar serviços para usuário {usuario.id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

# Endpoint público para listar serviços (não requer autenticação)
@router.get("/public", response_model=list[schemas.ServicoSchema])
def get_public_services(db: Session = Depends(get_db)):
    """
    Lista todos os serviços disponíveis publicamente.
    Por enquanto, retorna serviços do salão padrão (ID 1).
    """
    try:
        print("[SERVICES] Buscando serviços públicos para salon_id=1")
        services = db.query(models.Servico).filter(models.Servico.salon_id == 1).all()
        print(f"[SERVICES] Encontrados {len(services)} serviços públicos")
        return services
    except Exception as e:
        print(f"[SERVICES] Erro em /public: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

# Endpoint público para listar serviços de um salão específico
@router.get("/public/{salon_id}", response_model=list[schemas.ServicoSchema])
def get_public_services_by_salon(salon_id: int, db: Session = Depends(get_db)):
    """
    Lista todos os serviços disponíveis publicamente para um salão específico.
    Usado pelo frontend do cliente para carregar serviços do seu salão.
    """
    try:
        print(f"[SERVICES] Buscando serviços públicos para salon_id={salon_id}")

        services = db.query(models.Servico).filter(models.Servico.salon_id == salon_id).all()

        print(f"[SERVICES] Encontrados {len(services)} serviços para salão {salon_id}")

        return services

    except Exception as e:
        print(f"[SERVICES] Erro ao buscar serviços públicos para salão {salon_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

@router.post("/", response_model=schemas.ServicoSchema)
def create_service(service: schemas.ServicoCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    print(f"[SERVICES] Criando serviço - usuario_id={usuario.id} (type: {type(usuario.id)}), service.salon_id={service.salon_id} (type: {type(service.salon_id)})")
    # Verificar se o serviço pertence ao salão do usuário
    if service.salon_id != usuario.id:
        print(f"[SERVICES] ERRO: salon_id mismatch - usuario.id={usuario.id} (type: {type(usuario.id)}), service.salon_id={service.salon_id} (type: {type(service.salon_id)})")
        raise HTTPException(status_code=403, detail="Não autorizado a criar serviço para outro salão")

    db_service = models.Servico(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("/{service_id}", response_model=schemas.ServicoSchema)
def get_service(service_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    service = db.query(models.Servico).filter(
        models.Servico.id == service_id,
        models.Servico.salon_id == usuario.id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return service

@router.put("/{service_id}", response_model=schemas.ServicoSchema)
def update_service(service_id: int, service_update: schemas.ServicoUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    service = db.query(models.Servico).filter(
        models.Servico.id == service_id,
        models.Servico.salon_id == usuario.id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    for key, value in service_update.model_dump(exclude_unset=True).items():
        setattr(service, key, value)
    db.commit()
    db.refresh(service)
    return service

@router.delete("/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    service = db.query(models.Servico).filter(
        models.Servico.id == service_id,
        models.Servico.salon_id == usuario.id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    db.delete(service)
    db.commit()
    return {"message": "Serviço deletado com sucesso"}