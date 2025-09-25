#!/usr/bin/env python3
"""
Script para verificar usuários administradores
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Usuario

def check_admin_users():
    """Verifica usuários administradores"""

    session = SessionLocal()

    try:
        # Buscar todos os usuários
        users = session.query(Usuario).all()

        print("Usuários no sistema:")
        print("-" * 80)

        for user in users:
            admin_status = "ADMIN" if user.admin else "DONO"
            active_status = "ATIVO" if user.ativo else "INATIVO"
            mensalidade = "PAGA" if getattr(user, 'mensalidade_pago', False) else "EM ATRASO"

            print(f"ID: {user.id}")
            print(f"Nome: {user.nome}")
            print(f"Email: {user.email}")
            print(f"Tipo: {admin_status}")
            print(f"Status: {active_status}")
            print(f"Mensalidade: {mensalidade}")
            print("-" * 80)

    except Exception as e:
        print(f"Erro ao verificar usuários: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_admin_users()