#!/usr/bin/env python3
"""
Script simple para crear usuario SuperAdmin inicial
"""
import sys
sys.path.append('.')

def create_superadmin():
    try:
        print("🔧 Importando módulos...")
        
        from database import Base, engine, SessionLocal
        from models.user import User, UserRole
        import bcrypt
        from datetime import datetime
        
        print("✅ Módulos importados correctamente")
        
        # Crear todas las tablas
        print("🔧 Creando tablas...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas/verificadas")
        
        # Verificar si ya existe el usuario
        db = SessionLocal()
        try:
            existing_user = db.query(User).filter(User.username == "superadmin").first()
            
            if existing_user:
                print(f"⚠️ Usuario 'superadmin' ya existe:")
                print(f"   - ID: {existing_user.id}")
                print(f"   - Email: {existing_user.email}")
                print(f"   - Rol: {existing_user.role.value}")
                print("✅ Puedes usar las credenciales: superadmin / admin123")
                return
            
            # Crear usuario SuperAdmin
            print("🔧 Creando usuario SuperAdmin...")
            
            user = User(
                username="superadmin",
                email="admin@empresa.com",
                full_name="Super Administrador",
                role=UserRole.SUPERADMIN,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Hashear contraseña
            password = "admin123"
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            user.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
            # Guardar en la base de datos
            db.add(user)
            db.commit()
            db.refresh(user)
            
            print(f"✅ Usuario SuperAdmin creado exitosamente!")
            print(f"   - Username: superadmin")
            print(f"   - Password: admin123")
            print(f"   - Email: admin@empresa.com")
            print(f"   - ID: {user.id}")
            print(f"   - Rol: {user.role.value}")
            
            # Crear usuario Admin de prueba
            admin_user = User(
                username="admin",
                email="admin2@empresa.com",
                full_name="Administrador",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.utcnow()
            )
            admin_user.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
            db.add(admin_user)
            db.commit()
            
            print(f"✅ Usuario Admin creado:")
            print(f"   - Username: admin")
            print(f"   - Password: admin123")
            
            # Crear usuario normal de prueba
            user_normal = User(
                username="usuario",
                email="usuario@empresa.com",
                full_name="Usuario Normal",
                role=UserRole.USUARIO,
                is_active=True,
                created_at=datetime.utcnow()
            )
            user_normal.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
            db.add(user_normal)
            db.commit()
            
            print(f"✅ Usuario normal creado:")
            print(f"   - Username: usuario")
            print(f"   - Password: admin123")
            
            print(f"\n🎯 Credenciales para probar:")
            print(f"   SuperAdmin: superadmin / admin123")
            print(f"   Admin: admin / admin123")
            print(f"   Usuario: usuario / admin123")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_superadmin()
