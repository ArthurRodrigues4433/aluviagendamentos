# Dependências e utilitários da aplicação
# Funções auxiliares para autenticação, validação e controle de acesso
from .database import SessionLocal
from .config import SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session  # type: ignore
from fastapi import Depends, HTTPException  # type: ignore
from .models import User
from jose import jwt, JWTError  # type: ignore
from fastapi.security import OAuth2PasswordBearer  # type: ignore

# Provedor OAuth2 utilizado para extrair o token do header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login-form")

def pegar_sessao():
    """Fornece uma sessão de banco de dados para as rotas"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def verificar_token(token: str = Depends(oauth2_scheme), session: Session = Depends(pegar_sessao)):  # type: ignore
    """
    Verifica e decodifica token JWT, retornando o usuário autenticado.
    Suporte para roles: "dono" (donos de salão) e "cliente" (clientes).
    """
    from .core.logging import get_logger
    logger = get_logger("auth")

    try:
        logger.debug(f"Token recebido: {token[:10]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        usuario_id = int(payload.get("sub"))  # type: ignore
        role = payload.get("role", "dono")  # Default para donos existentes
        logger.debug(f"Payload decodificado: sub={usuario_id}, role={role}")
    except JWTError as e:
        logger.warning(f"Erro JWT na validação do token: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido ou expirado!")
    except Exception as e:
        logger.error(f"Erro inesperado na decodificação do token: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Erro na validação do token!")

    # Verificar se token está na blacklist
    from .models import TokenBlacklist
    blacklisted = session.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
    if blacklisted:
        logger.warning(f"Token revogado na blacklist: {token[:10]}...")
        raise HTTPException(status_code=401, detail="Token revogado - faça login novamente!")

    # Buscar usuário baseado no role - com fallback inteligente
    usuario = None

    if role == "cliente":
        # Primeiro tentar buscar como cliente
        from .models import Client
        logger.debug(f"Buscando cliente ID={usuario_id}")
        usuario = session.query(Client).filter(Client.id == usuario_id).first()
        logger.debug(f"Cliente encontrado: {usuario is not None}")

        # Se não encontrou como cliente, tentar como dono (fallback)
        if not usuario:
            logger.debug("Cliente não encontrado, tentando como dono...")
            usuario = session.query(User).filter(User.id == usuario_id).first()  # type: ignore
            if usuario:
                logger.debug("Encontrado como dono, ajustando role")
                role = "dono"  # Ajustar role se encontrado na tabela errada
    else:
        # Primeiro tentar buscar como dono
        logger.debug(f"Buscando usuário (dono) ID={usuario_id}")
        usuario = session.query(User).filter(User.id == usuario_id).first()  # type: ignore
        logger.debug(f"Usuário encontrado: {usuario is not None}")

        # Se não encontrou como dono, tentar como cliente (fallback)
        if not usuario:
            logger.debug("Dono não encontrado, tentando como cliente...")
            from .models import Client
            usuario = session.query(Client).filter(Client.id == usuario_id).first()
            if usuario:
                logger.debug("Encontrado como cliente, ajustando role")
                role = "cliente"  # Ajustar role se encontrado na tabela errada

    if not usuario:
        logger.warning(f"Usuário não encontrado para ID={usuario_id} em nenhuma tabela")
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou token inválido!")

    # Adicionar role ao objeto para uso posterior (como atributo dinâmico)
    usuario._auth_role = role  # Usar atributo privado para armazenar role
    logger.debug(f"Autenticação bem-sucedida: ID={usuario.id}, role={role}")
    return usuario

def verificar_admin(usuario: User = Depends(verificar_token)):
    """
    Verifica se o usuário autenticado é administrador.
    Deve ser usado como dependência em rotas que requerem privilégios de admin.
    """
    from .core.logging import get_logger
    logger = get_logger("auth")

    logger.debug(f"Verificando privilégios de admin para usuário {usuario.id}")

    if not hasattr(usuario, 'is_admin') or not usuario.is_admin: #type: ignore
        logger.warning(f"Acesso negado - usuário {usuario.id} não possui privilégios de administrador")
        raise HTTPException(status_code=403, detail="Acesso negado - privilégios de administrador necessários")

    logger.debug(f"Acesso autorizado para administrador: {usuario.id}")
    return usuario