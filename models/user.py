from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime
import bcrypt

class UserRole(enum.Enum):
    USUARIO = "USUARIO"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USUARIO)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)  # ID del usuario que lo creó

    def set_password(self, password: str):
        """Hashea y establece la contraseña"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verifica la contraseña"""
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def has_permission(self, required_role: UserRole) -> bool:
        """Verifica si el usuario tiene el rol requerido o superior"""
        role_hierarchy = {
            UserRole.USUARIO: 1,
            UserRole.ADMIN: 2,
            UserRole.SUPERADMIN: 3
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

    def can_manage_users(self) -> bool:
        """Solo SuperAdmin puede gestionar usuarios"""
        return self.role == UserRole.SUPERADMIN

    def can_close_repartos(self) -> bool:
        """Admin y SuperAdmin pueden cerrar repartos"""
        return self.role in [UserRole.ADMIN, UserRole.SUPERADMIN]

    def can_view_repartos(self) -> bool:
        """Todos los usuarios pueden ver repartos"""
        return self.role in [UserRole.USUARIO, UserRole.ADMIN, UserRole.SUPERADMIN]

    def to_dict(self):
        """Convierte el usuario a diccionario (sin password)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
