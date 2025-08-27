from fastapi import APIRouter, Header, HTTPException, status
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
        from services.auth_service import auth_service

        db = SessionLocal()
        try:
            # Buscar usuario
            user = db.query(User).filter(
                User.username == login_data.username,
                User.is_active == True
            ).first()

            if not user:
                return JSONResponse(status_code=401, content={"error": "Usuario no encontrado"})

            # Verificar contraseña
            if not bcrypt.checkpw(login_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
                return JSONResponse(status_code=401, content={"error": "Contraseña incorrecta"})

            # Crear token usando la MISMA clave que el servicio principal
            secret_key = auth_service.secret_key

            payload = {
                "sub": user.username,
                "user_id": user.id,
                "role": user.role.value,
                "full_name": user.full_name,
                "exp": datetime.utcnow() + timedelta(hours=2),
                "iat": datetime.utcnow(),
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
                    "is_active": user.is_active,
                },
            }
        finally:
            db.close()
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": traceback.format_exc()})

@router.post("/logout")
def logout_fix():
    """Logout no-op para frontend: solo responde 200 y deja que el cliente limpie el token"""
    return {"success": True, "message": "Logout realizado (cliente)"}

@router.get("/verify-token")
def verify_token_fix(Authorization: str | None = Header(None)):
    """Verifica el JWT usando el mismo servicio que el backend principal"""
    try:
        if not Authorization or not Authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta token")
        token = Authorization.split(" ", 1)[1]

        # Usar el servicio de auth para validar con la misma clave
        from services.auth_service import auth_service
        payload = auth_service.verify_token(token)
        return {"valid": True, "payload": payload}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
