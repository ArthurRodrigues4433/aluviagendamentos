#!/usr/bin/env python3
"""
Script para adicionar campos de controle de mensalidade e acesso à tabela usuarios
"""

import sqlite3

def add_salon_fields():
    """Adiciona as novas colunas à tabela usuarios"""

    conn = sqlite3.connect('aluvi.db')
    cursor = conn.cursor()

    try:
        # Verificar colunas existentes
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print("Colunas atuais da tabela usuarios:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        # Adicionar coluna mensalidade_pago se não existir
        if 'mensalidade_pago' not in column_names:
            print("\nAdicionando coluna mensalidade_pago...")
            cursor.execute('''
                ALTER TABLE usuarios
                ADD COLUMN mensalidade_pago BOOLEAN DEFAULT 0
            ''')

        # Adicionar coluna data_vencimento_mensalidade se não existir
        if 'data_vencimento_mensalidade' not in column_names:
            print("Adicionando coluna data_vencimento_mensalidade...")
            cursor.execute('''
                ALTER TABLE usuarios
                ADD COLUMN data_vencimento_mensalidade DATE
            ''')

        # Adicionar coluna senha_temporaria se não existir
        if 'senha_temporaria' not in column_names:
            print("Adicionando coluna senha_temporaria...")
            cursor.execute('''
                ALTER TABLE usuarios
                ADD COLUMN senha_temporaria BOOLEAN DEFAULT 1
            ''')

        # Adicionar coluna primeiro_login se não existir
        if 'primeiro_login' not in column_names:
            print("Adicionando coluna primeiro_login...")
            cursor.execute('''
                ALTER TABLE usuarios
                ADD COLUMN primeiro_login BOOLEAN DEFAULT 1
            ''')

        conn.commit()
        print("\nMigração concluída com sucesso!")

        # Verificar colunas após migração
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = cursor.fetchall()
        print("\nColunas após migração:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

    except Exception as e:
        print(f"Erro ao executar migração: {e}")
        conn.rollback()
    finally:
        conn.close()

def create_audit_logs_table():
    """Cria a tabela audit_logs se não existir ou recria se tiver estrutura incorreta"""

    conn = sqlite3.connect('aluvi.db')
    cursor = conn.cursor()

    try:
        # Verificar se a tabela já existe e tem a estrutura correta
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
        if cursor.fetchone():
            # Verificar se tem a coluna endereco_ip
            cursor.execute("PRAGMA table_info(audit_logs)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if 'endereco_ip' in column_names and 'created_at' in column_names and 'updated_at' in column_names:
                print("Tabela audit_logs já existe com estrutura correta")
                return

            print("Tabela audit_logs tem estrutura incorreta, recriando...")
            cursor.execute("DROP TABLE audit_logs")

        print("Criando tabela audit_logs...")

        cursor.execute('''
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acao TEXT NOT NULL,
                usuario_id INTEGER,
                salon_id INTEGER,
                detalhes TEXT,
                endereco_ip TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                FOREIGN KEY (salon_id) REFERENCES usuarios (id)
            )
        ''')

        conn.commit()
        print("Tabela audit_logs criada com sucesso!")

    except Exception as e:
        print(f"Erro ao criar tabela audit_logs: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Executando migração para adicionar campos de salão...")
    add_salon_fields()
    create_audit_logs_table()
    print("Todas as migrações concluídas!")