#!/usr/bin/env python3
"""
Migración: Añadir campo efectivo_esperado a la tabla deposits

Este campo almacenará solo el valor del efectivo (no el total suma) 
para ser usado en el cierre de repartos via SOAP.
"""

import os
import sys

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine

def run_migration():
    """Ejecuta la migración para añadir el campo efectivo_esperado"""
    
    print("🔄 Iniciando migración: Añadir campo efectivo_esperado")
    
    try:
        with engine.connect() as connection:
            # Verificar si la columna ya existe
            check_query = """
            SELECT COUNT(*) as column_count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'deposits' 
            AND COLUMN_NAME = 'efectivo_esperado'
            """
            
            result = connection.execute(text(check_query))
            column_exists = result.fetchone()[0] > 0
            
            if column_exists:
                print("✅ La columna 'efectivo_esperado' ya existe en la tabla 'deposits'")
                return
            
            # Añadir la nueva columna
            alter_query = """
            ALTER TABLE deposits 
            ADD efectivo_esperado INTEGER NULL
            """
            
            print("📝 Ejecutando: ALTER TABLE deposits ADD efectivo_esperado INTEGER NULL")
            connection.execute(text(alter_query))
            connection.commit()
            
            print("✅ Migración completada exitosamente")
            print("📊 Campo 'efectivo_esperado' añadido a la tabla 'deposits'")
            
    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        raise

def rollback_migration():
    """Rollback de la migración (eliminar la columna)"""
    
    print("🔄 Iniciando rollback: Eliminar campo efectivo_esperado")
    
    try:
        with engine.connect() as connection:
            # Verificar si la columna existe antes de eliminarla
            check_query = """
            SELECT COUNT(*) as column_count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'deposits' 
            AND COLUMN_NAME = 'efectivo_esperado'
            """
            
            result = connection.execute(text(check_query))
            column_exists = result.fetchone()[0] > 0
            
            if not column_exists:
                print("✅ La columna 'efectivo_esperado' no existe en la tabla 'deposits'")
                return
            
            # Eliminar la columna
            drop_query = """
            ALTER TABLE deposits 
            DROP COLUMN efectivo_esperado
            """
            
            print("📝 Ejecutando: ALTER TABLE deposits DROP COLUMN efectivo_esperado")
            connection.execute(text(drop_query))
            connection.commit()
            
            print("✅ Rollback completado exitosamente")
            print("📊 Campo 'efectivo_esperado' eliminado de la tabla 'deposits'")
            
    except Exception as e:
        print(f"❌ Error durante el rollback: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        run_migration()
