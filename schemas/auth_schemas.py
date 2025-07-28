from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from models.user import UserRole

# Schemas para autenticación
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

# Schemas para usuarios
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.USUARIO
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('La nueva contraseña debe tener al menos 6 caracteres')
        return v

# Schemas para respuestas
class MessageResponse(BaseModel):
    message: str
    success: bool = True

class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int

# Schema para información del usuario actual
class CurrentUserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    permissions: dict
    
    class Config:
        from_attributes = True
