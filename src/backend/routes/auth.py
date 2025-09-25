from fastapi import APIRouter, Depends, HTTPException
from ..models import Usuario, AuditLog
from ..dependencies import pegar_sessao, verificar_token
from ..config import bcrypt_context
from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from ..schemas import UsuarioSchema, LoginSchema, ChangePasswordSchema
from ..core.logging import get_logger
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
import secrets
import string

# Configuração de hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Configurar logger
logger = get_logger()

router = APIRouter()

# CRIAR TOKEN
def criar_token(usuario_id, role="dono", duracao_token=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    """
    Cria token JWT com claims de role
    role: "dono" para donos de estabelecimento, "cliente" para clientes
    """
    data_expiracao = datetime.now(timezone.utc) + duracao_token
    dic_info = {
        "sub": str(usuario_id),
        "exp": data_expiracao,
        "role": role,
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(dic_info, SECRET_KEY, ALGORITHM)
    return encoded_jwt

# AUTENTICAÇÃO DO USUARIO
def autenticar_usuario(email: str, senha: str, session: Session):
    usuario = session.query(Usuario).filter(Usuario.email==email).first() #type: ignore
    if not usuario:
        return False
    elif not bcrypt_context.verify(senha, usuario.password):  # type: ignore[arg-type]
        return False
    return usuario


# ROTA PARA REGISTRAR NOVO USUARIO
@router.post("/register")
def registrar_usuario(usuario_schema: UsuarioSchema, session: Session = Depends(pegar_sessao)):
    try:
        usuario = session.query(Usuario).filter(Usuario.email==usuario_schema.email).first()
        if usuario:
            return {
                "success": False,
                "error": "Usuário já existe!"
            }

        senha_criptografada = bcrypt_context.hash(usuario_schema.senha)
        novo_usuario = Usuario(
            name=usuario_schema.nome,
            email=usuario_schema.email,
            password=senha_criptografada,
            is_active=usuario_schema.ativo,
            is_admin=usuario_schema.admin
        )
        session.add(novo_usuario)
        session.commit()

        return {
            "success": True,
            "user_id": novo_usuario.id,
            "message": "Usuário registrado com sucesso!",
            "email": usuario_schema.email
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Erro no registro de usuário: {str(e)}")

        # Verificar se é erro de constraint UNIQUE
        if "UNIQUE constraint failed" in str(e):
            if "email" in str(e):
                return {
                    "success": False,
                    "error": "E-mail já cadastrado no sistema"
                }

        # Para outros erros, retornar mensagem genérica
        return {
            "success": False,
            "error": "Erro interno do servidor. Tente novamente."
        }


# rota para login e criação do token
@router.post("/login")
async def login(login_schema: LoginSchema, session: Session =  Depends(pegar_sessao)):
    """
    Login para donos de salão.
    Busca apenas na tabela Usuario (donos).
    Sempre retorna role="dono".
    Verifica se o salão está ativo e se a mensalidade está paga.
    """
    usuario = autenticar_usuario(login_schema.email, login_schema.senha, session)
    if not usuario:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    # Verificações de segurança para donos de salão
    if not usuario.is_active:
        logger.warning(f"Acesso bloqueado: salão {usuario.id} inativo")
        raise HTTPException(status_code=403, detail="Este salão está temporariamente indisponível")

    if not usuario.subscription_paid:
        logger.warning(f"Acesso bloqueado: mensalidade não paga para salão {usuario.id}")
        raise HTTPException(status_code=403, detail="Acesso bloqueado: mensalidade em atraso. Regularize o pagamento para continuar.")

    # Verificar se é admin ou dono normal
    role = "admin" if usuario.is_admin else "dono"

    logger.info(f"Usuário autenticado: ID={usuario.id}, nome={usuario.name}, role={role}")

    # Registrar log de auditoria para login
    from ..models import AuditLog
    log_entry = AuditLog(
        acao="login",
        usuario_id=usuario.id,
        salon_id=usuario.id,  # Mesmo ID pois é o próprio salão
        detalhes="Login realizado com sucesso"
    )
    session.add(log_entry)
    session.commit()

    access_token = criar_token(usuario.id, role=role)
    refresh_token = criar_token(usuario.id, role=role, duracao_token=timedelta(days=1))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": role
    }
    

# rota para trocar o token via form data no docs
@router.post("/login-form")
async def login_form(dados_formulario: OAuth2PasswordRequestForm = Depends(), session: Session =  Depends(pegar_sessao)):
    usuario = autenticar_usuario(dados_formulario.username, dados_formulario.password, session)
    if not usuario:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    else:
        access_token = criar_token(usuario.id, role="dono")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": "dono"
            }
    
    
# rota para renovar o token
@router.get("/refresh")
async def use_refresh_token(usuario: Usuario = Depends(verificar_token)):
    access_token = criar_token(usuario.id, role="dono")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "dono"
        }

