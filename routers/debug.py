from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/debug",
    tags=["debug"]
)

@router.get("/test-auth")
def test_auth_setup():
    """Endpoint de debug para verificar la configuración de autenticación"""
    try:
        import sys
        sys.path.append('.')
        
        # Test imports step by step
        results = {"imports": {}, "database": {}, "user_creation": {}}
        
        try:
            from models.user import User, UserRole
            results["imports"]["user_models"] = "✅ OK"
        except Exception as e:
            results["imports"]["user_models"] = f"❌ {str(e)}"
            
        try:
            from database import SessionLocal, Base, engine
            results["imports"]["database"] = "✅ OK"
        except Exception as e:
            results["imports"]["database"] = f"❌ {str(e)}"
            
        try:
            import bcrypt
            results["imports"]["bcrypt"] = "✅ OK"
        except Exception as e:
            results["imports"]["bcrypt"] = f"❌ {str(e)}"
            
        # Test database connection
        try:
            Base.metadata.create_all(bind=engine)
            results["database"]["table_creation"] = "✅ OK"
        except Exception as e:
            results["database"]["table_creation"] = f"❌ {str(e)}"
            
        # Test database query
        try:
            db = SessionLocal()
            existing_users = db.query(User).count()
            results["database"]["query_test"] = f"✅ OK - {existing_users} usuarios"
            
            # Create SuperAdmin if doesn't exist
            if existing_users == 0:
                from datetime import datetime
                
                test_user = User(
                    username="superadmin",
                    email="admin@empresa.com",
                    full_name="Super Admin",
                    role=UserRole.SUPERADMIN,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
                # Hash password manually
                password = "admin123"
                password_bytes = password.encode('utf-8')
                salt = bcrypt.gensalt()
                test_user.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
                
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
                
                results["user_creation"]["superadmin"] = f"✅ Creado - ID: {test_user.id}"
                
                # Create additional test users
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
                
                results["user_creation"]["all_users"] = "✅ SuperAdmin, Admin y Usuario creados"
                
            else:
                users = db.query(User).all()
                results["user_creation"]["existing"] = [
                    {"username": u.username, "role": u.role.value, "active": u.is_active} 
                    for u in users
                ]
                
            db.close()
            
        except Exception as e:
            results["database"]["query_error"] = f"❌ {str(e)}"
            import traceback
            results["database"]["traceback"] = traceback.format_exc()
            
        return {
            "success": True,
            "message": "Diagnóstico de autenticación completado",
            "results": results,
            "credentials": {
                "superadmin": "superadmin / admin123",
                "admin": "admin / admin123", 
                "usuario": "usuario / admin123"
            }
        }
            
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )

@router.post("/test-login")
def test_login():
    """Test del proceso de login sin usar auth_service"""
    try:
        from database import SessionLocal
        from models.user import User
        import bcrypt
        import jwt
        from datetime import datetime, timedelta
        import os
        
        # Credenciales de prueba
        username = "superadmin"
        password = "admin123"
        
        db = SessionLocal()
        try:
            # Buscar usuario
            user = db.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if not user:
                return {
                    "success": False,
                    "error": "Usuario no encontrado",
                    "hint": "Ejecuta primero GET /api/debug/test-auth"
                }
            
            # Verificar contraseña
            password_bytes = password.encode('utf-8')
            hash_bytes = user.password_hash.encode('utf-8')
            password_valid = bcrypt.checkpw(password_bytes, hash_bytes)
            
            if not password_valid:
                return {
                    "success": False,
                    "error": "Contraseña incorrecta"
                }
            
            # Crear token JWT
            secret_key = os.getenv("JWT_SECRET_KEY", "mi_clave_secreta_jwt_para_cierre_repartos_2025_desarrollo")
            
            payload = {
                "sub": user.username,
                "user_id": user.id,
                "role": user.role.value,
                "full_name": user.full_name,
                "exp": datetime.utcnow() + timedelta(hours=2),
                "iat": datetime.utcnow()
            }
            
            token = jwt.encode(payload, secret_key, algorithm="HS256")
            
            # Actualizar último login
            user.last_login = datetime.utcnow()
            db.commit()
            
            return {
                "success": True,
                "message": "Login exitoso",
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 7200,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "is_active": user.is_active
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
