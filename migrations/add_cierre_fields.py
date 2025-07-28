"""
Script de migración para agregar el campo fecha_envio para el cierre de repartos
"""
import sqlite3
from datetime import datetime

def migrate_database():
    """
    Agrega el campo fecha_envio necesario para el sistema de cierre de repartos
    """
    conn = sqlite3.connect('./repartos.db')
    cursor = conn.cursor()
    
    try:
        print("🔄 Iniciando migración de base de datos...")
        
        # Solo agregar el campo fecha_envio
        try:
            cursor.execute("ALTER TABLE deposits ADD COLUMN fecha_envio DATETIME")
            print("✅ Campo 'fecha_envio' agregado exitosamente")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("⚠️ Campo 'fecha_envio' ya existe, omitiendo...")
            else:
                print(f"❌ Error al agregar campo 'fecha_envio': {e}")
                raise e
        
        conn.commit()
        print("✅ Migración completada exitosamente")
        
        # Verificar los cambios
        cursor.execute("PRAGMA table_info(deposits)")
        columns = cursor.fetchall()
        print(f"\n📋 Estructura actual de la tabla 'deposits':")
        for column in columns:
            print(f"   - {column[1]} ({column[2]})")
            
    except Exception as e:
        conn.rollback()
        print(f"💥 Error durante la migración: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
