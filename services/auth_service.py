import jwt
from jwt.exceptions import ExpiredSignatureError, DecodeError, InvalidTokenError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.user import User, UserRole
from database import SessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

class AuthService:
    """Servicio de autenticación y gestión de usuarios"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "tu_clave_secreta_super_segura_aqui_2025")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 120  # 2 horas
        
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Crea un token JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifica y decodifica un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (DecodeError, InvalidTokenError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Autentica un usuario con username y password"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if user and user.verify_password(password):
                # Actualizar último login
                user.last_login = datetime.utcnow()
                db.commit()
                return user
            return None
        finally:
            db.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por username"""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.username == username).first()
        finally:
            db.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por ID"""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    
    def create_user(self, username: str, email: str, password: str, full_name: str, 
                   role: UserRole = UserRole.USUARIO, created_by_id: Optional[int] = None) -> User:
        """Crea un nuevo usuario"""
        db = SessionLocal()
        try:
            # Verificar si ya existe
            if db.query(User).filter(User.username == username).first():
                raise HTTPException(status_code=400, detail="Username ya existe")
            
            if db.query(User).filter(User.email == email).first():
                raise HTTPException(status_code=400, detail="Email ya existe")
            
            # Crear usuario
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                created_by=created_by_id
            )
            user.set_password(password)
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user
        finally:
            db.close()
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Proceso completo de login"""
        user = self.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Crear token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "role": user.role.value,
                "full_name": user.full_name
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "user": user.to_dict()
        }
    
    def get_all_users(self) -> list[User]:
        """Obtiene todos los usuarios (solo para SuperAdmin)"""
        db = SessionLocal()
        try:
            return db.query(User).order_by(User.created_at.desc()).all()
        finally:
            db.close()
    
    def update_user_role(self, user_id: int, new_role: UserRole) -> User:
        """Actualiza el rol de un usuario"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
            user.role = new_role
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()
    
    def deactivate_user(self, user_id: int) -> User:
        """Desactiva un usuario"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
            user.is_active = False
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()

# Instancia global del servicio
auth_service = AuthService()
