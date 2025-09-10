#!/usr/bin/env python3
"""
Script para actualizar los estados de todos los depósitos según la nueva lógica:
- PENDIENTE: Solo si tiene cheques o retenciones
- LISTO: Todos los demás casos (independiente de diferencias faltantes/sobrantes)
"""

from database import SessionLocal
from models.deposit import Deposit, EstadoDeposito
from models.cheque_retencion import Cheque, Retencion
from sqlalchemy.orm import joinedload
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_all_deposit_states():
    """Actualiza el estado de todos los depósitos según la nueva lógica"""
    
    db = SessionLocal()
    try:
        # Obtener todos los depósitos con sus cheques y retenciones cargados
        deposits = db.query(Deposit).options(
            joinedload(Deposit.cheques),
            joinedload(Deposit.retenciones)
        ).all()
        
        logger.info(f"🔄 Iniciando actualización de estados para {len(deposits)} depósitos...")
        
        updated_count = 0
        pendiente_count = 0
        listo_count = 0
        
        for deposit in deposits:
            estado_anterior = deposit.estado
            
            # Verificar si tiene cheques o retenciones
            tiene_cheques = deposit.cheques and len(deposit.cheques) > 0
            tiene_retenciones = deposit.retenciones and len(deposit.retenciones) > 0
            
            # Aplicar nueva lógica
            if tiene_cheques or tiene_retenciones:
                nuevo_estado = EstadoDeposito.PENDIENTE
                pendiente_count += 1
            else:
                nuevo_estado = EstadoDeposito.LISTO
                listo_count += 1
            
            # Actualizar solo si cambió
            if deposit.estado != nuevo_estado:
                deposit.estado = nuevo_estado
                updated_count += 1
                
                logger.info(f"📋 Depósito {deposit.deposit_id}: {estado_anterior.value} → {nuevo_estado.value} "
                          f"(Cheques: {len(deposit.cheques) if deposit.cheques else 0}, "
                          f"Retenciones: {len(deposit.retenciones) if deposit.retenciones else 0})")
        
        # Guardar cambios
        db.commit()
        
        logger.info(f"✅ Actualización completada:")
        logger.info(f"   📊 Total depósitos procesados: {len(deposits)}")
        logger.info(f"   🔄 Estados actualizados: {updated_count}")
        logger.info(f"   ⏸️  Depósitos PENDIENTE: {pendiente_count}")
        logger.info(f"   ✅ Depósitos LISTO: {listo_count}")
        
        return {
            "total_procesados": len(deposits),
            "actualizados": updated_count,
            "pendientes": pendiente_count,
            "listos": listo_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error durante la actualización: {e}")
        raise
    finally:
        db.close()

def show_current_state_distribution():
    """Muestra la distribución actual de estados antes de actualizar"""
    
    db = SessionLocal()
    try:
        from sqlalchemy import func
        
        # Contar depósitos por estado
        estado_counts = db.query(
            Deposit.estado, 
            func.count(Deposit.id).label('count')
        ).group_by(Deposit.estado).all()
        
        logger.info("📊 Distribución actual de estados:")
        for estado, count in estado_counts:
            logger.info(f"   {estado.value}: {count} depósitos")
            
        # Mostrar algunos ejemplos de depósitos con cheques/retenciones
        deposits_with_docs = db.query(Deposit).options(
            joinedload(Deposit.cheques),
            joinedload(Deposit.retenciones)
        ).limit(5).all()
        
        logger.info("📋 Ejemplos de depósitos con documentos:")
        for dep in deposits_with_docs:
            cheques_count = len(dep.cheques) if dep.cheques else 0
            retenciones_count = len(dep.retenciones) if dep.retenciones else 0
            
            if cheques_count > 0 or retenciones_count > 0:
                logger.info(f"   Depósito {dep.deposit_id}: Estado {dep.estado.value}, "
                          f"Cheques: {cheques_count}, Retenciones: {retenciones_count}")
                
    except Exception as e:
        logger.error(f"❌ Error al mostrar estado actual: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🚀 Iniciando actualización masiva de estados de depósitos")
    logger.info("📋 Nueva lógica: PENDIENTE solo si tiene cheques/retenciones, LISTO en todos los demás casos")
    
    # Mostrar estado actual
    show_current_state_distribution()
    
    # Confirmar antes de proceder
    respuesta = input("\n¿Desea proceder con la actualización? (s/N): ")
    if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        resultado = update_all_deposit_states()
        logger.info("🎉 Actualización completada exitosamente")
    else:
        logger.info("❌ Actualización cancelada por el usuario")
