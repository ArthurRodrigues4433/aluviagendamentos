#!/usr/bin/env python3
"""
Script para adicionar a coluna pontos_fidelidade à tabela servicos
"""

import sqlite3

def add_points_column():
    """Adiciona a coluna pontos_fidelidade à tabela servicos"""

    conn = sqlite3.connect('aluvi.db')
    cursor = conn.cursor()

    try:
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(servicos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'pontos_fidelidade' not in column_names:
            print("Adicionando coluna pontos_fidelidade à tabela servicos...")

            # Adicionar a coluna com valor padrão 0
            cursor.execute('''
                ALTER TABLE servicos
                ADD COLUMN pontos_fidelidade INTEGER DEFAULT 0
            ''')

            conn.commit()
            print("Coluna pontos_fidelidade adicionada com sucesso!")
        else:
            print("Coluna pontos_fidelidade ja existe na tabela servicos")

        # Verificar se a coluna foi adicionada corretamente
        cursor.execute("PRAGMA table_info(servicos)")
        columns = cursor.fetchall()
        print("\nColunas da tabela servicos:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

    except Exception as e:
        print(f"Erro ao adicionar coluna: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Executando migracao para adicionar pontos de fidelidade...")
    add_points_column()
    print("Migracao concluida!")