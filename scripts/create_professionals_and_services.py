#!/usr/bin/env python3
"""
Script para criar profissionais, serviços e associações para teste
"""

import sqlite3
import argparse

def create_professionals_and_services(salon_id=1):
    """Cria profissionais, serviços e associações para teste"""

    conn = sqlite3.connect('aluvi.db')
    cursor = conn.cursor()

    try:
        # Limpar dados existentes para teste
        cursor.execute('DELETE FROM servicos_profissionais')
        cursor.execute('DELETE FROM profissionais')
        cursor.execute('DELETE FROM servicos')
        print("Dados existentes removidos")

        # Criar profissionais para o salão especificado
        professionals = [
            ("João Silva", "joao@salao.com", "11999999991", "Cabelereiro", salon_id),
            ("Maria Santos", "maria@salao.com", "11999999992", "Manicure", salon_id),
            ("Pedro Oliveira", "pedro@salao.com", "11999999993", "Barbeiro", salon_id)
        ]

        professional_ids = []
        for prof in professionals:
            cursor.execute('''
                INSERT INTO profissionais (nome, email, telefone, especialidade, salon_id, ativo)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', prof)
            professional_ids.append(cursor.lastrowid)
            print(f"Profissional criado: {prof[0]} (ID: {cursor.lastrowid})")

        # Criar serviços
        services = [
            ("Corte de Cabelo Masculino", "Corte completo para homens", 35.0, 30, salon_id),
            ("Corte de Cabelo Feminino", "Corte completo para mulheres", 45.0, 45, salon_id),
            ("Manicure", "Tratamento completo das unhas", 25.0, 60, salon_id),
            ("Barba", "Aparar e modelar barba", 20.0, 20, salon_id),
            ("Coloração", "Coloração completa do cabelo", 80.0, 90, salon_id)
        ]

        service_ids = []
        for serv in services:
            cursor.execute('''
                INSERT INTO servicos (nome, descricao, preco, duracao_minutos, salon_id)
                VALUES (?, ?, ?, ?, ?)
            ''', serv)
            service_ids.append(cursor.lastrowid)
            print(f"Serviço criado: {serv[0]} (ID: {cursor.lastrowid})")

        # Criar associações
        associations = [
            (professional_ids[0], service_ids[0]),  # João -> Corte Masculino
            (professional_ids[0], service_ids[1]),  # João -> Corte Feminino
            (professional_ids[0], service_ids[4]),  # João -> Coloração
            (professional_ids[1], service_ids[1]),  # Maria -> Corte Feminino
            (professional_ids[1], service_ids[2]),  # Maria -> Manicure
            (professional_ids[1], service_ids[4]),  # Maria -> Coloração
            (professional_ids[2], service_ids[0]),  # Pedro -> Corte Masculino
            (professional_ids[2], service_ids[3]),  # Pedro -> Barba
        ]

        for prof_id, serv_id in associations:
            cursor.execute('''
                INSERT INTO servicos_profissionais (profissional_id, servico_id, salon_id)
                VALUES (?, ?, ?)
            ''', (prof_id, serv_id, salon_id))
            print(f"Associação criada: Profissional {prof_id} -> Serviço {serv_id}")

        conn.commit()
        print("\nDados criados com sucesso!")

        # Verificar resultados
        cursor.execute('SELECT COUNT(*) FROM profissionais')
        prof_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM servicos')
        serv_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM servicos_profissionais')
        assoc_count = cursor.fetchone()[0]

        print(f"Total profissionais: {prof_count}")
        print(f"Total serviços: {serv_count}")
        print(f"Total associações: {assoc_count}")

    except Exception as e:
        print(f"Erro: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Criar profissionais, serviços e associações para um salão')
    parser.add_argument('--salon-id', type=int, default=1, help='ID do salão (padrão: 1)')

    args = parser.parse_args()

    print(f"Criando profissionais, serviços e associações para o salão {args.salon_id}...")
    create_professionals_and_services(args.salon_id)