#!/usr/bin/env python3
"""
Script para verificar las retenciones reales en la base de datos
y ver por qué no se están enviando en el procesamiento
"""

import sys
sys.path.append('.')

from database import SessionLocal
from models.deposit import Deposit, EstadoDeposito
from models.cheque_retencion import Retencion
from datetime import datetime
from sqlalchemy import func

def main():
    db = SessionLocal()
    
    print("🔍 ANÁLISIS DE RETENCIONES EN BASE DE DATOS")
    print("=" * 60)
    
    # 1. Ver todas las retenciones que existen
    all_retenciones = db.query(Retencion).all()
    print(f"\n📊 TOTAL RETENCIONES EN BD: {len(all_retenciones)}")
    
    if all_retenciones:
        print("\n🧾 RETENCIONES ENCONTRADAS:")
        for i, ret in enumerate(all_retenciones[:10], 1):  # Mostrar solo las primeras 10
            print(f"  {i}. ID: {ret.id} | Deposit ID: {ret.deposit_id} | Número: {ret.nro_retencion} | Importe: ${ret.importe}")
        
        if len(all_retenciones) > 10:
            print(f"  ... y {len(all_retenciones) - 10} más")
    
    # 2. Ver retenciones con sus depósitos y estados
    print(f"\n🏭 RETENCIONES POR ESTADO DE DEPÓSITO:")
    estados_count = db.query(
        Deposit.estado, 
        func.count(Retencion.id)
    ).join(
        Retencion, Deposit.deposit_id == Retencion.deposit_id
    ).group_by(Deposit.estado).all()
    
    for estado, count in estados_count:
        print(f"  📈 {estado.value}: {count} retenciones")
    
    # 3. Ver depósitos LISTOS y sus retenciones (lo que se está procesando)
    print(f"\n🎯 DEPÓSITOS CON ESTADO 'LISTO' Y SUS RETENCIONES:")
    depositos_listos = db.query(Deposit).filter(Deposit.estado == EstadoDeposito.LISTO).all()
    
    total_retenciones_listos = 0
    for dep in depositos_listos:
        retenciones_count = len(dep.retenciones)
        total_retenciones_listos += retenciones_count
        
        if retenciones_count > 0:
            print(f"  ✅ Deposit {dep.deposit_id}: {retenciones_count} retenciones")
            for ret in dep.retenciones:
                print(f"    - Número: {ret.nro_retencion}, Importe: ${ret.importe}, Concepto: {ret.concepto}")
    
    if total_retenciones_listos == 0:
        print("  ⚠️ PROBLEMA: No hay retenciones asociadas a depósitos LISTOS")
        print("     Esto explica por qué no se envían en el procesamiento!")
    
    # 4. Verificar si hay retenciones recientes que deberían estar en LISTO
    print(f"\n🕐 RETENCIONES MÁS RECIENTES (últimas 5):")
    retenciones_recientes = db.query(Retencion).order_by(Retencion.id.desc()).limit(5).all()
    
    for ret in retenciones_recientes:
        deposit = db.query(Deposit).filter(Deposit.deposit_id == ret.deposit_id).first()
        estado = deposit.estado.value if deposit else "NO_ENCONTRADO"
        print(f"  🧾 ID: {ret.id} | Deposit: {ret.deposit_id} | Estado Deposit: {estado}")
        print(f"     Número: {ret.nro_retencion} | Importe: ${ret.importe} | Concepto: {ret.concepto}")
    
    # 5. Sugerencia de solución
    print(f"\n💡 ANÁLISIS Y SUGERENCIA:")
    if total_retenciones_listos == 0:
        print("  🎯 PROBLEMA CONFIRMADO: Los depósitos LISTOS no tienen retenciones")
        print("  🔧 SOLUCIONES POSIBLES:")
        print("     1. Crear retenciones en depósitos que aún están LISTOS")
        print("     2. Cambiar algunos depósitos ENVIADOS de vuelta a LISTO temporalmente")
        print("     3. Modificar el servicio para buscar retenciones en depósitos ENVIADOS recientes")
    
    db.close()

if __name__ == "__main__":
    main()
