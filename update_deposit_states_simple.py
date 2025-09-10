#!/usr/bin/env python3
"""
Script simple para actualizar los estados de todos los depósitos según la nueva lógica:
- PENDIENTE: si tiene cheques o retenciones
- LISTO: si no tiene cheques ni retenciones
"""

import sys
import os

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.deposit import Deposit
from sqlalchemy import text

def update_deposit_states():
    """Actualizar estados de todos los depósitos"""
    db = SessionLocal()
    try:
        print("🔄 Iniciando actualización de estados de depósitos...")
        
        # Obtener todos los depósitos
        deposits = db.query(Deposit).all()
        print(f"📊 Encontrados {len(deposits)} depósitos para procesar")
        
        updated_count = 0
        
        for deposit in deposits:
            # Contar cheques y retenciones
            cheques_count = len(deposit.cheques) if deposit.cheques else 0
            retenciones_count = len(deposit.retenciones) if deposit.retenciones else 0
            
            # Determinar nuevo estado
            if cheques_count > 0 or retenciones_count > 0:
                nuevo_estado = "PENDIENTE"
            else:
                nuevo_estado = "LISTO"
            
            # Actualizar solo si cambió
            if deposit.estado.value != nuevo_estado:
                print(f"📝 Actualizando depósito {deposit.deposit_id}: {deposit.estado.value} -> {nuevo_estado} (cheques: {cheques_count}, retenciones: {retenciones_count})")
                deposit.estado = nuevo_estado
                updated_count += 1
        
        # Confirmar cambios
        if updated_count > 0:
            db.commit()
            print(f"✅ Actualización completada. {updated_count} depósitos actualizados.")
        else:
            print("ℹ️ No se encontraron depósitos que necesiten actualización.")
            
    except Exception as e:
        print(f"❌ Error durante la actualización: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_deposit_states()
