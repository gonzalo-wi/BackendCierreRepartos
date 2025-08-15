from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from typing import List
from models.user import User, UserRole
from services.auth_service import auth_service
from auth.dependencies import get_current_user, get_superadmin_user, get_any_user
from schemas.auth_schemas import (
    LoginRequest, LoginResponse, UserCreate, UserResponse, 
    UserUpdate, ChangePasswordRequest, MessageResponse,
    UserListResponse, CurrentUserResponse
)

# Importar utilidades de logging
from utils.logging_utils import log_user_action, log_technical_error, log_technical_warning
from middleware.logging_middleware import log_endpoint_access

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/login", response_model=LoginResponse)
def login(request: Request, login_data: LoginRequest):
    """
    Autenticar usuario y obtener token JWT
    """
    try:
        # Log del intento de login
        log_user_action(
            action="ATTEMPT_LOGIN",
            resource="authentication",
            request=request,
            extra_data={
                "username": login_data.username,
                "attempt_time": "now"
            }
        )
        
        result = auth_service.login(login_data.username, login_data.password)
        
        # Log de login exitoso
        log_user_action(
            action="LOGIN_SUCCESS",
            user_id=login_data.username,
            resource="authentication", 
            request=request,
            success=True,
            extra_data={
                "username": login_data.username,
                "user_role": result.get("user", {}).get("role", "unknown")
            }
        )
        
        return result
        
    except HTTPException as e:
        # Log de login fallido
        log_user_action(
            action="LOGIN_FAILED",
            resource="authentication",
            request=request,
            success=False,
            extra_data={
                "username": login_data.username,
                "error_code": e.status_code,
                "error_detail": str(e.detail)
            }
        )
        
        # Log técnico del error
        log_technical_warning(
            f"Login fallido para usuario {login_data.username}: {e.detail}",
            "authentication_failed",
            request=request,
            extra_data={"username": login_data.username, "status_code": e.status_code}
        )
        raise
        
    except Exception as e:
        # Log de error técnico
        log_technical_error(
            e,
            "login_endpoint", 
            request=request,
            extra_data={"username": login_data.username}
        )
        
        # Log de login fallido por error del sistema
        log_user_action(
            action="LOGIN_SYSTEM_ERROR", 
            resource="authentication",
            request=request,
            success=False,
            extra_data={
                "username": login_data.username,
                "error_type": type(e).__name__
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el proceso de login: {str(e)}"
        )

@router.get("/me", response_model=CurrentUserResponse)
@log_endpoint_access("GET_USER_INFO", "authentication")
def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)):
    """
    Obtener información del usuario actual
    """
    try:
        # Log de consulta de información de usuario
        log_user_action(
            action="GET_USER_INFO",
            user_id=current_user.username,
            resource="user_profile",
            request=request,
            success=True,
            extra_data={
                "user_id": current_user.id,
                "username": current_user.username,
                "role": current_user.role.value
            }
        )
        
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.value,
            "permissions": {
                "can_view_repartos": current_user.can_view_repartos(),
                "can_close_repartos": current_user.can_close_repartos(),
                "can_manage_users": current_user.can_manage_users()
            }
        }
        
    except Exception as e:
        log_technical_error(
            e,
            "get_user_info_endpoint",
            user_id=current_user.username if current_user else None,
            request=request
        )
        raise

@router.post("/change-password", response_model=MessageResponse)
def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cambiar la contraseña del usuario actual
    """
    # Verificar contraseña actual
    if not current_user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña
    from database import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        user.set_password(password_data.new_password)
        db.commit()
        
        return MessageResponse(message="Contraseña actualizada exitosamente")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar contraseña: {str(e)}"
        )
    finally:
        db.close()

# === ENDPOINTS SOLO PARA SUPERADMIN ===

@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_superadmin_user)
):
    """
    Crear un nuevo usuario (solo SuperAdmin)
    """
    try:
        new_user = auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role,
            created_by_id=current_user.id
        )
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role.value,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login=new_user.last_login
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {str(e)}"
        )

@router.get("/users", response_model=UserListResponse)
def get_all_users(current_user: User = Depends(get_superadmin_user)):
    """
    Obtener lista de todos los usuarios (solo SuperAdmin)
    """
    try:
        users = auth_service.get_all_users()
        user_responses = [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login
            )
            for user in users
        ]
        
        return UserListResponse(users=user_responses, total=len(user_responses))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuarios: {str(e)}"
        )

@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(get_superadmin_user)
):
    """
    Actualizar el rol de un usuario (solo SuperAdmin)
    """
    try:
        updated_user = auth_service.update_user_role(user_id, new_role)
        
        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            full_name=updated_user.full_name,
            role=updated_user.role.value,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar rol: {str(e)}"
        )

@router.put("/users/{user_id}/deactivate", response_model=MessageResponse)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_superadmin_user)
):
    """
    Desactivar un usuario (solo SuperAdmin)
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivarte a ti mismo"
        )
    
    try:
        auth_service.deactivate_user(user_id)
        return MessageResponse(message="Usuario desactivado exitosamente")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desactivar usuario: {str(e)}"
        )

@router.get("/roles")
def get_available_roles():
    """
    Obtener lista de roles disponibles
    """
    return {
        "roles": [
            {"value": "USUARIO", "label": "Usuario", "description": "Solo visualización"},
            {"value": "ADMIN", "label": "Administrador", "description": "Gestión de repartos"},
            {"value": "SUPERADMIN", "label": "Super Administrador", "description": "Control total del sistema"}
        ]
    }

# Endpoint para verificar token (útil para el frontend)
@router.post("/verify-token")
def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verificar si el token es válido
    """
    return {
        "valid": True,
        "user": current_user.to_dict()
    }
