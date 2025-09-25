from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import secrets
import string
import os
import shutil
from pathlib import Path
from datetime import date, timedelta
from ..database import get_db
from .. import models, schemas
from ..dependencies import verificar_admin, verificar_token
from ..config import bcrypt_context
from ..core.config import filesystem

router = APIRouter()

@router.get("/public", response_model=List[schemas.SalonInfo])
def get_public_salons(db: Session = Depends(get_db)):
    """
    Lista todos os salões disponíveis publicamente.
    Usado para a tela de seleção de salão quando o cliente não tem um salão específico.

    Retorna apenas salões ativos com informações básicas públicas.
    """
    try:
        print("[SALON] Buscando lista de salões disponíveis")

        # Buscar apenas salões ativos (não administradores)
        salons = db.query(models.Usuario).filter(
            models.Usuario.is_active == True,
            models.Usuario.is_admin == False
        ).order_by(models.Usuario.name).all()

        if not salons:
            print("[SALON] Nenhum salão ativo encontrado")
            return []

        # Converter para formato de resposta
        salons_list = []
        for salon in salons:
            salon_info = {
                "id": salon.id,
                "nome": salon.name or "Salão",
                "telefone": getattr(salon, 'telefone', None),
                "logo": getattr(salon, 'logo', None),
                "endereco": getattr(salon, 'endereco', None),
                # Campos customizados da aparência do card
                "cardDisplayName": getattr(salon, 'card_display_name', None),
                "cardLocation": getattr(salon, 'card_location', None),
                "cardDescription": getattr(salon, 'card_description', None),
                "cardLogo": getattr(salon, 'card_logo', None)
            }
            salons_list.append(salon_info)

        print(f"[SALON] Encontrados {len(salons_list)} salões ativos")
        return salons_list

    except Exception as e:
        print(f"[SALON] Erro ao buscar lista de salões: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar salões disponíveis")

@router.get("/public/{salon_id}", response_model=schemas.SalonInfo)
def get_public_salon_info(salon_id: int, db: Session = Depends(get_db)):
    """
    Retorna informações públicas do salão (nome, logo, telefone, etc.)
    Endpoint público - usado pelo frontend do cliente para exibir info do salão.

    Validações de segurança:
    - Verifica se o salon_id é válido (existe no banco)
    - Verifica se o salão está ativo
    - Retorna apenas informações públicas seguras
    """
    try:
        print(f"[SALON] Buscando informações públicas para salon_id={salon_id}")

        # Validação: salon_id deve ser um número positivo
        if salon_id <= 0:
            raise HTTPException(status_code=400, detail="ID do salão inválido")

        # Buscar salão no banco de dados
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()

        if not salon:
            print(f"[SALON] Salão {salon_id} não encontrado no banco")
            raise HTTPException(status_code=404, detail="Salão não encontrado")

        # Validação: verificar se o salão está ativo
        if not salon.is_active:
            print(f"[SALON] Salão {salon_id} está inativo")
            raise HTTPException(status_code=403, detail="Este salão não está disponível no momento")

        # Retornar apenas informações públicas seguras
        salon_info = {
            "id": salon.id,
            "nome": salon.name or "Salão",
            "telefone": getattr(salon, 'telefone', None),
            "logo": getattr(salon, 'logo', None),
            "endereco": getattr(salon, 'endereco', None),
            # Campos customizados da aparência do card
            "cardDisplayName": getattr(salon, 'card_display_name', None),
            "cardLocation": getattr(salon, 'card_location', None),
            "cardDescription": getattr(salon, 'card_description', None),
            "cardLogo": getattr(salon, 'card_logo', None)
        }

        print(f"[SALON] Informações encontradas para salão {salon_id}: {salon_info}")

        return salon_info

    except HTTPException:
        # Re-lançar HTTPExceptions já tratadas
        raise
    except Exception as e:
        print(f"[SALON] Erro interno ao buscar informações do salão {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

def gerar_senha_temporaria():
    """Gera uma senha temporária segura de 12 caracteres"""
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(caracteres) for _ in range(12))

def gerar_email_salon(nome_salon: str):
    """Gera um email único para o salão baseado no nome"""
    # Remove espaços e caracteres especiais, converte para minúsculo
    base = ''.join(c for c in nome_salon.lower() if c.isalnum())
    return f"{base}@salon.temp"

