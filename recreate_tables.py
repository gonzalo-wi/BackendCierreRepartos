"""
Script para recrear las tablas de cheques y retenciones con la nueva estructura
"""
import sqlite3
from database import engine, Base
from models.deposit import Deposit  # Importar primero Deposit
from models.cheque_retencion import Cheque, Retencion  # Luego los que dependen de él

def recreate_tables():
    """Eliminar y recrear las tablas con la nueva estructura"""
    print("🔄 Recreando tablas con nueva estructura...")
    
    try:
        # Conectar a la base de datos SQLite
        db_path = "deposits.db"  # Ajusta si tu base de datos tiene otro nombre
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Eliminar tablas existentes si existen
        print("🗑️ Eliminando tablas existentes...")
        cursor.execute("DROP TABLE IF EXISTS cheques")
        cursor.execute("DROP TABLE IF EXISTS retenciones") 
        cursor.execute("DROP TABLE IF EXISTS repartos")
        
        conn.commit()
        conn.close()
        
        # Recrear las tablas con la nueva estructura
        print("🔨 Creando nuevas tablas...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas recreadas exitosamente:")
        print("   - cheques (con deposit_id)")
        print("   - retenciones (con deposit_id)")
        print("   - tabla repartos eliminada")
        
    except Exception as e:
        print(f"❌ Error al recrear tablas: {str(e)}")
        raise

if __name__ == "__main__":
    recreate_tables()
