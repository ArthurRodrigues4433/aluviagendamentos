#!/usr/bin/env python3
"""
Script para atualizar agendamentos passados que não foram confirmados.
Marca como 'nao_compareceu' agendamentos que já passaram mais de 20 minutos do horário.
"""

import sqlite3
from datetime import datetime, timedelta

def update_past_appointments():
    """Atualiza agendamentos passados para status 'nao_compareceu'"""

    conn = sqlite3.connect('aluvi.db')
    cursor = conn.cursor()

    try:
        # Calcular o limite: 20 minutos atrás
        cutoff_time = (datetime.now() - timedelta(minutes=20)).strftime('%Y-%m-%d %H:%M:%S')

        print(f"Atualizando agendamentos anteriores a: {cutoff_time}")

        # Buscar agendamentos que precisam ser atualizados
        cursor.execute('''
            SELECT id, data_hora, cliente_id, servico_id
            FROM agendamentos
            WHERE status = 'agendado'
            AND data_hora < ?
        ''', (cutoff_time,))

        past_appointments = cursor.fetchall()

        if not past_appointments:
            print("Nenhum agendamento passado encontrado para atualizar.")
            return

        print(f"Encontrados {len(past_appointments)} agendamentos passados:")

        # Atualizar cada agendamento
        updated_count = 0
        for appointment in past_appointments:
            appointment_id, data_hora, cliente_id, servico_id = appointment

            # Atualizar status para 'nao_compareceu'
            cursor.execute('''
                UPDATE agendamentos
                SET status = 'nao_compareceu'
                WHERE id = ?
            ''', (appointment_id,))

            print(f"  [OK] Agendamento ID {appointment_id}: {data_hora} -> 'nao_compareceu'")
            updated_count += 1

        conn.commit()
        print(f"\n[SUCCESS] Atualizacao concluida! {updated_count} agendamentos marcados como 'nao compareceu'.")

        # Verificar resultado
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM agendamentos
            GROUP BY status
        ''')

        status_counts = cursor.fetchall()
        print("\n[STATS] Status dos agendamentos apos atualizacao:")
        for status, count in status_counts:
            print(f"  {status}: {count}")

    except Exception as e:
        print(f"[ERROR] Erro ao atualizar agendamentos: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Atualizando agendamentos passados para status 'nao_compareceu'...")
    update_past_appointments()