def enviar_email_credenciais(email: str, senha: str, nome_salon: str, salon_id: int):
    """
    Simula envio de email com credenciais (implementação real seria com SMTP)
    """
    print(f"[EMAIL] Enviando credenciais para {email}")
    print(f"[EMAIL] Salão: {nome_salon}")
    print(f"[EMAIL] Senha temporária: {senha}")
    print(f"[EMAIL] Link de acesso: https://meusite.com/login?salon_id={salon_id}")
    # TODO: Implementar envio real de email com SMTP

def registrar_log_auditoria(db: Session, acao: str, usuario_id: Optional[int] = None, salon_id: Optional[int] = None, detalhes: Optional[str] = None, ip_address: Optional[str] = None):
    """Registra uma ação no log de auditoria"""
    log_entry = models.AuditLog(
        acao=acao,
        usuario_id=usuario_id,
        salon_id=salon_id,
        detalhes=detalhes,
        endereco_ip=ip_address
    )
    db.add(log_entry)
    db.commit()

@router.post("/admin/create", response_model=dict)
def create_salon_admin(
    salon_data: schemas.SalonCreateAdmin,
    admin: models.Usuario = Depends(verificar_admin),
    db: Session = Depends(get_db)
):
    """
    Endpoint privado para administradores criarem novos salões.
    Apenas usuários com admin=True podem acessar.
    Gera automaticamente email e senha temporária.
    """
    try:
        print(f"[CREATE_SALON] Admin {admin.id} criando salão: {salon_data.nome}")

        # Gerar credenciais automaticamente
        email_gerado = salon_data.email or gerar_email_salon(salon_data.nome)
        senha_temporaria = gerar_senha_temporaria()

        # Verificar se email já existe
        existing_user = db.query(models.Usuario).filter(models.Usuario.email == email_gerado).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email já cadastrado no sistema")

        # Criptografar senha
        senha_hash = bcrypt_context.hash(senha_temporaria)

        # Definir data de vencimento da mensalidade (30 dias a partir de hoje)
        data_vencimento = date.today() + timedelta(days=30)

        # Criar novo salão
        novo_salon = models.Usuario(
            name=salon_data.nome,
            email=email_gerado,
            password=senha_hash,
            is_active=True,  # Salão começa ativo
            is_admin=False,  # Não é admin
            subscription_paid=False,  # Mensalidade não paga inicialmente
            subscription_due_date=data_vencimento,
            has_temp_password=True,  # Senha é temporária
            is_first_login=True  # Primeiro login pendente
        )

        db.add(novo_salon)
        db.commit()
        db.refresh(novo_salon)

        # Registrar log de auditoria
        registrar_log_auditoria(
            db=db,
            acao="criacao_salon",
            usuario_id=admin.id,
            salon_id=novo_salon.id,
            detalhes=f"Salão criado: {salon_data.nome}"
        )

        # Enviar email com credenciais (simulado)
        enviar_email_credenciais(
            email=email_gerado,
            senha=senha_temporaria,
            nome_salon=salon_data.nome,
            salon_id=novo_salon.id
        )

        print(f"[CREATE_SALON] Salão criado com sucesso: ID={novo_salon.id}, email={email_gerado}")

        return {
            "success": True,
            "salon_id": novo_salon.id,
            "nome": salon_data.nome,
            "email": email_gerado,
            "data_vencimento_mensalidade": data_vencimento.isoformat(),
            "message": "Salão criado com sucesso. Credenciais enviadas por email."
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[CREATE_SALON] Erro ao criar salão: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar salão")

@router.put("/admin/{salon_id}/subscription")
def update_subscription_status(
    salon_id: int,
    subscription_data: schemas.SubscriptionUpdate,
    admin: models.Usuario = Depends(verificar_admin),
    db: Session = Depends(get_db)
):
    """
    Endpoint para administradores atualizarem status de mensalidade de um salão.
    Usado para registrar pagamentos ou atualizações manuais.
    """
    try:
        print(f"[UPDATE_SUBSCRIPTION] Admin {admin.id} atualizando mensalidade do salão {salon_id}")

        # Buscar salão
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Salão não encontrado")

        # Atualizar campos
        salon.subscription_paid = subscription_data.mensalidade_pago
        if subscription_data.data_vencimento:
            salon.subscription_due_date = subscription_data.data_vencimento

        db.commit()

        # Registrar log de auditoria
        registrar_log_auditoria(
            db=db,
            acao="atualizacao_mensalidade",
            usuario_id=admin.id,
            salon_id=salon_id,
            detalhes=f"Mensalidade atualizada: pago={subscription_data.mensalidade_pago}, vencimento={subscription_data.data_vencimento}"
        )

        print(f"[UPDATE_SUBSCRIPTION] Mensalidade atualizada com sucesso para salão {salon_id}")

        return {
            "success": True,
            "message": "Status de mensalidade atualizado com sucesso",
            "salon_id": salon_id,
            "mensalidade_pago": subscription_data.mensalidade_pago,
            "data_vencimento_mensalidade": salon.subscription_due_date
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[UPDATE_SUBSCRIPTION] Erro ao atualizar mensalidade: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar mensalidade")

@router.get("/admin/subscriptions")
def get_subscriptions_status(admin: models.Usuario = Depends(verificar_admin), db: Session = Depends(get_db)):
    """
    Endpoint para administradores visualizarem status de mensalidade de todos os salões.
    """
    try:
        print(f"[GET_SUBSCRIPTIONS] Admin {admin.id} consultando status de mensalidades")

        # Buscar todos os salões com informações de mensalidade
        salons = db.query(models.Usuario).filter(models.Usuario.is_admin == False).all()

        subscriptions = []
        for salon in salons:
            subscriptions.append({
                "id": salon.id,
                "nome": salon.name,
                "email": salon.email,
                "ativo": salon.is_active,
                "mensalidade_pago": salon.subscription_paid,
                "data_vencimento_mensalidade": salon.subscription_due_date,
                "dias_atraso": None  # TODO: calcular dias de atraso
            })

        return {
            "success": True,
            "subscriptions": subscriptions
        }

    except Exception as e:
        print(f"[GET_SUBSCRIPTIONS] Erro ao consultar mensalidades: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao consultar mensalidades")

@router.get("/admin/owners")
def get_owners_list(admin: models.Usuario = Depends(verificar_admin), db: Session = Depends(get_db)):
    """
    Endpoint para administradores visualizarem lista de todos os donos de salão.
    """
    try:
        print(f"[GET_OWNERS] Admin {admin.id} consultando lista de donos")

        # Buscar todos os donos (usuários que não são admin)
        owners = db.query(models.Usuario).filter(models.Usuario.is_admin == False).all()
        print(f"[GET_OWNERS] Query executada: encontrados {len(owners)} donos")

        owners_list = []
        for owner in owners:
            owner_data = {
                "id": owner.id,
                "nome": owner.name,
                "email": owner.email,
                "ativo": owner.is_active,
                "mensalidade_pago": owner.subscription_paid,
                "data_vencimento_mensalidade": owner.subscription_due_date,
                "criado_em": getattr(owner, 'created_at', None),
                "criado_por": getattr(owner, 'created_by', None),
                "senha_temporaria": owner.has_temp_password
            }
            owners_list.append(owner_data)
            print(f"[GET_OWNERS] Dono {owner.id}: nome='{owner.name}', email='{owner.email}', ativo={owner.is_active}, pago={owner.subscription_paid}, criado_em={owner.created_at}")

        print(f"[GET_OWNERS] Retornando {len(owners_list)} donos para o frontend")
        return {
            "success": True,
            "owners": owners_list
        }

    except Exception as e:
        print(f"[GET_OWNERS] Erro ao consultar donos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao consultar donos")

@router.get("/{salon_id}")
def get_salon_details(salon_id: int, current_user: models.Usuario = Depends(verificar_token), db: Session = Depends(get_db)):
    """
    Retorna detalhes completos do salão para o dono.
    Apenas o dono do salão pode acessar seus próprios dados.
    """
    try:
        print(f"[GET_SALON] Usuário {current_user.id} solicitando detalhes do salão {salon_id}")

        # Verificar se o usuário é o dono do salão
        if current_user.id != salon_id:
            raise HTTPException(status_code=403, detail="Acesso negado - você só pode acessar dados do seu próprio salão")

        # Buscar salão
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Salão não encontrado")

        # Retornar dados completos do salão
        salon_data = {
            "id": salon.id,
            "nome": salon.name,
            "owner_name": getattr(salon, 'owner_name', None),
            "email": salon.email,
            "telefone": getattr(salon, 'telefone', None),
            "endereco": getattr(salon, 'endereco', None),
            "descricao": getattr(salon, 'descricao', None),
            "logo": getattr(salon, 'logo', None),
            "ativo": salon.is_active,
            "mensalidade_pago": salon.subscription_paid,
            "data_vencimento_mensalidade": salon.subscription_due_date
        }

        print(f"[GET_SALON] Dados retornados para salão {salon_id}")
        return salon_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"[GET_SALON] Erro ao buscar detalhes do salão {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar dados do salão")

@router.put("/{salon_id}/appearance")
def update_salon_appearance(salon_id: int, appearance_data: dict, current_user: models.Usuario = Depends(verificar_token), db: Session = Depends(get_db)):
    """
    Permite ao dono do salão atualizar a aparência customizada do card.
    Apenas o dono pode atualizar sua própria aparência.
    """
    try:
        print(f"[UPDATE_APPEARANCE] Usuário {current_user.id} atualizando aparência do salão {salon_id}")
        print(f"[UPDATE_APPEARANCE] Dados recebidos: {appearance_data}")
        print(f"[UPDATE_APPEARANCE] Chaves recebidas: {list(appearance_data.keys())}")

        # Verificar se o usuário é o dono do salão
        if current_user.id != salon_id:
            raise HTTPException(status_code=403, detail="Acesso negado - você só pode atualizar a aparência do seu próprio salão")

        # Buscar salão
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Salão não encontrado")

        # Campos permitidos para atualização da aparência
        allowed_fields = ['cardDisplayName', 'cardLocation', 'cardDescription', 'cardLogo']
        updated_fields = []

        print(f"[UPDATE_APPEARANCE] Campos permitidos: {allowed_fields}")

        # Atualizar apenas campos permitidos
        for field in allowed_fields:
            if field in appearance_data:
                print(f"[UPDATE_APPEARANCE] Processando campo {field}: {appearance_data[field]}")
                db_field = field.replace('card', '').lower()  # cardDisplayName -> display_name
                if db_field == 'displayname':
                    db_field = 'display_name'
                setattr(salon, f'card_{db_field}', appearance_data[field])
                updated_fields.append(field)
            else:
                print(f"[UPDATE_APPEARANCE] Campo {field} NÃO encontrado nos dados recebidos")

        # Se cardLogo não foi enviado mas há um logo geral, usar como cardLogo
        if 'cardLogo' not in appearance_data and salon.logo and not salon.card_logo:
            print(f"[UPDATE_APPEARANCE] cardLogo não enviado, usando logo geral como fallback: {salon.logo}")
            salon.card_logo = salon.logo
            if 'cardLogo' not in updated_fields:
                updated_fields.append('cardLogo')

        print(f"[UPDATE_APPEARANCE] Campos que serão atualizados: {updated_fields}")

        # Commit das mudanças
        db.commit()
        db.refresh(salon)

        # Registrar log de auditoria
        registrar_log_auditoria(
            db=db,
            acao="atualizacao_aparencia_card",
            usuario_id=current_user.id,
            salon_id=salon_id,
            detalhes=f"Campos atualizados: {', '.join(updated_fields)}"
        )

        print(f"[UPDATE_APPEARANCE] Aparência do salão {salon_id} atualizada com sucesso. Campos: {updated_fields}")

        return {
            "success": True,
            "message": "Aparência do card atualizada com sucesso",
            "updated_fields": updated_fields
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[UPDATE_APPEARANCE] Erro ao atualizar aparência do salão {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar aparência do card")

@router.put("/{salon_id}")
def update_salon_details(salon_id: int, salon_update: dict, current_user: models.Usuario = Depends(verificar_token), db: Session = Depends(get_db)):
    """
    Permite ao dono do salão atualizar suas informações básicas.
    Apenas o dono pode atualizar seu próprio salão.
    """
    try:
        print(f"[UPDATE_SALON] Usuário {current_user.id} atualizando salão {salon_id}")
        print(f"[UPDATE_SALON] Dados recebidos: {salon_update}")

        # Verificar se o usuário é o dono do salão
        if current_user.id != salon_id:
            raise HTTPException(status_code=403, detail="Acesso negado - você só pode atualizar seu próprio salão")

        # Buscar salão
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Salão não encontrado")

        print(f"[UPDATE_SALON] Estado atual do salão antes da atualização:")
        print(f"  nome: '{salon.name}'")
        print(f"  telefone: '{getattr(salon, 'telefone', None)}'")
        print(f"  endereco: '{getattr(salon, 'endereco', None)}'")
        print(f"  descricao: '{getattr(salon, 'descricao', None)}'")

        # Campos permitidos para atualização
        allowed_fields = ['nome', 'telefone', 'endereco', 'descricao']
        updated_fields = []

        # Atualizar apenas campos permitidos
        for field in allowed_fields:
            if field in salon_update:
                old_value = getattr(salon, field if field != 'nome' else 'name', None)
                new_value = salon_update[field]
                print(f"[UPDATE_SALON] Campo '{field}': '{old_value}' -> '{new_value}'")

                if field == 'nome':
                    salon.name = salon_update[field]
                else:
                    setattr(salon, field, salon_update[field])
                updated_fields.append(field)

        # Commit das mudanças
        print(f"[ADMIN-COMPANY] Antes do commit - owner_name: '{getattr(salon, 'owner_name', None)}'")
        db.commit()
        db.refresh(salon)
        print(f"[ADMIN-COMPANY] Após commit e refresh - owner_name: '{getattr(salon, 'owner_name', None)}'")

        print(f"[UPDATE_SALON] Estado do salão após atualização:")
        print(f"  nome: '{salon.name}'")
        print(f"  telefone: '{getattr(salon, 'telefone', None)}'")
        print(f"  endereco: '{getattr(salon, 'endereco', None)}'")
        print(f"  descricao: '{getattr(salon, 'descricao', None)}'")

        # Registrar log de auditoria
        registrar_log_auditoria(
            db=db,
            acao="atualizacao_salon",
            usuario_id=current_user.id,
            salon_id=salon_id,
            detalhes=f"Campos atualizados: {', '.join(updated_fields)}"
        )

        print(f"[UPDATE_SALON] Salão {salon_id} atualizado com sucesso. Campos: {updated_fields}")

        return {
            "success": True,
            "message": "Dados do salão atualizados com sucesso",
            "updated_fields": updated_fields
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[UPDATE_SALON] Erro ao atualizar salão {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar dados do salão")

@router.post("/{salon_id}/upload-logo")
async def upload_salon_logo(
    salon_id: int,
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Faz upload do logo do salão.
    Apenas o dono do salão pode fazer upload do logo.
    """
    try:
        print(f"[UPLOAD_LOGO] Usuário {current_user.id} fazendo upload de logo para salão {salon_id}")

        # Verificar se o usuário é o dono do salão
        if current_user.id != salon_id:
            raise HTTPException(status_code=403, detail="Acesso negado - você só pode fazer upload do logo do seu próprio salão")

        # Buscar salão
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Salão não encontrado")

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
        upload_dir = Path(filesystem.LOGO_UPLOAD_DIRECTORY)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Gerar nome único para o arquivo
        filename = file.filename or "upload.jpg"
        file_extension = Path(filename).suffix.lower()
        if not file_extension:
            file_extension = ".jpg"  # Extensão padrão

        unique_filename = f"salon_{salon_id}_logo_{secrets.token_hex(8)}{file_extension}"
        file_path = upload_dir / unique_filename

        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Atualizar caminho do logo no banco de dados
        logo_url = f"/logos/{unique_filename}"
        salon.logo = logo_url
        db.commit()

        # Registrar log de auditoria
        registrar_log_auditoria(
            db=db,
            acao="upload_logo",
            usuario_id=current_user.id,
            salon_id=salon_id,
            detalhes=f"Logo atualizado: {unique_filename}"
        )

        print(f"[UPLOAD_LOGO] Logo do salão {salon_id} atualizado com sucesso: {logo_url}")

        return {
            "success": True,
            "message": "Logo atualizado com sucesso",
            "logo_url": logo_url,
            "file_size": file_size,
            "file_name": unique_filename
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[UPLOAD_LOGO] Erro ao fazer upload do logo para salão {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao fazer upload do logo")

@router.get("/{salon_id}/share-link")
def get_salon_share_link(
    salon_id: int,
    current_user: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Gera link único para compartilhar o salão com clientes.
    Apenas o dono do salão pode gerar o link.
    """
    try:
        print(f"[SHARE_LINK] Usuário {current_user.id} solicitando link de compartilhamento para salão {salon_id}")

        # Verificar se o usuário é o dono do salão
        if current_user.id != salon_id:
            raise HTTPException(status_code=403, detail="Acesso negado - você só pode gerar link do seu próprio salão")

        # Buscar salão
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Salão não encontrado")

        # Verificar se o salão está ativo
        if not salon.is_active:
            raise HTTPException(status_code=403, detail="Salão inativo - não é possível gerar link de compartilhamento")

        # Gerar link único
        base_url = "http://localhost:8000"  # Em produção, usar variável de ambiente
        share_link = f"{base_url}/salon-selection.html?salon={salon_id}"

        print(f"[SHARE_LINK] Link gerado para salão {salon_id}: {share_link}")

        return {
            "success": True,
            "share_link": share_link,
            "salon_name": salon.name,
            "expires_in": None,  # Link não expira
            "is_active": salon.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[SHARE_LINK] Erro ao gerar link de compartilhamento para salão {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao gerar link de compartilhamento")

@router.get("/{salon_id}/qr-code")
def get_salon_qr_code(
    salon_id: int,
    current_user: models.Usuario = Depends(verificar_token),
    db: Session = Depends(get_db)
):
    """
    Gera QR code para o link de compartilhamento do salão.
    Apenas o dono do salão pode gerar o QR code.
    """
    try:
        print(f"[QR_CODE] Usuário {current_user.id} solicitando QR code para salão {salon_id}")

        # Verificar se o usuário é o dono do salão
        if current_user.id != salon_id:
            raise HTTPException(status_code=403, detail="Acesso negado - você só pode gerar QR code do seu próprio salão")

        # Buscar salão
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Salão não encontrado")

        # Verificar se o salão está ativo
        if not salon.is_active:
            raise HTTPException(status_code=403, detail="Salão inativo - não é possível gerar QR code")

        # Gerar link para o QR code
        base_url = "http://localhost:8000"  # Em produção, usar variável de ambiente
        share_link = f"{base_url}/salon-selection.html?salon={salon_id}"

        # Por enquanto, retornar apenas o link (QR code seria gerado no frontend ou com biblioteca adicional)
        print(f"[QR_CODE] QR code preparado para salão {salon_id}")

        return {
            "success": True,
            "qr_data": share_link,
            "salon_name": salon.name,
            "message": "QR code gerado com sucesso (implementação completa em desenvolvimento)",
            "implementation_status": "partial"  # Indica que é uma implementação parcial
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[QR_CODE] Erro ao gerar QR code para salão {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao gerar QR code")

# ============ ROTAS PARA ADMIN ACESSAR CONFIGURAÇÕES DE QUALQUER EMPRESA ============

@router.get("/admin/company/{salon_id}/details")
def get_company_details_admin(salon_id: int, admin: models.Usuario = Depends(verificar_admin), db: Session = Depends(get_db)):
    """
    Endpoint para administradores acessarem dados completos de qualquer empresa.
    Apenas usuários com admin=True podem acessar.
    """
    try:
        print(f"[ADMIN-COMPANY] Admin {admin.id} solicitando detalhes da empresa {salon_id}")

        # Buscar empresa
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

        # Retornar dados completos da empresa
        salon_data = {
            "id": salon.id,
            "nome": salon.name,
            "nome_dono": getattr(salon, 'owner_name', None),
            "email": salon.email,
            "telefone": getattr(salon, 'telefone', None),
            "endereco": getattr(salon, 'endereco', None),
            "descricao": getattr(salon, 'descricao', None),
            "logo": getattr(salon, 'logo', None),
            "ativo": salon.is_active,
            "mensalidade_pago": salon.subscription_paid,
            "data_vencimento_mensalidade": salon.subscription_due_date,
            # Campos de aparência do card
            "card_display_name": getattr(salon, 'card_display_name', None),
            "card_location": getattr(salon, 'card_location', None),
            "card_description": getattr(salon, 'card_description', None),
            "card_logo": getattr(salon, 'card_logo', None)
        }

        print(f"[ADMIN-COMPANY] Dados retornados para empresa {salon_id}")
        return salon_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADMIN-COMPANY] Erro ao buscar detalhes da empresa {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar dados da empresa")

@router.put("/admin/company/{salon_id}/basic-info")
def update_company_basic_info_admin(salon_id: int, basic_data: dict, admin: models.Usuario = Depends(verificar_admin), db: Session = Depends(get_db)):
    """
    Permite ao admin atualizar informações básicas de qualquer empresa.
    Apenas usuários com admin=True podem acessar.
    """
    try:
        print(f"[ADMIN-COMPANY] Admin {admin.id} atualizando informações básicas da empresa {salon_id}")
        print(f"[ADMIN-COMPANY] Dados recebidos: {basic_data}")

        # Buscar empresa
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

        # Campos permitidos para atualização
        allowed_fields = ['nome', 'telefone', 'endereco', 'descricao']
        updated_fields = []

        # Atualizar apenas campos permitidos
        for field in allowed_fields:
            if field in basic_data:
                old_value = getattr(salon, field if field != 'nome' else 'name', None)
                new_value = basic_data[field]
                print(f"[ADMIN-COMPANY] Campo '{field}': '{old_value}' -> '{new_value}'")

                if field == 'nome':
                    salon.name = basic_data[field]
                else:
                    setattr(salon, field, basic_data[field])
                updated_fields.append(field)

        # Commit das mudanças
        db.commit()
        db.refresh(salon)

        # Registrar log de auditoria
        registrar_log_auditoria(
            db=db,
            acao="admin_atualizacao_basica_empresa",
            usuario_id=admin.id,
            salon_id=salon_id,
            detalhes=f"Campos atualizados: {', '.join(updated_fields)}"
        )

        print(f"[ADMIN-COMPANY] Empresa {salon_id} atualizada com sucesso. Campos: {updated_fields}")

        return {
            "success": True,
            "message": "Informações básicas atualizadas com sucesso",
            "updated_fields": updated_fields
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ADMIN-COMPANY] Erro ao atualizar empresa {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar dados da empresa")

@router.put("/admin/company/{salon_id}/appearance")
def update_company_appearance_admin(salon_id: int, appearance_data: dict, admin: models.Usuario = Depends(verificar_admin), db: Session = Depends(get_db)):
    """
    Permite ao admin atualizar a aparência customizada do card de qualquer empresa.
    Apenas usuários com admin=True podem acessar.
    """
    try:
        print(f"[ADMIN-COMPANY] Admin {admin.id} atualizando aparência da empresa {salon_id}")
        print(f"[ADMIN-COMPANY] Dados recebidos: {appearance_data}")

        # Buscar empresa
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

        # Campos permitidos para atualização da aparência
        allowed_fields = ['cardDisplayName', 'cardLocation', 'cardDescription', 'cardLogo']
        updated_fields = []

        # Atualizar apenas campos permitidos
        for field in allowed_fields:
            if field in appearance_data:
                print(f"[ADMIN-COMPANY] Processando campo {field}: {appearance_data[field]}")
                db_field = field.replace('card', '').lower()  # cardDisplayName -> display_name
                if db_field == 'displayname':
                    db_field = 'display_name'
                setattr(salon, f'card_{db_field}', appearance_data[field])
                updated_fields.append(field)

        # Se cardLogo não foi enviado mas há um logo geral, usar como cardLogo
        if 'cardLogo' not in appearance_data and salon.logo and not salon.card_logo:
            print(f"[ADMIN-COMPANY] cardLogo não enviado, usando logo geral como fallback: {salon.logo}")
            salon.card_logo = salon.logo
            if 'cardLogo' not in updated_fields:
                updated_fields.append('cardLogo')

        print(f"[ADMIN-COMPANY] Campos que serão atualizados: {updated_fields}")

        # Commit das mudanças
        db.commit()
        db.refresh(salon)

        # Registrar log de auditoria
        registrar_log_auditoria(
            db=db,
            acao="admin_atualizacao_aparencia_empresa",
            usuario_id=admin.id,
            salon_id=salon_id,
            detalhes=f"Campos atualizados: {', '.join(updated_fields)}"
        )

        print(f"[ADMIN-COMPANY] Aparência da empresa {salon_id} atualizada com sucesso. Campos: {updated_fields}")

        return {
            "success": True,
            "message": "Aparência do card atualizada com sucesso",
            "updated_fields": updated_fields
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ADMIN-COMPANY] Erro ao atualizar aparência da empresa {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar aparência do card")

@router.put("/admin/company/{salon_id}/owner-info")
def update_company_owner_info_admin(salon_id: int, owner_data: dict, admin: models.Usuario = Depends(verificar_admin), db: Session = Depends(get_db)):
    """
    Permite ao admin atualizar informações do dono de qualquer empresa.
    Apenas usuários com admin=True podem acessar.
    """
    try:
        print(f"[ADMIN-COMPANY] Admin {admin.id} atualizando informações do dono da empresa {salon_id}")
        print(f"[ADMIN-COMPANY] Dados recebidos: {owner_data}")
        print(f"[ADMIN-COMPANY] Chaves recebidas: {list(owner_data.keys())}")
        print(f"[ADMIN-COMPANY] owner_name no payload: {'owner_name' in owner_data}")

        # Buscar empresa (que é o próprio dono)
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

        # Campos permitidos para atualização do dono
        allowed_fields = ['name', 'owner_name', 'email', 'telefone', 'experiencia']
        updated_fields = []

        # Atualizar apenas campos permitidos
        for field in allowed_fields:
            if field in owner_data:
                old_value = getattr(salon, field, None)
                new_value = owner_data[field]
                print(f"[ADMIN-COMPANY] Campo '{field}': '{old_value}' -> '{new_value}'")

                setattr(salon, field, owner_data[field])
                updated_fields.append(field)

        # Debug: verificar se owner_name foi atualizado
        print(f"[ADMIN-COMPANY] Após atualização - owner_name: '{getattr(salon, 'owner_name', None)}'")
        print(f"[ADMIN-COMPANY] Campos atualizados: {updated_fields}")

        # Commit das mudanças
        db.commit()
        db.refresh(salon)

        # Registrar log de auditoria
        registrar_log_auditoria(
            db=db,
            acao="admin_atualizacao_dono_empresa",
            usuario_id=admin.id,
            salon_id=salon_id,
            detalhes=f"Campos atualizados: {', '.join(updated_fields)}"
        )

        print(f"[ADMIN-COMPANY] Informações do dono da empresa {salon_id} atualizadas com sucesso. Campos: {updated_fields}")

        return {
            "success": True,
            "message": "Informações do dono atualizadas com sucesso",
            "updated_fields": updated_fields
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ADMIN-COMPANY] Erro ao atualizar dono da empresa {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar informações do dono")

@router.post("/admin/company/{salon_id}/upload-logo")
async def upload_company_logo_admin(salon_id: int, file: UploadFile = File(...), admin: models.Usuario = Depends(verificar_admin), db: Session = Depends(get_db)):
    """
    Faz upload do logo de qualquer empresa.
    Apenas usuários com admin=True podem acessar.
    """
    try:
        print(f"[ADMIN-COMPANY] Admin {admin.id} fazendo upload de logo para empresa {salon_id}")

        # Buscar empresa
        salon = db.query(models.Usuario).filter(models.Usuario.id == salon_id).first()
        if not salon:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

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
        upload_dir = Path(filesystem.LOGO_UPLOAD_DIRECTORY)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Gerar nome único para o arquivo
        filename = file.filename or "upload.jpg"
        file_extension = Path(filename).suffix.lower()
        if not file_extension:
            file_extension = ".jpg"  # Extensão padrão

        unique_filename = f"salon_{salon_id}_logo_{secrets.token_hex(8)}{file_extension}"
        file_path = upload_dir / unique_filename

        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Atualizar caminho do logo no banco de dados
        logo_url = f"/logos/{unique_filename}"
        salon.logo = logo_url
        db.commit()

        # Registrar log de auditoria
        registrar_log_auditoria(
            db=db,
            acao="admin_upload_logo_empresa",
            usuario_id=admin.id,
            salon_id=salon_id,
            detalhes=f"Logo atualizado: {unique_filename}"
        )

        print(f"[ADMIN-COMPANY] Logo da empresa {salon_id} atualizado com sucesso: {logo_url}")

        return {
            "success": True,
            "message": "Logo atualizado com sucesso",
            "logo_url": logo_url,
            "file_size": file_size,
            "file_name": unique_filename
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ADMIN-COMPANY] Erro ao fazer upload do logo para empresa {salon_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao fazer upload do logo")