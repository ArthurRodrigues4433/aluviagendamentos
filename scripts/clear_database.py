#!/usr/bin/env python3
"""
Script para limpar completamente o banco de dados
"""

import sqlite3

def clear_database():
    """Limpa todas as tabelas do banco de dados"""

    conn = sqlite3.connect('aluvi.db')
    cursor = conn.cursor()

    try:
        # Lista de todas as tabelas
        tables = [
            'agendamentos',
            'clientes',
            'servicos',
            'profissionais',
            'servicos_profissionais',
            'usuarios',
            'horarios_funcionamento',
            'token_blacklist'
        ]

        print("Limpando banco de dados...")

        # Desabilitar foreign keys temporariamente
        cursor.execute('PRAGMA foreign_keys = OFF;')

        # Limpar todas as tabelas
        for table in tables:
            try:
                cursor.execute(f'DELETE FROM {table};')
                print(f"Tabela {table} limpa")
            except Exception as e:
                print(f"Erro ao limpar tabela {table}: {e}")

        # Resetar auto-increment
        for table in tables:
            try:
                cursor.execute(f'DELETE FROM sqlite_sequence WHERE name="{table}";')
            except Exception as e:
                pass  # Ignorar erros de sequencia

        # Reabilitar foreign keys
        cursor.execute('PRAGMA foreign_keys = ON;')

        conn.commit()
        print("Banco de dados limpo com sucesso!")

        # Verificar se está vazio
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table};')
            count = cursor.fetchone()[0]
            print(f"Tabela {table}: {count} registros")

    except Exception as e:
        print(f"Erro ao limpar banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Iniciando limpeza do banco de dados...")
    clear_database()
    print("Limpeza concluida!")