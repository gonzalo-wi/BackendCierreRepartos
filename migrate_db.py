#!/usr/bin/env python3
"""
Script para migrar la base de datos y agregar los nuevos campos
"""
import sqlite3
import os

def migrate_database():
    """
    Migra la base de datos agregando los nuevos campos
    """
    print("🔄 Iniciando migración de base de datos...")
    
    # Buscar archivo de base de datos
    db_files = ['repartos.db', 'deposits.db']
    db_path = None
    
    for db_file in db_files:
        if os.path.exists(db_file):
            db_path = db_file
            break
    
    if not db_path:
        print("❌ No se encontró archivo de base de datos")
        return False
    
    print(f"📂 Usando base de datos: {db_path}")
    
    # Conectar directamente a SQLite para agregar columnas
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar si las columnas ya existen
        cursor.execute("PRAGMA table_info(deposits)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Columnas actuales: {columns}")
        
        # Agregar deposit_esperado si no existe
        if 'deposit_esperado' not in columns:
            print("➕ Agregando columna 'deposit_esperado'...")
            cursor.execute("ALTER TABLE deposits ADD COLUMN deposit_esperado INTEGER")
        else:
            print("✅ Columna 'deposit_esperado' ya existe")
        
        # Agregar estado si no existe
        if 'estado' not in columns:
            print("➕ Agregando columna 'estado'...")
            cursor.execute("ALTER TABLE deposits ADD COLUMN estado VARCHAR(20) DEFAULT 'PENDIENTE'")
        else:
            print("✅ Columna 'estado' ya existe")
        
        conn.commit()
        print("✅ Migración completada exitosamente")
        
        # Mostrar estadísticas
        cursor.execute("SELECT COUNT(*) FROM deposits")
        total = cursor.fetchone()[0]
        print(f"📊 Total de depósitos en BD: {total}")
        
        # Verificar estructura final
        cursor.execute("PRAGMA table_info(deposits)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Columnas después de migración: {final_columns}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
