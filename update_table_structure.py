#!/usr/bin/env python3
"""
Script para actualizar las tablas con campos de fecha más grandes
"""
import os
os.environ["DB_TYPE"] = "sqlserver"

from database import SessionLocal, engine
from sqlalchemy import text

def update_table_structure():
    """Actualizar estructura de tablas"""
    print("🔧 Actualizando estructura de tablas...")
    
    db = SessionLocal()
    try:
        # Actualizar campo fecha en cheques
        print("📋 Actualizando tabla cheques...")
        db.execute(text("ALTER TABLE cheques ALTER COLUMN fecha VARCHAR(50)"))
        
        # Actualizar campo fecha en retenciones
        print("🔒 Actualizando tabla retenciones...")
        db.execute(text("ALTER TABLE retenciones ALTER COLUMN fecha VARCHAR(50)"))
        
        db.commit()
        print("✅ Estructura actualizada exitosamente")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error actualizando estructura: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if update_table_structure():
        print("\n🎉 ¡Estructura actualizada!")
        print("📋 Ahora puedes ejecutar nuevamente:")
        print("   python migrate_data_to_sqlserver.py")
    else:
        print("\n❌ Error en actualización de estructura")
