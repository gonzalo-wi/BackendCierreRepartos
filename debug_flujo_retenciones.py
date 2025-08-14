#!/usr/bin/env python3
"""
Debug: Verificar el flujo completo de retenciones desde creación hasta procesamiento
"""
import sys
sys.path.append('.')

from database import SessionLocal
from models.deposit import Deposit, EstadoDeposito
from models.cheque_retencion import Retencion
from sqlalchemy import func
from datetime import datetime

def verificar_flujo_retenciones():
    """Verificar el flujo completo de retenciones"""
    db = SessionLocal()
    
    print("🔍 VERIFICANDO FLUJO DE RETENCIONES")
    print("=" * 60)
    
    # 1. Verificar depósitos LISTOS con retenciones
    depositos_listos = db.query(Deposit).filter(Deposit.estado == EstadoDeposito.LISTO).all()
    
    print(f"📋 DEPÓSITOS CON ESTADO LISTO: {len(depositos_listos)}")
    
    for i, deposit in enumerate(depositos_listos[:10]):  # Solo primeros 10
        retenciones = db.query(Retencion).filter(Retencion.deposit_id == deposit.deposit_id).all()
        print(f"  {i+1}. Depósito {deposit.deposit_id} ({deposit.identifier}) - {len(retenciones)} retenciones")
        
        if retenciones:
            print(f"     🧾 Retenciones encontradas:")
            for r in retenciones:
                print(f"       - ID:{r.id} | Nro:{r.nro_retencion} | ${r.importe} | Fecha:{r.fecha}")
    
    # 2. Verificar si hay depósitos LISTOS creados recientemente con retenciones
    print(f"\n🔍 BUSCANDO DEPÓSITOS LISTOS CON RETENCIONES...")
    
    depositos_con_retenciones = db.query(Deposit).join(Retencion).filter(
        Deposit.estado == EstadoDeposito.LISTO
    ).distinct().all()
    
    print(f"📊 DEPÓSITOS LISTOS QUE TIENEN RETENCIONES: {len(depositos_con_retenciones)}")
    
    for deposit in depositos_con_retenciones:
        retenciones = deposit.retenciones  # Usando relación ORM
        total_importe = sum(float(r.importe) for r in retenciones)
        print(f"  ✅ {deposit.deposit_id} ({deposit.identifier}) - {len(retenciones)} retenciones - Total: ${total_importe}")
        
        for r in retenciones:
            print(f"       🧾 {r.nro_retencion}: ${r.importe} ({r.concepto}) - {r.fecha}")
    
    # 3. Verificar la última retención creada
    print(f"\n🔍 ÚLTIMAS RETENCIONES CREADAS:")
    ultimas_retenciones = db.query(Retencion).order_by(Retencion.id.desc()).limit(5).all()
    
    for r in ultimas_retenciones:
        deposit = db.query(Deposit).filter(Deposit.deposit_id == r.deposit_id).first()
        estado_deposito = deposit.estado.value if deposit else "NO_ENCONTRADO"
        print(f"  🧾 ID:{r.id} | Depósito:{r.deposit_id} (Estado:{estado_deposito}) | Nro:{r.nro_retencion} | ${r.importe}")
    
    # 4. Test de relación ORM
    print(f"\n🔍 TEST DE RELACIÓN ORM:")
    print("Verificando si deposit.retenciones funciona correctamente...")
    
    for deposit in depositos_listos[:3]:  # Solo primeros 3
        try:
            retenciones_orm = deposit.retenciones  # Usando relación ORM
            retenciones_query = db.query(Retencion).filter(Retencion.deposit_id == deposit.deposit_id).all()
            
            print(f"  Depósito {deposit.deposit_id}:")
            print(f"    - Via ORM: {len(retenciones_orm)} retenciones")
            print(f"    - Via Query: {len(retenciones_query)} retenciones")
            
            if len(retenciones_orm) != len(retenciones_query):
                print(f"    ❌ DISCREPANCIA EN RELACIÓN ORM!")
            else:
                print(f"    ✅ Relación ORM funciona correctamente")
                
        except Exception as e:
            print(f"    ❌ Error en relación ORM: {e}")
    
    db.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    verificar_flujo_retenciones()
