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
    try:
        print(f"[VERIFICAR_TOKEN] Token recebido: {token[:50]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        usuario_id = int(payload.get("sub"))  # type: ignore
        role = payload.get("role", "dono")  # Default para donos existentes
        print(f"[VERIFICAR_TOKEN] Payload decodificado: sub={usuario_id}, role={role}")
    except JWTError as e:
        print(f"[VERIFICAR_TOKEN] Erro JWT: {e}")
        raise HTTPException(status_code=401, detail="Token inválido ou expirado!")
    except Exception as e:
        print(f"[VERIFICAR_TOKEN] Erro inesperado na decodificação: {e}")
        raise HTTPException(status_code=401, detail="Erro na validação do token!")

    # Verificar se token está na blacklist
    from .models import TokenBlacklist
    blacklisted = session.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
    if blacklisted:
        print(f"[VERIFICAR_TOKEN] Token na blacklist")
        raise HTTPException(status_code=401, detail="Token revogado - faça login novamente!")

    # Buscar usuário baseado no role - com fallback inteligente
    usuario = None

    if role == "cliente":
        # Primeiro tentar buscar como cliente
        from .models import Client
        print(f"[VERIFICAR_TOKEN] Buscando cliente ID={usuario_id}")
        usuario = session.query(Client).filter(Client.id == usuario_id).first()
        print(f"[VERIFICAR_TOKEN] Cliente encontrado: {usuario is not None}")

        # Se não encontrou como cliente, tentar como dono (fallback)
        if not usuario:
            print(f"[VERIFICAR_TOKEN] Cliente não encontrado, tentando como dono...")
            usuario = session.query(User).filter(User.id == usuario_id).first()  # type: ignore
            if usuario:
                print(f"[VERIFICAR_TOKEN] Encontrado como dono, ajustando role")
                role = "dono"  # Ajustar role se encontrado na tabela errada
    else:
        # Primeiro tentar buscar como dono
        print(f"[VERIFICAR_TOKEN] Buscando usuário (dono) ID={usuario_id}")
        usuario = session.query(User).filter(User.id == usuario_id).first()  # type: ignore
        print(f"[VERIFICAR_TOKEN] Usuário encontrado: {usuario is not None}")

        # Se não encontrou como dono, tentar como cliente (fallback)
        if not usuario:
            print(f"[VERIFICAR_TOKEN] Dono não encontrado, tentando como cliente...")
            from .models import Client
            usuario = session.query(Client).filter(Client.id == usuario_id).first()
            if usuario:
                print(f"[VERIFICAR_TOKEN] Encontrado como cliente, ajustando role")
                role = "cliente"  # Ajustar role se encontrado na tabela errada

    if not usuario:
        print(f"[VERIFICAR_TOKEN] Usuário não encontrado para ID={usuario_id} em nenhuma tabela")
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou token inválido!")

    # Adicionar role ao objeto para uso posterior (como atributo dinâmico)
    usuario._auth_role = role  # Usar atributo privado para armazenar role
    print(f"[VERIFICAR_TOKEN] Retornando usuário: ID={usuario.id}, nome={getattr(usuario, 'nome', 'N/A')}, role={role}, type={type(usuario)}")
    return usuario

def verificar_admin(usuario: User = Depends(verificar_token)):
    """
    Verifica se o usuário autenticado é administrador.
    Deve ser usado como dependência em rotas que requerem privilégios de admin.
    """
    print(f"[VERIFICAR_ADMIN] Verificando admin para usuário {usuario.id}: hasattr(is_admin)={hasattr(usuario, 'is_admin')}, is_admin={getattr(usuario, 'is_admin', 'N/A')}")

    if not hasattr(usuario, 'is_admin') or not usuario.is_admin: #type: ignore
        print(f"[VERIFICAR_ADMIN] Acesso negado: usuário {usuario.id} não é admin")
        raise HTTPException(status_code=403, detail="Acesso negado - privilégios de administrador necessários")

    print(f"[VERIFICAR_ADMIN] Acesso autorizado para admin: {usuario.id}")
    return usuario