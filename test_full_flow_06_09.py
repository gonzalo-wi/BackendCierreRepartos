#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.deposits_service import get_all_deposits, save_deposits_to_db
from database import SessionLocal
from models.deposit import Deposit
from datetime import datetime as dt
from sqlalchemy import func
from sqlalchemy.types import Date

def test_full_flow_06_09():
    print("🔍 Simulando el flujo completo para 06/09/2025...")
    
    date = "2025-09-06"
    
    # 1. Obtener datos de la API de miniBank
    print("\n1️⃣ Obteniendo datos de miniBank...")
    try:
        fresh_data = get_all_deposits(date)
        print(f"✅ Datos obtenidos: {type(fresh_data)}")
        
        # Analizar estructura
        total_deposits = 0
        for machine_id, data in fresh_data.items():
            if "error" not in data:
                array_deposits = data.get("ArrayOfWSDepositsByDayDTO", {})
                deposits = array_deposits.get("WSDepositsByDayDTO", [])
                
                # Convertir a lista si es dict
                if isinstance(deposits, dict):
                    deposits = [deposits]
                
                print(f"   {machine_id}: {len(deposits)} depósitos")
                total_deposits += len(deposits)
        
        print(f"   Total depósitos encontrados: {total_deposits}")
        
        if total_deposits == 0:
            print("❌ No hay depósitos en las APIs de miniBank para esta fecha")
            return
            
    except Exception as e:
        print(f"❌ Error obteniendo datos de miniBank: {e}")
        return
    
    # 2. Guardar en base de datos
    print("\n2️⃣ Guardando en base de datos...")
    try:
        result = save_deposits_to_db(fresh_data)
        print(f"✅ Resultado del guardado: {result}")
    except Exception as e:
        print(f"❌ Error guardando en DB: {e}")
    
    # 3. Verificar en base de datos
    print("\n3️⃣ Verificando en base de datos...")
    try:
        db = SessionLocal()
        query_date = dt.strptime(date, "%Y-%m-%d").date()
        
        deposits = db.query(Deposit).filter(
            func.cast(Deposit.date_time, Date) == query_date
        ).all()
        
        print(f"✅ Depósitos en DB: {len(deposits)}")
        
        if len(deposits) > 0:
            # Mostrar algunos ejemplos
            for i, deposit in enumerate(deposits[:3]):
                print(f"   Depósito {i+1}: {deposit.deposit_id} - {deposit.identifier} - ${deposit.total_amount}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error consultando DB: {e}")
    
    print("\n🎯 Conclusión:")
    if total_deposits > 0:
        print("✅ HAY datos en miniBank para esta fecha")
        print("🔍 El problema puede estar en:")
        print("   - El formato de fecha al consultar la DB")
        print("   - La lógica de auto-sincronización")
        print("   - La respuesta del endpoint")
    else:
        print("❌ NO hay datos en miniBank para esta fecha")
        print("🔍 Esto explicaría por qué el endpoint devuelve arrays vacíos")

if __name__ == "__main__":
    test_full_flow_06_09()
