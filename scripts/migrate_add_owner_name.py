#!/usr/bin/env python3
"""
Migração incremental para adicionar campo nome_dono à tabela usuarios
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_owner_name():
    """Adiciona coluna nome_dono à tabela usuarios sem perder dados"""

    db_path = "aluvi.db"

    if not os.path.exists(db_path):
        print(f"[ERROR] Banco de dados {db_path} não encontrado!")
        return False

    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("[MIGRATE] Verificando estrutura da tabela usuarios...")

        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'nome_dono' in column_names:
            print("[INFO] Coluna nome_dono já existe!")
            conn.close()
            return True

        print("[MIGRATE] Adicionando coluna nome_dono...")

        # Adicionar coluna nome_dono
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nome_dono VARCHAR(255)")

        # Confirmar que foi adicionada
        cursor.execute("PRAGMA table_info(usuarios)")
        columns_after = cursor.fetchall()
        column_names_after = [col[1] for col in columns_after]

        if 'nome_dono' in column_names_after:
            print("[SUCCESS] Coluna nome_dono adicionada com sucesso!")
            conn.commit()
            conn.close()
            return True
        else:
            print("[ERROR] Falha ao adicionar coluna nome_dono!")
            conn.close()
            return False

    except Exception as e:
        print(f"[ERROR] Erro durante migração: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("=== MIGRAÇÃO: Adicionar nome_dono ===")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    success = migrate_add_owner_name()

    if success:
        print("[SUCCESS] Migração concluída com sucesso!")
        print("[INFO] Reinicie o servidor para aplicar as mudanças.")
    else:
        print("[ERROR] Migração falhou!")
        exit(1)