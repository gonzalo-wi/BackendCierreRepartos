#!/usr/bin/env python3
"""
Script para crear el usuario SuperAdmin inicial del sistema
"""
import sys
import os
sys.path.append('.')

from services.auth_service import auth_service
from models.user import UserRole
from database import Base, engine

def create_initial_superadmin():
    """Crea el usuario SuperAdmin inicial"""
    
    print("🔐 Configuración inicial del sistema de autenticación")
    print("=" * 60)
    
    # Crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas de base de datos verificadas")
    
    # Verificar si ya existe un SuperAdmin
    existing_users = auth_service.get_all_users()
    superadmins = [u for u in existing_users if u.role == UserRole.SUPERADMIN]
    
    if superadmins:
        print(f"⚠️ Ya existe(n) {len(superadmins)} SuperAdmin(s):")
        for admin in superadmins:
            print(f"   - {admin.username} ({admin.email})")
        
        respuesta = input("\n¿Deseas crear otro SuperAdmin? (y/n): ")
        if respuesta.lower() != 'y':
            print("❌ Operación cancelada")
            return
    
    print("\n📝 Creando usuario SuperAdmin inicial...")
    
    # Solicitar datos del usuario
    print("\nIngresa los datos del SuperAdmin:")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    full_name = input("Nombre completo: ").strip()
    password = input("Contraseña (mín. 6 caracteres): ").strip()
    
    # Validaciones básicas
    if len(username) < 3:
        print("❌ El username debe tener al menos 3 caracteres")
        return
    
    if len(password) < 6:
        print("❌ La contraseña debe tener al menos 6 caracteres")
        return
    
    if "@" not in email:
        print("❌ Email inválido")
        return
    
    try:
        # Crear usuario
        user = auth_service.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=UserRole.SUPERADMIN
        )
        
        print(f"\n✅ Usuario SuperAdmin creado exitosamente!")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Nombre: {user.full_name}")
        print(f"   Rol: {user.role.value}")
        print(f"   Creado: {user.created_at}")
        
        print(f"\n🎯 Credenciales de acceso:")
        print(f"   Username: {username}")
        print(f"   Password: [OCULTA]")
        
        print(f"\n🚀 Ahora puedes:")
        print(f"   1. Hacer login en: POST /api/auth/login")
        print(f"   2. Crear más usuarios desde: POST /api/auth/users")
        print(f"   3. Gestionar repartos con permisos completos")
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")

def create_demo_users():
    """Crea usuarios de demostración"""
    print("\n🎭 ¿Deseas crear usuarios de demostración? (y/n): ", end="")
    respuesta = input()
    
    if respuesta.lower() != 'y':
        return
    
    try:
        # Usuario Admin
        admin_user = auth_service.create_user(
            username="admin",
            email="admin@empresa.com",
            password="admin123",
            full_name="Administrador Sistema",
            role=UserRole.ADMIN
        )
        print(f"✅ Usuario Admin creado: admin / admin123")
        
        # Usuario normal
        normal_user = auth_service.create_user(
            username="usuario",
            email="usuario@empresa.com", 
            password="usuario123",
            full_name="Usuario Normal",
            role=UserRole.USUARIO
        )
        print(f"✅ Usuario normal creado: usuario / usuario123")
        
        print(f"\n🎯 Usuarios de demostración creados:")
        print(f"   SuperAdmin: [tu usuario creado arriba]")
        print(f"   Admin: admin / admin123")
        print(f"   Usuario: usuario / usuario123")
        
    except Exception as e:
        print(f"⚠️ Error al crear usuarios demo: {e}")

if __name__ == "__main__":
    create_initial_superadmin()
    create_demo_users()
    
    print(f"\n🏁 Configuración inicial completada!")
    print(f"💡 Inicia el servidor con: python3 main.py")
    print(f"📚 Documentación API en: http://localhost:8000/docs")
