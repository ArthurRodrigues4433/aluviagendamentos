#!/usr/bin/env python3
"""
Script para verificar os agendamentos no banco de dados
"""

import sqlite3

def check_appointments():
    """Verifica os agendamentos no banco"""

    conn = sqlite3.connect('aluvi.db')
    cursor = conn.cursor()

    try:
        # Verificar todos os agendamentos
        cursor.execute('SELECT id, client_id, service_id, professional_id, salon_id, appointment_datetime, status, price FROM agendamentos')
        appointments = cursor.fetchall()

        print(f"Encontrados {len(appointments)} agendamentos:")
        for apt in appointments:
            print(f"ID: {apt[0]}, Cliente: {apt[1]}, Status: {apt[6]}, Data: {apt[5]}")

        # Verificar apenas do salon_id=1
        cursor.execute('SELECT id, client_id, service_id, professional_id, salon_id, appointment_datetime, status, price FROM agendamentos WHERE salon_id = 1')
        salon_appointments = cursor.fetchall()

        print(f"\nAgendamentos do salão 1 ({len(salon_appointments)}):")
        for apt in salon_appointments:
            print(f"ID: {apt[0]}, Cliente: {apt[1]}, Salon: {apt[4]}, Status: {apt[6]}, Data: {apt[5]}")

        # Verificar clientes
        cursor.execute('SELECT id, nome, salon_id FROM clientes')
        clients = cursor.fetchall()

        print(f"\nClientes ({len(clients)}):")
        for client in clients:
            print(f"ID: {client[0]}, Nome: {client[1]}, Salon: {client[2]}")

        # Verificar se há agendamentos com client_id NULL
        cursor.execute('SELECT id, client_id FROM agendamentos WHERE client_id IS NULL')
        null_clients = cursor.fetchall()

        print(f"\nAgendamentos com client_id NULL ({len(null_clients)}):")
        for apt in null_clients:
            print(f"ID: {apt[0]}, Cliente: {apt[1]}")

        # Verificar JOIN simulado
        cursor.execute('''
            SELECT a.id, a.client_id, c.id as cliente_existe
            FROM agendamentos a
            LEFT JOIN clientes c ON a.client_id = c.id
            WHERE a.salon_id = 1 AND c.id IS NOT NULL
        ''')
        joined = cursor.fetchall()

        print(f"\nJOIN simulado (salon_id=1, cliente existe) ({len(joined)}):")
        for apt in joined:
            print(f"ID: {apt[0]}, Cliente: {apt[1]}, Cliente existe: {apt[2]}")

        # Verificar serviços
        cursor.execute('SELECT id, nome, salon_id FROM servicos')
        services = cursor.fetchall()

        print(f"\nServiços ({len(services)}):")
        for svc in services:
            print(f"ID: {svc[0]}, Nome: {svc[1]}, Salon: {svc[2]}")

        # Verificar profissionais
        cursor.execute('SELECT id, nome, salon_id FROM profissionais')
        professionals = cursor.fetchall()

        print(f"\nProfissionais ({len(professionals)}):")
        for prof in professionals:
            print(f"ID: {prof[0]}, Nome: {prof[1]}, Salon: {prof[2]}")

        # Verificar JOIN completo
        cursor.execute('''
            SELECT a.id, a.service_id, s.id as servico_existe, a.professional_id, p.id as prof_existe
            FROM agendamentos a
            LEFT JOIN servicos s ON a.service_id = s.id
            LEFT JOIN profissionais p ON a.professional_id = p.id
            WHERE a.salon_id = 1
        ''')
        full_join = cursor.fetchall()

        print(f"\nJOIN completo ({len(full_join)}):")
        for apt in full_join:
            print(f"ID: {apt[0]}, Servico: {apt[1]}->{apt[2]}, Prof: {apt[3]}->{apt[4]}")

    except Exception as e:
        print(f"Erro ao verificar agendamentos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_appointments()