# rota para obter dados do salão logado
@router.get("/me")
async def get_salon_info(usuario: Usuario = Depends(verificar_token)):
    return {
        "id": usuario.id,
        "nome": usuario.name,
        "email": usuario.email,
        "ativo": usuario.is_active,
        "admin": usuario.is_admin,
        "mensalidade_pago": getattr(usuario, 'subscription_paid', False),
        "data_vencimento_mensalidade": getattr(usuario, 'subscription_due_date', None),
        "senha_temporaria": getattr(usuario, 'has_temp_password', False),
        "primeiro_login": getattr(usuario, 'is_first_login', False)
    }

# rota para logout seguro
@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme), session: Session = Depends(pegar_sessao)):
    """
    Logout seguro - adiciona token à blacklist
    O token será invalidado e não poderá mais ser usado
    """
    try:
        # Decodificar token para obter data de expiração
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        if exp_timestamp is None:
            raise HTTPException(status_code=401, detail="Token sem data de expiração")
        expiracao = datetime.fromtimestamp(exp_timestamp, timezone.utc)

        # Adicionar token à blacklist
        from ..models import TokenBlacklist
        blacklist_entry = TokenBlacklist(
            token=token,
            expiracao=expiracao
        )
        session.add(blacklist_entry)
        session.commit()

        return {"message": "Logout realizado com sucesso"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao fazer logout: {str(e)}")

# Função para gerar senha temporária segura
def gerar_senha_temporaria():
    """
    Gera uma senha temporária segura com 12 caracteres.
    Inclui letras maiúsculas, minúsculas, números e símbolos.
    """
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    senha = ''.join(secrets.choice(caracteres) for _ in range(12))
    return senha

# rota para trocar senha
@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordSchema,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    """
    Troca a senha do usuário logado.
    Verifica a senha atual e atualiza para a nova.
    Remove flags de senha temporária e primeiro login.
    """
    try:
        logger.info(f"Usuário {usuario.id} solicitando troca de senha")

        # Verificar senha atual
        if not bcrypt_context.verify(password_data.senha_atual, usuario.password):
            raise HTTPException(status_code=400, detail="Senha atual incorreta")

        # Validar nova senha (mínimo 6 caracteres)
        if len(password_data.nova_senha) < 6:
            raise HTTPException(status_code=400, detail="Nova senha deve ter pelo menos 6 caracteres")

        # Criptografar nova senha
        nova_senha_hash = bcrypt_context.hash(password_data.nova_senha)

        # Atualizar senha e flags
        usuario.password = nova_senha_hash
        usuario.has_temp_password = False
        usuario.is_first_login = False

        session.commit()

        # Registrar log de auditoria
        from ..models import AuditLog
        log_entry = AuditLog(
            acao="troca_senha",
            usuario_id=usuario.id,
            salon_id=usuario.id,
            detalhes="Senha alterada com sucesso"
        )
        session.add(log_entry)
        session.commit()

        logger.info(f"Senha alterada com sucesso para usuário {usuario.id}")

        return {
            "success": True,
            "message": "Senha alterada com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao trocar senha: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao trocar senha")

# rota para admin criar dono de salão
@router.post("/admin/create-owner")
async def admin_create_owner(
    owner_data: dict,
    admin_user: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    """
    Endpoint exclusivo para administradores criarem donos de salão.
    Apenas usuários com admin=True podem usar esta rota.
    Gera senha temporária automaticamente e envia notificação.
    """
    try:
        # Verificar se o usuário é admin
        if not admin_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Acesso negado. Apenas administradores podem criar donos de salão."
            )

        # Validar dados obrigatórios
        nome = owner_data.get('nome', '').strip()
        email = owner_data.get('email', '').strip()

        if not nome:
            raise HTTPException(status_code=400, detail="Nome do dono é obrigatório")

        if not email:
            raise HTTPException(status_code=400, detail="Email do dono é obrigatório")

        # Verificar se email já existe
        usuario_existente = session.query(Usuario).filter(Usuario.email == email).first()
        if usuario_existente:
            raise HTTPException(status_code=400, detail="Este email já está cadastrado no sistema")

        # Gerar senha temporária segura
        senha_temporaria = gerar_senha_temporaria()
        senha_hash = bcrypt_context.hash(senha_temporaria)

        logger.info(f"Criando dono: {nome} ({email})")

        # Criar novo usuário dono
        novo_dono = Usuario(
            name=nome,
            email=email,
            password=senha_hash,
            is_active=True,
            is_admin=False,  # Donos não são admins
            subscription_paid=False,  # Começa sem mensalidade paga
            has_temp_password=True,  # Força troca de senha no primeiro login
            is_first_login=True,  # Primeiro login
            temp_password=senha_temporaria,  # Armazenar senha temporária para logs
            created_by=admin_user.id  # Registrar quem criou
        )

        session.add(novo_dono)
        session.commit()
        session.refresh(novo_dono)

        # Registrar log de auditoria
        log_entry = AuditLog(
            acao="criacao_dono",
            usuario_id=admin_user.id,
            salon_id=novo_dono.id,
            detalhes=f"Dono criado por admin {admin_user.id}: {nome} ({email})"
        )
        session.add(log_entry)
        session.commit()

        # Simular envio de email/notificação
        logger.info(f"Notificação simulada enviada para {email}")
        logger.info(f"Login: {email}")
        logger.info(f"Senha temporária: {senha_temporaria}")
        logger.info(f"URL: http://localhost:3000/login.html")

        # Em produção, aqui seria integrado com um serviço de email real
        # send_email(email, "Bem-vindo ao Aluvi", f"Login: {email}\nSenha: {senha_temporaria}")

        logger.info(f"Dono criado com sucesso: ID={novo_dono.id}")

        return {
            "success": True,
            "owner_id": novo_dono.id,
            "owner_name": nome,
            "owner_email": email,
            "temp_password": senha_temporaria,
            "login_url": "http://localhost:3000/login.html",
            "message": f"Dono '{nome}' criado com sucesso. Use as credenciais abaixo para o primeiro acesso:",
            "credentials": {
                "email": email,
                "password": senha_temporaria
            },
            "notification_sent": True
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao criar dono: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar dono de salão")

# rota para atualizar perfil do usuário
@router.put("/update-profile")
async def update_profile(
    profile_data: dict,
    usuario: Usuario = Depends(verificar_token),
    session: Session = Depends(pegar_sessao)
):
    """
    Atualiza informações do perfil do usuário logado.
    Permite atualizar nome, email, telefone e experiência.
    """
    try:
        logger.info(f"Usuário {usuario.id} atualizando perfil")

        # Campos permitidos para atualização
        campos_permitidos = ['name', 'email', 'telefone', 'experiencia']

        # Aplicar apenas campos permitidos
        atualizacoes = {}
        for campo in campos_permitidos:
            if campo in profile_data:
                valor = profile_data[campo].strip() if isinstance(profile_data[campo], str) else profile_data[campo]
                if campo == 'name':
                    atualizacoes['name'] = valor
                elif campo == 'email':
                    # Verificar se email já existe (exceto o próprio usuário)
                    if valor and valor != usuario.email:
                        usuario_existente = session.query(Usuario).filter(
                            Usuario.email == valor,
                            Usuario.id != usuario.id
                        ).first()
                        if usuario_existente:
                            raise HTTPException(status_code=400, detail="Este email já está sendo usado por outro usuário")
                    atualizacoes['email'] = valor
                elif campo == 'telefone':
                    atualizacoes['telefone'] = valor
                elif campo == 'experiencia':
                    atualizacoes['experiencia'] = valor

        # Validar dados obrigatórios
        if 'name' in atualizacoes and not atualizacoes['name']:
            raise HTTPException(status_code=400, detail="Nome é obrigatório")

        # Aplicar atualizações
        for campo, valor in atualizacoes.items():
            setattr(usuario, campo, valor)

        session.commit()

        # Registrar log de auditoria
        log_entry = AuditLog(
            acao="atualizacao_perfil",
            usuario_id=usuario.id,
            salon_id=usuario.id,
            detalhes=f"Perfil atualizado: {', '.join(atualizacoes.keys())}"
        )
        session.add(log_entry)
        session.commit()

        logger.info(f"Perfil atualizado com sucesso para usuário {usuario.id}")

        return {
            "success": True,
            "message": "Perfil atualizado com sucesso",
            "updated_fields": list(atualizacoes.keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao atualizar perfil: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar perfil")