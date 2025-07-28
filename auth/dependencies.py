from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from models.user import User, UserRole
from services.auth_service import auth_service

# Configurar Bearer token
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Obtiene el usuario actual del token JWT"""
    token = credentials.credentials
    
    # Verificar token
    payload = auth_service.verify_token(token)
    username: str = payload.get("sub")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener usuario
    user = auth_service.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def require_role(required_role: UserRole):
    """Decorator para requerir un rol específico"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_permission(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol {required_role.value} o superior"
            )
        return current_user
    return role_checker

# Dependencias específicas por rol
def get_superadmin_user(current_user: User = Depends(get_current_user)) -> User:
    """Solo SuperAdmin"""
    if not current_user.can_manage_users():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de SuperAdmin"
        )
    return current_user

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Admin o SuperAdmin"""
    if not current_user.can_close_repartos():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de Admin o superior"
        )
    return current_user

def get_any_user(current_user: User = Depends(get_current_user)) -> User:
    """Cualquier usuario autenticado"""
    return current_user

# Dependencia opcional (para endpoints públicos con info adicional si está logueado)
def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Obtiene el usuario actual si está autenticado, sino None"""
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
