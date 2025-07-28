from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(
    prefix="/fix",
    tags=["fix"]
)

class LoginRequest(BaseModel):
    username: str
    password: str

@router.get("/setup")
def setup_auth():
    """Configurar autenticación desde cero"""
    try:
        import sys
        sys.path.append('.')
        
        from database import SessionLocal, Base, engine
        from models.user import User, UserRole
        import bcrypt
        from datetime import datetime
        
        # Crear tablas
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            # Verificar usuarios existentes
            existing = db.query(User).count()
            
            if existing == 0:
                # Crear SuperAdmin
                password = "admin123"
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
                superadmin = User(
                    username="superadmin",
                    email="admin@empresa.com",
                    full_name="Super Admin",
                    role=UserRole.SUPERADMIN,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    password_hash=hashed
                )
                
                db.add(superadmin)
                db.commit()
                db.refresh(superadmin)
                
                return {
                    "success": True,
                    "message": "SuperAdmin creado",
                    "credentials": "superadmin / admin123",
                    "user_id": superadmin.id
                }
            else:
                users = db.query(User).all()
                return {
                    "success": True,
                    "message": f"{existing} usuarios ya existen",
                    "users": [{"username": u.username, "role": u.role.value} for u in users]
                }
                
        finally:
            db.close()
            
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()}
        )

@router.post("/login")
def login_fix(login_data: LoginRequest):
    """Login que funciona sin auth_service"""
    try:
        from database import SessionLocal
        from models.user import User
        import bcrypt
        import jwt
        from datetime import datetime, timedelta
        import os
        
        db = SessionLocal()
        try:
            # Buscar usuario
            user = db.query(User).filter(
                User.username == login_data.username,
                User.is_active == True
            ).first()
            
            if not user:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Usuario no encontrado"}
                )
            
            # Verificar contraseña
            if not bcrypt.checkpw(login_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Contraseña incorrecta"}
                )
            
            # Crear token
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
            content={"error": str(e), "traceback": traceback.format_exc()}
        )
