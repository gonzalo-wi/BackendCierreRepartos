"""
Script para crear las nuevas tablas de cheques y retenciones
"""
from database import engine, Base
from models.cheque_retencion import Cheque, Retencion

def create_new_tables():
    """Crear las nuevas tablas en la base de datos"""
    print("🔄 Creando nuevas tablas...")
    
    try:
        # Crear todas las tablas definidas en los modelos
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente:")
        print("   - cheques") 
        print("   - retenciones")
    except Exception as e:
        print(f"❌ Error al crear tablas: {str(e)}")
        raise

if __name__ == "__main__":
    create_new_tables()
