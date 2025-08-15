#!/usr/bin/env python3
"""
Script para migrar de SQLite a SQL Server
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sqlite3
import json
from datetime import datetime

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

def migrate_data_from_sqlite():
    """Migrar datos desde SQLite a SQL Server"""
    print("📊 Migrando datos desde SQLite...")
    
    # Conexión a SQLite
    sqlite_conn = sqlite3.connect('deposits.db')
    sqlite_conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
    sqlite_cursor = sqlite_conn.cursor()
    
    # Conexión a SQL Server
    sqlserver_db = SessionLocal()
    
    try:
        # Migrar usuarios
        print("👥 Migrando usuarios...")
        sqlite_cursor.execute("SELECT * FROM users")
        users_data = sqlite_cursor.fetchall()
        
        for user_row in users_data:
            existing_user = sqlserver_db.query(User).filter(User.username == user_row['username']).first()
            if not existing_user:
                user = User(
                    id=user_row['id'],
                    username=user_row['username'],
                    email=user_row['email'],
                    password_hash=user_row['password_hash'],
                    full_name=user_row['full_name'],
                    role=UserRole(user_row['role']),
                    is_active=user_row['is_active'],
                    created_at=datetime.fromisoformat(user_row['created_at']) if user_row['created_at'] else None,
                    last_login=datetime.fromisoformat(user_row['last_login']) if user_row['last_login'] else None,
                    created_by=user_row['created_by']
                )
                sqlserver_db.add(user)
        
        # Migrar depósitos
        print("💰 Migrando depósitos...")
        sqlite_cursor.execute("SELECT * FROM deposits")
        deposits_data = sqlite_cursor.fetchall()
        
        for deposit_row in deposits_data:
            existing_deposit = sqlserver_db.query(Deposit).filter(Deposit.deposit_id == deposit_row['deposit_id']).first()
            if not existing_deposit:
                deposit = Deposit(
                    id=deposit_row['id'],
                    deposit_id=deposit_row['deposit_id'],
                    identifier=deposit_row['identifier'],
                    user_name=deposit_row['user_name'],
                    total_amount=deposit_row['total_amount'],
                    deposit_esperado=deposit_row['deposit_esperado'] if 'deposit_esperado' in deposit_row.keys() else None,
                    composicion_esperado=deposit_row['composicion_esperado'] if 'composicion_esperado' in deposit_row.keys() else None,
                    currency_code=deposit_row['currency_code'],
                    deposit_type=deposit_row['deposit_type'],
                    date_time=datetime.fromisoformat(deposit_row['date_time']) if deposit_row['date_time'] else None,
                    pos_name=deposit_row['pos_name'],
                    st_name=deposit_row['st_name'],
                    estado=EstadoDeposito(deposit_row['estado'] if 'estado' in deposit_row.keys() else 'PENDIENTE'),
                    fecha_envio=datetime.fromisoformat(deposit_row['fecha_envio']) if ('fecha_envio' in deposit_row.keys() and deposit_row['fecha_envio']) else None
                )
                sqlserver_db.add(deposit)
        
        # Migrar cheques
        print("📋 Migrando cheques...")
        try:
            sqlite_cursor.execute("SELECT * FROM cheques")
            cheques_data = sqlite_cursor.fetchall()
            
            for cheque_row in cheques_data:
                existing_cheque = sqlserver_db.query(Cheque).filter(Cheque.id == cheque_row['id']).first()
                if not existing_cheque:
                    cheque = Cheque(
                        id=cheque_row['id'],
                        deposit_id=cheque_row['deposit_id'],
                        nrocta=cheque_row['nrocta'] if 'nrocta' in cheque_row.keys() else 1,
                        concepto=cheque_row['concepto'] if 'concepto' in cheque_row.keys() else 'CHE',
                        banco=cheque_row['banco'] if 'banco' in cheque_row.keys() else None,
                        sucursal=cheque_row['sucursal'] if 'sucursal' in cheque_row.keys() else '001',
                        localidad=cheque_row['localidad'] if 'localidad' in cheque_row.keys() else '1234',
                        nro_cheque=cheque_row['nro_cheque'] if 'nro_cheque' in cheque_row.keys() else None,
                        nro_cuenta=cheque_row['nro_cuenta'] if 'nro_cuenta' in cheque_row.keys() else 1234,
                        titular=cheque_row['titular'] if 'titular' in cheque_row.keys() else '',
                        fecha=cheque_row['fecha'] if 'fecha' in cheque_row.keys() else None,
                        importe=cheque_row['importe'] if 'importe' in cheque_row.keys() else None
                    )
                    sqlserver_db.add(cheque)
        except Exception as e:
            print(f"⚠️ No se pudieron migrar cheques (tabla puede no existir): {e}")
        
        # Migrar retenciones
        print("🔒 Migrando retenciones...")
        try:
            sqlite_cursor.execute("SELECT * FROM retenciones")
            retenciones_data = sqlite_cursor.fetchall()
            
            for retencion_row in retenciones_data:
                existing_retencion = sqlserver_db.query(Retencion).filter(Retencion.id == retencion_row['id']).first()
                if not existing_retencion:
                    retencion = Retencion(
                        id=retencion_row['id'],
                        deposit_id=retencion_row['deposit_id'],
                        nrocta=retencion_row['nrocta'] if 'nrocta' in retencion_row.keys() else 1,
                        concepto=retencion_row['concepto'] if 'concepto' in retencion_row.keys() else 'RIB',
                        nro_retencion=retencion_row['nro_retencion'] if 'nro_retencion' in retencion_row.keys() else None,
                        fecha=retencion_row['fecha'] if 'fecha' in retencion_row.keys() else None,
                        importe=retencion_row['importe'] if 'importe' in retencion_row.keys() else None,
                        tipo=retencion_row['tipo'] if 'tipo' in retencion_row.keys() else None
                    )
                    sqlserver_db.add(retencion)
        except Exception as e:
            print(f"⚠️ No se pudieron migrar retenciones (tabla puede no existir): {e}")
        
        # Commit de todos los cambios
        sqlserver_db.commit()
        print("✅ Migración completada exitosamente")
        
    except Exception as e:
        sqlserver_db.rollback()
        print(f"❌ Error durante la migración: {e}")
        return False
    finally:
        sqlite_conn.close()
        sqlserver_db.close()
    
    return True

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
    print("🚀 Iniciando migración a SQL Server...")
    print("=" * 50)
    
    # Paso 1: Probar conexión
    if not test_connection():
        print("❌ Abortando migración por problemas de conexión")
        return
    
    # Paso 2: Crear tablas
    if not create_tables():
        print("❌ Abortando migración por problemas creando tablas")
        return
    
    # Paso 3: Migrar datos (opcional)
    if os.path.exists('deposits.db'):
        response = input("¿Migrar datos desde SQLite? (s/n): ").lower()
        if response in ['s', 'si', 'yes', 'y']:
            if not migrate_data_from_sqlite():
                print("❌ Error en migración de datos")
                return
    else:
        print("ℹ️ No se encontró base SQLite para migrar")
    
    # Paso 4: Crear superadmin
    create_superadmin()
    
    print("=" * 50)
    print("🎉 ¡Migración completada!")
    print()
    print("📋 Próximos pasos:")
    print("1. Configurar variable de entorno: export DB_TYPE=sqlserver")
    print("2. Reiniciar el servidor FastAPI")
    print("3. Verificar que todo funcione correctamente")
    print()
    print("🔑 Credenciales superadmin:")
    print("   Usuario: superadmin")
    print("   Contraseña: admin123 (¡CAMBIAR INMEDIATAMENTE!)")

if __name__ == "__main__":
    main()
