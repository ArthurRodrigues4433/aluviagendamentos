#!/usr/bin/env python3
import sys
sys.path.append('src')
from backend.database import get_db
from backend import models

def debug_query():
    db = next(get_db())
    try:
        # Ver todos os agendamentos
        all_appointments = db.query(models.Agendamento).all()
        print(f"Total de agendamentos no banco: {len(all_appointments)}")

        # Ver agendamentos com professional_id=2
        prof_appointments = db.query(models.Agendamento).filter(models.Agendamento.professional_id == 2).all()
        print(f"Agendamentos com professional_id=2: {len(prof_appointments)}")
        for apt in prof_appointments:
            print(f"  ID={apt.id}, professional_id={apt.professional_id}, datetime={apt.appointment_datetime}, status={apt.status}")

        # Ver agendamentos na data específica
        from datetime import datetime
        target_datetime = datetime(2025, 9, 25, 11, 0, 0)
        date_appointments = db.query(models.Agendamento).filter(
            models.Agendamento.professional_id == 2,
            models.Agendamento.appointment_datetime == target_datetime
        ).all()
        print(f"Agendamentos com professional_id=2 e datetime={target_datetime}: {len(date_appointments)}")
        for apt in date_appointments:
            print(f"  ID={apt.id}, professional_id={apt.professional_id}, datetime={apt.appointment_datetime}, status={apt.status}")

    finally:
        db.close()

if __name__ == "__main__":
    debug_query()