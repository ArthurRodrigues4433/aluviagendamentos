#!/usr/bin/env python3
"""
Script para definir senha conhecida para o admin
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Usuario
from app.config import bcrypt_context

def set_admin_password():
    """Define senha conhecida para o admin"""

    session = SessionLocal()

    try:
        # Buscar admin
        admin = session.query(Usuario).filter(Usuario.admin == True).first()

        if not admin:
            print("❌ Nenhum usuário admin encontrado")
            return

        # Definir nova senha
        new_password = "admin123"
        hashed_password = bcrypt_context.hash(new_password)

        # Atualizar senha e garantir que seja admin ativo
        admin.senha = hashed_password
        admin.ativo = True
        admin.admin = True
        admin.mensalidade_pago = True  # Admin sempre tem mensalidade paga
        admin.senha_temporaria = False
        admin.primeiro_login = False

        session.commit()

        print("Senha do admin atualizada com sucesso!")
        print(f"   Email: {admin.email}")
        print(f"   Senha: {new_password}")
        print(f"   ID: {admin.id}")

    except Exception as e:
        session.rollback()
        print(f"Erro ao atualizar senha do admin: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("Definindo senha conhecida para o admin...")
    set_admin_password()
    print("Concluído!")