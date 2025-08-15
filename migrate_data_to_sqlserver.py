#!/usr/bin/env python3
"""
Script para migrar DATOS de SQLite a SQL Server
"""
import os
import sys
import sqlite3
from datetime import datetime

# Configurar el entorno para usar SQL Server
os.environ["DB_TYPE"] = "sqlserver"

# Importar después de configurar el entorno
from database import SessionLocal
from models.deposit import Deposit, EstadoDeposito
from models.cheque_retencion import Cheque, Retencion
from models.user import User, UserRole

def safe_get_column(row, column_name, default=None):
    """Obtener columna de forma segura desde sqlite3.Row"""
    try:
        return row[column_name]
    except (KeyError, IndexError):
        return default

def convert_string_to_int_safe(value):
    """Convertir string a int de forma segura"""
    if value is None:
        return None
    try:
        # Si es string, intentar convertir a int
        if isinstance(value, str):
            # Quitar espacios y caracteres especiales
            clean_value = value.strip()
            if clean_value == '' or clean_value.lower() in ['none', 'null']:
                return None
            return int(float(clean_value))  # float primero por si tiene decimales
        # Si ya es numérico, convertir a int
        return int(value)
    except (ValueError, TypeError):
        return None

def convert_string_to_float_safe(value):
    """Convertir valor a float de forma segura"""
    if value is None:
        return None
    try:
        if isinstance(value, str):
            clean_value = value.strip()
            if clean_value == '' or clean_value.lower() in ['none', 'null']:
                return None
            return float(clean_value)
        return float(value)
    except (ValueError, TypeError):
        return None

