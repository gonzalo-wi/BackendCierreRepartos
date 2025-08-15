#!/usr/bin/env python3

import pymssql
import sys

def main():
    try:
        print("🔧 Actualizando campos nrocta a BigInt...")
        
        # Conectar a SQL Server
        conn = pymssql.connect(
            server='192.168.0.234',
            user='h2o',
            password='Jumi1234',
            database='PAC',
            port=1433,
            timeout=30
        )
        
        cursor = conn.cursor()
        
        print("📋 Actualizando tabla cheques...")
        # Actualizar cheques
        try:
            cursor.execute("ALTER TABLE cheques ALTER COLUMN nrocta BIGINT")
            conn.commit()
            print("   ✅ Cheques actualizado")
        except Exception as e:
            print(f"   ⚠️ Error en cheques: {e}")
        
        print("🔒 Actualizando tabla retenciones...")
        # Actualizar retenciones
        try:
            cursor.execute("ALTER TABLE retenciones ALTER COLUMN nrocta BIGINT")
            conn.commit()
            print("   ✅ Retenciones actualizado")
        except Exception as e:
            print(f"   ⚠️ Error en retenciones: {e}")
        
        cursor.close()
        conn.close()
        
        print("✅ Campos nrocta actualizados exitosamente")
        print("🎉 ¡BigInt configurado!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
