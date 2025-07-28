from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel, EmailStr, validator
from database import SessionLocal
from models.user import User, UserRole
from auth.dependencies import get_superadmin_user
import bcrypt
from datetime import datetime

router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"]
)

# Schemas para gestión de usuarios
class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('El username debe tener al menos 3 caracteres')
        return v

class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class ChangePasswordRequest(BaseModel):
    user_id: int
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    created_by: Optional[int]

# === ENDPOINTS DE GESTIÓN DE USUARIOS ===

@router.get("/", response_model=List[UserResponse])
def get_all_users(current_user: User = Depends(get_superadmin_user)):
    """
    Obtener lista de todos los usuarios (solo SuperAdmin)
    """
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
                created_by=user.created_by
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {str(e)}")
    finally:
        db.close()

@router.post("/", response_model=UserResponse)
def create_user(
    user_data: CreateUserRequest,
    current_user: User = Depends(get_superadmin_user)
):
    """
    Crear un nuevo usuario (solo SuperAdmin)
    """
    db = SessionLocal()
    try:
        # Verificar si ya existe el username
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="El username ya existe")
        
        # Verificar si ya existe el email
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="El email ya existe")
        
        # Crear nuevo usuario
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=True,
            created_at=datetime.utcnow(),
            created_by=current_user.id
        )
        
        # Hashear contraseña
        password_bytes = user_data.password.encode('utf-8')
        salt = bcrypt.gensalt()
        new_user.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role.value,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login=new_user.last_login,
            created_by=new_user.created_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {str(e)}")
    finally:
        db.close()

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UpdateUserRequest,
    current_user: User = Depends(get_superadmin_user)
):
    """
    Actualizar un usuario (solo SuperAdmin)
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Prevenir que el SuperAdmin se desactive a sí mismo
        if user.id == current_user.id and user_data.is_active is False:
            raise HTTPException(status_code=400, detail="No puedes desactivarte a ti mismo")
        
        # Actualizar campos
        if user_data.email is not None:
            # Verificar que el email no esté en uso por otro usuario
            existing_email = db.query(User).filter(
                User.email == user_data.email,
                User.id != user_id
            ).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="El email ya está en uso")
            user.email = user_data.email
            
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
            
        if user_data.role is not None:
            user.role = user_data.role
            
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        db.commit()
        db.refresh(user)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            created_by=user.created_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {str(e)}")
    finally:
        db.close()

@router.post("/change-password")
def change_user_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_superadmin_user)
):
    """
    Cambiar contraseña de un usuario (solo SuperAdmin)
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == password_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Hashear nueva contraseña
        password_bytes = password_data.new_password.encode('utf-8')
        salt = bcrypt.gensalt()
        user.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Contraseña actualizada para el usuario {user.username}",
            "user_id": user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cambiar contraseña: {str(e)}")
    finally:
        db.close()

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_superadmin_user)
):
    """
    Eliminar un usuario (solo SuperAdmin)
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Prevenir que el SuperAdmin se elimine a sí mismo
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
        
        username = user.username
        db.delete(user)
        db.commit()
        
        return {
            "success": True,
            "message": f"Usuario {username} eliminado exitosamente",
            "deleted_user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")
    finally:
        db.close()

@router.put("/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int,
    current_user: User = Depends(get_superadmin_user)
):
    """
    Activar/Desactivar un usuario (solo SuperAdmin)
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Prevenir que el SuperAdmin se desactive a sí mismo
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="No puedes cambiar tu propio estado")
        
        # Cambiar estado
        user.is_active = not user.is_active
        db.commit()
        
        status = "activado" if user.is_active else "desactivado"
        
        return {
            "success": True,
            "message": f"Usuario {user.username} {status} exitosamente",
            "user_id": user.id,
            "is_active": user.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cambiar estado: {str(e)}")
    finally:
        db.close()

@router.get("/roles")
def get_available_roles():
    """
    Obtener lista de roles disponibles
    """
    return {
        "roles": [
            {
                "value": "USUARIO",
                "label": "Usuario",
                "description": "Solo visualización de repartos",
                "permissions": ["view_repartos"]
            },
            {
                "value": "ADMIN",
                "label": "Administrador",
                "description": "Gestión de repartos y visualización",
                "permissions": ["view_repartos", "close_repartos"]
            },
            {
                "value": "SUPERADMIN",
                "label": "Super Administrador",
                "description": "Control total del sistema",
                "permissions": ["view_repartos", "close_repartos", "manage_users"]
            }
        ]
    }