def migrate_users():
    """Migrar usuarios desde SQLite"""
    print("👥 Migrando usuarios...")
    
    # Conexión a SQLite
    sqlite_conn = sqlite3.connect('deposits.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Conexión a SQL Server
    sqlserver_db = SessionLocal()
    
    try:
        sqlite_cursor.execute("SELECT * FROM users")
        users_data = sqlite_cursor.fetchall()
        
        migrated = 0
        for user_row in users_data:
            existing_user = sqlserver_db.query(User).filter(User.username == user_row['username']).first()
            if not existing_user:
                user = User(
                    username=user_row['username'],
                    email=user_row['email'],
                    password_hash=user_row['password_hash'],
                    full_name=user_row['full_name'],
                    role=UserRole(user_row['role']),
                    is_active=bool(user_row['is_active']),
                    created_at=datetime.fromisoformat(user_row['created_at']) if user_row['created_at'] else None,
                    last_login=datetime.fromisoformat(user_row['last_login']) if user_row['last_login'] else None,
                    created_by=safe_get_column(user_row, 'created_by')
                )
                sqlserver_db.add(user)
                migrated += 1
        
        sqlserver_db.commit()
        print(f"✅ {migrated} usuarios migrados")
        return True
        
    except Exception as e:
        sqlserver_db.rollback()
        print(f"❌ Error migrando usuarios: {e}")
        return False
    finally:
        sqlite_conn.close()
        sqlserver_db.close()

def migrate_deposits():
    """Migrar depósitos desde SQLite"""
    print("💰 Migrando depósitos...")
    
    sqlite_conn = sqlite3.connect('deposits.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    sqlserver_db = SessionLocal()
    
    try:
        sqlite_cursor.execute("SELECT * FROM deposits")
        deposits_data = sqlite_cursor.fetchall()
        
        migrated = 0
        for deposit_row in deposits_data:
            existing_deposit = sqlserver_db.query(Deposit).filter(Deposit.deposit_id == deposit_row['deposit_id']).first()
            if not existing_deposit:
                deposit = Deposit(
                    deposit_id=deposit_row['deposit_id'],
                    identifier=safe_get_column(deposit_row, 'identifier'),
                    user_name=safe_get_column(deposit_row, 'user_name'),
                    total_amount=safe_get_column(deposit_row, 'total_amount', 0),
                    deposit_esperado=safe_get_column(deposit_row, 'deposit_esperado'),
                    composicion_esperado=safe_get_column(deposit_row, 'composicion_esperado'),
                    currency_code=safe_get_column(deposit_row, 'currency_code'),
                    deposit_type=safe_get_column(deposit_row, 'deposit_type'),
                    date_time=datetime.fromisoformat(deposit_row['date_time']) if deposit_row['date_time'] else None,
                    pos_name=safe_get_column(deposit_row, 'pos_name'),
                    st_name=safe_get_column(deposit_row, 'st_name'),
                    estado=EstadoDeposito(safe_get_column(deposit_row, 'estado', 'PENDIENTE')),
                    fecha_envio=datetime.fromisoformat(safe_get_column(deposit_row, 'fecha_envio')) if safe_get_column(deposit_row, 'fecha_envio') else None
                )
                sqlserver_db.add(deposit)
                migrated += 1
        
        sqlserver_db.commit()
        print(f"✅ {migrated} depósitos migrados")
        return True
        
    except Exception as e:
        sqlserver_db.rollback()
        print(f"❌ Error migrando depósitos: {e}")
        return False
    finally:
        sqlite_conn.close()
        sqlserver_db.close()

def migrate_cheques():
    """Migrar cheques desde SQLite"""
    print("📋 Migrando cheques...")
    
    sqlite_conn = sqlite3.connect('deposits.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    sqlserver_db = SessionLocal()
    
    try:
        # Verificar si la tabla cheques existe
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cheques'")
        if not sqlite_cursor.fetchone():
            print("ℹ️ Tabla cheques no existe en SQLite")
            return True
        
        sqlite_cursor.execute("SELECT * FROM cheques")
        cheques_data = sqlite_cursor.fetchall()
        
        migrated = 0
        for cheque_row in cheques_data:
            existing_cheque = sqlserver_db.query(Cheque).filter(Cheque.id == cheque_row['id']).first()
            if not existing_cheque:
                cheque = Cheque(
                    deposit_id=cheque_row['deposit_id'],
                    nrocta=convert_string_to_int_safe(safe_get_column(cheque_row, 'nrocta', 1)),
                    concepto=safe_get_column(cheque_row, 'concepto', 'CHE'),
                    banco=safe_get_column(cheque_row, 'banco'),
                    sucursal=safe_get_column(cheque_row, 'sucursal', '001'),
                    localidad=safe_get_column(cheque_row, 'localidad', '1234'),
                    nro_cheque=str(safe_get_column(cheque_row, 'nro_cheque', '')),
                    nro_cuenta=convert_string_to_int_safe(safe_get_column(cheque_row, 'nro_cuenta', 1234)),
                    titular=safe_get_column(cheque_row, 'titular', ''),
                    fecha=safe_get_column(cheque_row, 'fecha'),
                    importe=convert_string_to_float_safe(safe_get_column(cheque_row, 'importe'))
                )
                sqlserver_db.add(cheque)
                migrated += 1
        
        sqlserver_db.commit()
        print(f"✅ {migrated} cheques migrados")
        return True
        
    except Exception as e:
        sqlserver_db.rollback()
        print(f"❌ Error migrando cheques: {e}")
        return False
    finally:
        sqlite_conn.close()
        sqlserver_db.close()

def migrate_retenciones():
    """Migrar retenciones desde SQLite"""
    print("🔒 Migrando retenciones...")
    
    sqlite_conn = sqlite3.connect('deposits.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    sqlserver_db = SessionLocal()
    
    try:
        # Verificar si la tabla retenciones existe
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='retenciones'")
        if not sqlite_cursor.fetchone():
            print("ℹ️ Tabla retenciones no existe en SQLite")
            return True
        
        sqlite_cursor.execute("SELECT * FROM retenciones")
        retenciones_data = sqlite_cursor.fetchall()
        
        migrated = 0
        for retencion_row in retenciones_data:
            existing_retencion = sqlserver_db.query(Retencion).filter(Retencion.id == retencion_row['id']).first()
            if not existing_retencion:
                # El nro_retencion puede ser numérico en SQLite, necesitamos convertirlo a string
                nro_retencion_raw = safe_get_column(retencion_row, 'nro_retencion')
                nro_retencion = str(nro_retencion_raw) if nro_retencion_raw is not None else None
                
                retencion = Retencion(
                    deposit_id=retencion_row['deposit_id'],
                    nrocta=convert_string_to_int_safe(safe_get_column(retencion_row, 'nrocta', 1)),
                    concepto=safe_get_column(retencion_row, 'concepto', 'RIB'),
                    nro_retencion=nro_retencion,
                    fecha=safe_get_column(retencion_row, 'fecha'),
                    importe=convert_string_to_float_safe(safe_get_column(retencion_row, 'importe')),
                    tipo=safe_get_column(retencion_row, 'tipo')
                )
                sqlserver_db.add(retencion)
                migrated += 1
        
        sqlserver_db.commit()
        print(f"✅ {migrated} retenciones migradas")
        return True
        
    except Exception as e:
        sqlserver_db.rollback()
        print(f"❌ Error migrando retenciones: {e}")
        return False
    finally:
        sqlite_conn.close()
        sqlserver_db.close()

def main():
    """Función principal de migración de datos"""
    print("📊 Iniciando migración de DATOS a SQL Server...")
    print("=" * 60)
    
    if not os.path.exists('deposits.db'):
        print("❌ No se encontró la base de datos SQLite (deposits.db)")
        print("   Asegúrate de estar en el directorio correcto")
        return
    
    print("📋 Iniciando migración de datos...")
    
    # Migrar en orden de dependencias
    success = True
    
    # 1. Usuarios (no tienen dependencias)
    if not migrate_users():
        success = False
    
    # 2. Depósitos (no tienen dependencias de otros datos)
    if not migrate_deposits():
        success = False
    
    # 3. Cheques (dependen de depósitos)
    if not migrate_cheques():
        success = False
    
    # 4. Retenciones (dependen de depósitos)
    if not migrate_retenciones():
        success = False
    
    print("=" * 60)
    if success:
        print("🎉 ¡Migración de datos completada exitosamente!")
        print()
        print("📊 Próximos pasos:")
        print("1. Verificar que los datos se migraron correctamente")
        print("2. Probar la funcionalidad del sistema")
        print("3. Hacer backup de la nueva base de datos")
    else:
        print("⚠️ Migración completada con algunos errores")
        print("   Revisa los mensajes arriba para más detalles")
        print("   Los datos que se migraron exitosamente están disponibles")

if __name__ == "__main__":
    main()
