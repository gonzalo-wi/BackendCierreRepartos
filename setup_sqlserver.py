#!/usr/bin/env python3
"""
Script para migrar de SQLite a SQL Server - SOLO TABLAS
"""
import os
import sys

# Configurar el entorno para usar SQL Server
os.environ["DB_TYPE"] = "sqlserver"

# Importar después de configurar el entorno
from database import engine, SessionLocal, Base
from models.deposit import Deposit, EstadoDeposito
from models.cheque_retencion import Cheque, Retencion
from models.user import User, UserRole
from models.daily_totals import DailyTotal

def create_tables():
    """Crear todas las tablas en SQL Server"""
    print("📦 Creando tablas en SQL Server...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def test_connection():
    """Probar la conexión a SQL Server"""
    print("🔌 Probando conexión a SQL Server...")
    try:
        db = SessionLocal()
        # Test simple query
        from sqlalchemy import text
        result = db.execute(text("SELECT 1 as test"))
        test_value = result.scalar()
        db.close()
        
        if test_value == 1:
            print("✅ Conexión a SQL Server exitosa")
            return True
        else:
            print("❌ Problema en la conexión")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def create_superadmin():
    """Crear usuario superadmin si no existe"""
    print("👑 Verificando usuario superadmin...")
    
    db = SessionLocal()
    try:
        superadmin = db.query(User).filter(User.username == "superadmin").first()
        if not superadmin:
            superadmin = User(
                username="superadmin",
                email="admin@jumillano.com",
                full_name="Administrador del Sistema",
                role=UserRole.SUPERADMIN,
                is_active=True
            )
            superadmin.set_password("admin123")  # Cambiar después
            db.add(superadmin)
            db.commit()
            print("✅ Usuario superadmin creado")
        else:
            print("ℹ️ Usuario superadmin ya existe")
    except Exception as e:
        db.rollback()
        print(f"❌ Error creando superadmin: {e}")
    finally:
        db.close()

def main():
    """Función principal de migración"""
    print("🚀 Iniciando configuración de SQL Server...")
    print("=" * 50)
    
    # Paso 1: Probar conexión
    if not test_connection():
        print("❌ Abortando configuración por problemas de conexión")
        return
    
    # Paso 2: Crear tablas
    if not create_tables():
        print("❌ Abortando configuración por problemas creando tablas")
        return
    
    # Paso 3: Crear superadmin
    create_superadmin()
    
    print("=" * 50)
    print("🎉 ¡Configuración completada!")
    print()
    print("📋 Próximos pasos:")
    print("1. Configurar variable de entorno: export DB_TYPE=sqlserver")
    print("2. Reiniciar el servidor FastAPI")
    print("3. Verificar que todo funcione correctamente")
    print()
    print("🔑 Credenciales superadmin:")
    print("   Usuario: superadmin")
    print("   Contraseña: admin123 (¡CAMBIAR INMEDIATAMENTE!)")
    print()
    print("ℹ️ Las tablas están listas. Puedes empezar a usar el sistema desde cero")
    print("   o migrar datos manualmente si es necesario.")

if __name__ == "__main__":
    main()
