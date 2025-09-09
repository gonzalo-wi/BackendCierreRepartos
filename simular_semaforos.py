#!/usr/bin/env python3
"""
Script para simular depósitos con documentos pendientes para probar semáforos
"""

from database import SessionLocal
from models.deposit import Deposit, EstadoDeposito
from models.cheque_retencion import Cheque, Retencion
from datetime import datetime
import logging

def crear_deposito_prueba_semaforo():
    """
    Crea un depósito de prueba con documentos esperados pero sin cargar
    para verificar que los semáforos funcionen
    """
    db = SessionLocal()
    try:
        # Crear depósito con composición esperada pero sin docs
        deposit_prueba = Deposit(
            deposit_id="TEST_SEMAFORO_001",
            identifier="L-EJU-001",
            user_name="199, RTO 199",  # Este ID está en la API externa
            total_amount=50000,
            deposit_esperado=56000,  # Efectivo + Cheques + Retenciones
            efectivo_esperado=50000,  # Solo efectivo para el cierre
            composicion_esperado="ECR",  # Esperamos Efectivo + Cheques + Retenciones
            currency_code="ARS",
            deposit_type="CASH",
            date_time=datetime.now(),
            pos_name="Test POS",
            st_name="Test Station",
            estado=EstadoDeposito.LISTO
        )
        
        db.add(deposit_prueba)
        db.commit()
        db.refresh(deposit_prueba)
        
        print(f"✅ Depósito de prueba creado: {deposit_prueba.deposit_id}")
        print(f"   📊 Composición esperada: {deposit_prueba.composicion_esperado}")
        print(f"   💰 Monto esperado: ${deposit_prueba.deposit_esperado}")
        print(f"   💵 Efectivo esperado: ${deposit_prueba.efectivo_esperado}")
        print(f"   📄 Cheques cargados: 0")
        print(f"   🧾 Retenciones cargadas: 0")
        print(f"   🚨 Estado semáforo esperado: AMARILLO (docs pendientes)")
        
        return deposit_prueba.id
        
    except Exception as e:
        print(f"❌ Error creando depósito de prueba: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def agregar_documentos_prueba(deposit_db_id):
    """
    Agrega documentos al depósito de prueba para verificar que el semáforo cambie a verde
    """
    db = SessionLocal()
    try:
        # Buscar el depósito de prueba
        deposit = db.query(Deposit).filter(Deposit.deposit_id == "TEST_SEMAFORO_001").first()
        if not deposit:
            print("❌ No se encontró el depósito de prueba")
            return
            
        # Agregar un cheque de prueba usando el deposit_id string
        cheque = Cheque(
            deposit_id="TEST_SEMAFORO_001",  # Usar el deposit_id string, no el ID interno
            nrocta=1,
            concepto="CHE",
            banco=11,
            sucursal=1,
            localidad=1,
            nro_cheque="TEST001",
            nro_cuenta=1234567,
            titular="Juan Perez",
            fecha=datetime.now().strftime("%d/%m/%Y"),
            importe=3000.0
        )
        
        # Agregar una retención de prueba
        retencion = Retencion(
            deposit_id="TEST_SEMAFORO_001",  # Usar el deposit_id string, no el ID interno
            nrocta=1,
            concepto="RIB",
            nro_retencion=5001,
            fecha=datetime.now().strftime("%d/%m/%Y"),
            importe=3000.0
        )
        
        db.add(cheque)
        db.add(retencion)
        db.commit()
        
        print(f"✅ Documentos agregados al depósito TEST_SEMAFORO_001")
        print(f"   📄 Cheque: #{cheque.nro_cheque} - ${cheque.importe}")
        print(f"   🧾 Retención: #{retencion.nro_retencion} - ${retencion.importe}")
        print(f"   🟢 Estado semáforo esperado: VERDE (docs completos)")
        
    except Exception as e:
        print(f"❌ Error agregando documentos: {e}")
        db.rollback()
    finally:
        db.close()

def limpiar_deposito_prueba():
    """
    Elimina el depósito de prueba
    """
    db = SessionLocal()
    try:
        deposit = db.query(Deposit).filter(Deposit.deposit_id == "TEST_SEMAFORO_001").first()
        if deposit:
            # Eliminar documentos asociados
            for cheque in deposit.cheques:
                db.delete(cheque)
            for retencion in deposit.retenciones:
                db.delete(retencion)
            
            # Eliminar depósito
            db.delete(deposit)
            db.commit()
            print("🗑️ Depósito de prueba eliminado")
        else:
            print("⚠️ No se encontró depósito de prueba para eliminar")
            
    except Exception as e:
        print(f"❌ Error eliminando depósito de prueba: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 SIMULACIÓN DE SEMÁFOROS DE DOCUMENTOS")
    print("=" * 50)
    
    # 1. Crear depósito con docs pendientes
    print("\n1️⃣ Creando depósito con documentos pendientes...")
    deposit_id = crear_deposito_prueba_semaforo()
    
    if deposit_id:
        print(f"\n2️⃣ Prueba el semáforo AMARILLO visitando:")
        print(f"   http://localhost:8001/api/db/deposits/by-plant?date=2025-08-27")
        print(f"   Busca el depósito TEST_SEMAFORO_001")
        
        input("\n   Presiona ENTER después de verificar el semáforo amarillo...")
        
        # 2. Agregar documentos para cambiar a verde
        print("\n3️⃣ Agregando documentos para completar...")
        agregar_documentos_prueba(None)  # No necesitamos pasar el ID
        
        print(f"\n4️⃣ Prueba el semáforo VERDE refrescando la página")
        
        input("\n   Presiona ENTER después de verificar el semáforo verde...")
        
        # 3. Limpiar
        print("\n5️⃣ Limpiando depósito de prueba...")
        limpiar_deposito_prueba()
        
        print("\n✅ Simulación completada!")
        print("\n🎯 RESUMEN:")
        print("   • Semáforo AMARILLO: tiene_docs_esperados=true, docs_completos=false")
        print("   • Semáforo VERDE: tiene_docs_esperados=true, docs_completos=true")
        print("   • Semáforo GRIS: tiene_docs_esperados=false")
