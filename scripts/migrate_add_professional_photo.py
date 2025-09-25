#!/usr/bin/env python3
"""
Migração para adicionar campo foto à tabela profissionais
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.database import engine
from sqlalchemy import text

def migrate_add_professional_photo():
    """Adiciona o campo foto à tabela profissionais"""

    try:
        print("Iniciando migracao: adicionar campo foto a tabela profissionais...")

        # Adicionar coluna foto
        with engine.connect() as conn:
            # Verificar se a coluna já existe
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM pragma_table_info('profissionais')
                WHERE name = 'foto'
            """))
            row = result.fetchone()
            exists = row[0] > 0 if row else False

            if exists:
                print("AVISO: Coluna 'foto' ja existe na tabela profissionais")
                return True

            # Adicionar coluna foto
            conn.execute(text("""
                ALTER TABLE profissionais
                ADD COLUMN foto VARCHAR(500)
            """))

            conn.commit()

        print("SUCESSO: Migracao concluida: campo foto adicionado a tabela profissionais")
        return True

    except Exception as e:
        print(f"ERRO na migracao: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_add_professional_photo()
    sys.exit(0 if success else 1)