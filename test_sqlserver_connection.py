#!/usr/bin/env python3
"""
Script para probar la conexión a SQL Server
"""
import pymssql

def test_pymssql_connection():
    """Probar conexión directa con pymssql"""
    print("🔌 Probando conexión pymssql a SQL Server...")
    
    try:
        conn = pymssql.connect(
            server='192.168.0.234',
            user='h2o',
            password='Jumi1234',
            database='PAC',
            port=1433,
            timeout=30
        )
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"✅ Conexión exitosa!")
        print(f"📊 Versión SQL Server: {version[:50]}...")
        
        # Test database
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        print(f"🗄️ Base de datos actual: {db_name}")
        
        # List tables
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        print(f"📋 Tablas existentes ({len(tables)}):")
        for table in tables[:10]:  # Mostrar solo las primeras 10
            print(f"   - {table[0]}")
        if len(tables) > 10:
            print(f"   ... y {len(tables) - 10} más")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("\n💡 Posibles soluciones:")
        print("1. Verificar que el servidor SQL Server esté accesible en 192.168.0.234:1433")
        print("2. Verificar credenciales (usuario: h2o, contraseña: Jumi1234)")
        print("3. Verificar que el puerto 1433 esté abierto")
        print("4. Verificar que la base de datos PAC exista")
        return False

def test_sqlalchemy_connection():
    """Probar conexión con SQLAlchemy"""
    print("\n🔌 Probando conexión SQLAlchemy...")
    
    import os
    os.environ["DB_TYPE"] = "sqlserver"
    
    try:
        from database import engine, SessionLocal
        from sqlalchemy import text
        
        # Test connection
        db = SessionLocal()
        result = db.execute(text("SELECT 1 as test, GETDATE() as server_time"))
        row = result.fetchone()
        db.close()
        
        print(f"✅ SQLAlchemy conexión exitosa!")
        print(f"🕒 Hora del servidor: {row[1]}")
        return True
        
    except Exception as e:
        print(f"❌ Error SQLAlchemy: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Probando conexiones a SQL Server")
    print("=" * 50)
    
    pymssql_ok = test_pymssql_connection()
    sqlalchemy_ok = test_sqlalchemy_connection()
    
    print("\n" + "=" * 50)
    if pymssql_ok and sqlalchemy_ok:
        print("🎉 ¡Todas las conexiones funcionan correctamente!")
        print("\n✨ Puedes proceder con la migración ejecutando:")
        print("   python migrate_to_sqlserver.py")
    else:
        print("❌ Hay problemas de conexión que resolver antes de migrar")
