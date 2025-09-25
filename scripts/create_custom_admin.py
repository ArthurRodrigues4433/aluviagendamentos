#!/usr/bin/env python3
"""
Script para criar um usuário administrador personalizado

Uso: python create_custom_admin.py "Nome Completo" "email@exemplo.com" "senha123"
"""

import sys
import os
# Adicionar o diretório raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.database import SessionLocal
from src.backend.models.user import User
from src.backend.config import bcrypt_context

def create_custom_admin(name, email, password):
    """Cria um usuário administrador personalizado"""

    # Validações básicas
    if not name or not name.strip():
        print("ERRO: Nome é obrigatório!")
        return False

    if not email or "@" not in email:
        print("ERRO: Email válido é obrigatório!")
        return False

    if len(password) < 6:
        print("ERRO: Senha deve ter pelo menos 6 caracteres!")
        return False

    session = SessionLocal()

    try:
        # Verificar se já existe um admin com este email
        existing_admin = session.query(User).filter(User.email == email).first()
        if existing_admin:
            print(f"ERRO: Já existe um usuário com o email {email}")
            return False

        # Criar admin
        admin_data = {
            "name": name.strip(),
            "email": email.strip(),
            "password": bcrypt_context.hash(password),
            "is_active": True,
            "is_admin": True,
            "subscription_paid": True,  # Admin sempre tem mensalidade paga
            "subscription_due_date": None,
            "has_temp_password": False,
            "is_first_login": False
        }

        admin = User(**admin_data)
        session.add(admin)
        session.commit()
        session.refresh(admin)

        print("\n" + "="*50)
        print("ADMINISTRADOR CRIADO COM SUCESSO!")
        print("="*50)
        print(f"   Nome: {admin.name}")
        print(f"   Email: {admin.email}")
        print(f"   Senha: {'*'*len(password)} (oculta)")
        print(f"   ID: {admin.id}")
        print(f"   Tipo: Administrador")
        print("="*50)
        print("\nAgora você pode fazer login no sistema!")
        return True

    except Exception as e:
        session.rollback()
        print(f"ERRO ao criar administrador: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python create_custom_admin.py 'Nome Completo' 'email@exemplo.com' 'senha123'")
        print("Exemplo: python create_custom_admin.py 'João Silva' 'joao@empresa.com' 'minhasenha123'")
        sys.exit(1)

    name = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]

    success = create_custom_admin(name, email, password)
    sys.exit(0 if success else 1)