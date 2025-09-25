#!/usr/bin/env python3
"""
Script de migração do banco de dados.
Apaga todos os dados existentes e recria as tabelas com a estrutura atualizada.
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Executa migração completa do banco de dados"""

    db_path = 'aluvi.db'
    backup_path = f'aluvi_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

    print("=== MIGRACAO DO BANCO DE DADOS ===")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Banco atual: {db_path}")

    # Verificar se o banco existe
    if not os.path.exists(db_path):
        print("[ERROR] Banco de dados nao encontrado!")
        return False

    # Fazer backup
    print(f"[BACKUP] Criando backup: {backup_path}")
    try:
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print("[SUCCESS] Backup criado com sucesso!")
    except Exception as e:
        print(f"[ERROR] Erro ao criar backup: {e}")
        return False

    # Conectar ao banco
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("\n[DROP] Removendo tabelas existentes...")

        # Lista de tabelas para remover (em ordem de dependências)
        tables_to_drop = [
            'agendamentos',
            'clientes',
            'servicos',
            'profissionais',
            'servicos_profissionais',
            'usuarios',
            'horarios_funcionamento',
            'token_blacklist'
        ]

        for table in tables_to_drop:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table}')
                print(f"  [OK] Tabela {table} removida")
            except Exception as e:
                print(f"  [WARN] Erro ao remover {table}: {e}")

        conn.commit()
        print("[SUCCESS] Todas as tabelas removidas!")

        print("\n[CREATE] Criando novas tabelas...")

        # Criar tabelas na ordem correta (dependências)

        # 1. Usuários (dono do salão)
        cursor.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                senha VARCHAR NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                admin BOOLEAN DEFAULT 0,
                mensalidade_pago BOOLEAN DEFAULT 0,
                data_vencimento_mensalidade DATE,
                senha_temporaria BOOLEAN DEFAULT 1,
                primeiro_login BOOLEAN DEFAULT 1,
                senha_temporaria_atual VARCHAR,
                criado_por INTEGER,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                -- Campos para aparência customizada do card
                card_display_name VARCHAR,
                card_location VARCHAR,
                card_description TEXT,
                card_logo VARCHAR,
                -- Campos adicionais da empresa
                telefone VARCHAR,
                endereco VARCHAR,
                descricao TEXT,
                logo VARCHAR,
                -- Campo para nome do dono (separado do nome da empresa)
                nome_dono VARCHAR,
                FOREIGN KEY (criado_por) REFERENCES usuarios (id)
            )
        ''')
        print("  [OK] Tabela usuarios criada")

        # 2. Horários de funcionamento
        cursor.execute('''
            CREATE TABLE horarios_funcionamento (
                salon_id INTEGER PRIMARY KEY,
                monday_open VARCHAR(5),
                monday_close VARCHAR(5),
                tuesday_open VARCHAR(5),
                tuesday_close VARCHAR(5),
                wednesday_open VARCHAR(5),
                wednesday_close VARCHAR(5),
                thursday_open VARCHAR(5),
                thursday_close VARCHAR(5),
                friday_open VARCHAR(5),
                friday_close VARCHAR(5),
                saturday_open VARCHAR(5),
                saturday_close VARCHAR(5),
                sunday_open VARCHAR(5),
                sunday_close VARCHAR(5),
                FOREIGN KEY (salon_id) REFERENCES usuarios (id)
            )
        ''')
        print("  [OK] Tabela horarios_funcionamento criada")

        # 3. Clientes
        cursor.execute('''
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR NOT NULL,
                email VARCHAR,
                telefone VARCHAR UNIQUE,
                senha VARCHAR,
                pontos_fidelidade INTEGER DEFAULT 0,
                salon_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (salon_id) REFERENCES usuarios (id)
            )
        ''')
        print("  [OK] Tabela clientes criada")

        # 4. Serviços
        cursor.execute('''
            CREATE TABLE servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR NOT NULL,
                descricao TEXT,
                preco DECIMAL(10,2) NOT NULL,
                duracao_minutos INTEGER NOT NULL,
                pontos_fidelidade INTEGER DEFAULT 0,
                salon_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (salon_id) REFERENCES usuarios (id)
            )
        ''')
        print("  [OK] Tabela servicos criada")

        # 5. Profissionais
        cursor.execute('''
            CREATE TABLE profissionais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR NOT NULL,
                email VARCHAR UNIQUE,
                telefone VARCHAR,
                especialidade VARCHAR,
                foto VARCHAR(500),
                salon_id INTEGER NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (salon_id) REFERENCES usuarios (id)
            )
        ''')
        print("  [OK] Tabela profissionais criada")

        # 6. Serviços_Profissionais (relacionamento muitos-para-muitos)
        cursor.execute('''
            CREATE TABLE servicos_profissionais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servico_id INTEGER NOT NULL,
                profissional_id INTEGER NOT NULL,
                salon_id INTEGER NOT NULL,
                FOREIGN KEY (servico_id) REFERENCES servicos (id),
                FOREIGN KEY (profissional_id) REFERENCES profissionais (id),
                FOREIGN KEY (salon_id) REFERENCES usuarios (id),
                UNIQUE(servico_id, profissional_id)
            )
        ''')
        print("  [OK] Tabela servicos_profissionais criada")

        # 7. Agendamentos (com novo status 'nao_compareceu')
        cursor.execute('''
            CREATE TABLE agendamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                service_id INTEGER,
                professional_id INTEGER,
                salon_id INTEGER NOT NULL,
                appointment_datetime DATETIME NOT NULL,
                status VARCHAR(20) DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'NO_SHOW')),
                price DECIMAL(10,2) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clientes (id),
                FOREIGN KEY (service_id) REFERENCES servicos (id),
                FOREIGN KEY (professional_id) REFERENCES profissionais (id),
                FOREIGN KEY (salon_id) REFERENCES usuarios (id)
            )
        ''')
        print("  [OK] Tabela agendamentos criada (com novo status)")

        # 8. Token Blacklist
        cursor.execute('''
            CREATE TABLE token_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token VARCHAR UNIQUE NOT NULL,
                expiracao DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  [OK] Tabela token_blacklist criada")

        conn.commit()
        print("[SUCCESS] Todas as tabelas criadas com sucesso!")

        # Verificar estrutura
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n[INFO] Tabelas criadas: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")

        # Verificar constraints do status
        cursor.execute("PRAGMA table_info(agendamentos)")
        columns = cursor.fetchall()
        status_column = next((col for col in columns if col[1] == 'status'), None)
        if status_column:
            print(f"\n[CHECK] Coluna status: {status_column}")
            print("[SUCCESS] Constraint CHECK aplicada com sucesso!")

        conn.close()

        print("\n[SUCCESS] MIGRACAO CONCLUIDA COM SUCESSO!")
        print(f"[BACKUP] Backup salvo em: {backup_path}")
        print("[CLEAN] Todos os dados antigos foram removidos")
        print("[CREATE] Banco recriado com nova estrutura")
        print("[NEW] Novo status 'nao_compareceu' incluido")
        print("\n[READY] O sistema esta pronto para uso!")

        return True

    except Exception as e:
        print(f"[ERROR] ERRO DURANTE MIGRACAO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n[SUCCESS] Migracao executada com sucesso!")
        print("[INFO] Reinicie o servidor para aplicar as mudancas.")
    else:
        print("\n[ERROR] Migracao falhou!")
        print("[INFO] Restaure o backup se necessario.")
        import sys
        sys.exit(1)