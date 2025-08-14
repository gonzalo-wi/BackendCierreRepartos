"""
Utilidades para logging de acciones de usuario y errores técnicos
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request

# Loggers especializados
user_logger = logging.getLogger('user_actions')
error_logger = logging.getLogger('technical_errors')
app_logger = logging.getLogger('app')

class UserActionLogger:
    """
    Logger especializado para acciones de usuario (audit trail)
    """
    
    @staticmethod
    def log_action(
        action: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """
        Registra una acción del usuario
        
        Args:
            action: Descripción de la acción (ej: "CREATE_DEPOSIT", "DELETE_CHEQUE")
            user_id: ID del usuario (si está disponible)
            resource: Tipo de recurso afectado (ej: "deposit", "cheque", "retencion")
            resource_id: ID del recurso específico
            request: Objeto Request de FastAPI para obtener IP, user-agent, etc.
            extra_data: Datos adicionales específicos de la acción
            success: Si la acción fue exitosa o no
        """
        
        # Preparar información de contexto
        context = {
            'action': action,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if user_id:
            context['user_id'] = user_id
            
        if resource:
            context['resource'] = resource
            
        if resource_id:
            context['resource_id'] = str(resource_id)
            
        if request:
            context['ip_address'] = request.client.host if request.client else 'unknown'
            context['user_agent'] = request.headers.get('user-agent', 'unknown')
            context['method'] = request.method
            context['url'] = str(request.url)
            context['request_id'] = getattr(request.state, 'request_id', None)
            
        if extra_data:
            context['extra_data'] = extra_data
        
        # Crear mensaje simple y dejar los datos estructurados en extra
        base_msg = f"ACTION={action} STATUS={'OK' if success else 'FAIL'}"
        if resource:
            base_msg += f" RESOURCE={resource}"
        if resource_id:
            base_msg += f" RESOURCE_ID={resource_id}"

        # Usar API estándar de logging para respetar filtros/niveles
        user_logger.info(base_msg, extra=context)

class TechnicalErrorLogger:
    """
    Logger especializado para errores técnicos
    """
    
    @staticmethod
    def log_error(
        error: Exception,
        context: str,
        user_id: Optional[str] = None,
        request: Optional[Request] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        Registra un error técnico con contexto completo
        
        Args:
            error: La excepción que ocurrió
            context: Contexto donde ocurrió el error (ej: "database_connection", "api_call")
            user_id: ID del usuario si está disponible
            request: Objeto Request de FastAPI
            extra_data: Datos adicionales relevantes al error
        """
        
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        if user_id:
            error_info['user_id'] = user_id
            
        if request:
            error_info['request_info'] = {
                'method': request.method,
                'url': str(request.url),
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get('user-agent', 'unknown'),
                'request_id': getattr(request.state, 'request_id', None)
            }
            
        if extra_data:
            error_info['extra_data'] = extra_data
        
        # Crear mensaje descriptivo
        message = f"Error técnico en {context}: {type(error).__name__} - {str(error)}"
        
        # Crear record con información adicional
        record = error_logger.makeRecord(
            error_logger.name, logging.ERROR, __file__, 0, message, (), (type(error), error, error.__traceback__)
        )
        
        # Agregar información adicional al record
        for key, value in error_info.items():
            setattr(record, key, value)
            
        error_logger.handle(record)
    
    @staticmethod
    def log_warning(
        message: str,
        context: str,
        user_id: Optional[str] = None,
        request: Optional[Request] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        Registra una advertencia técnica
        """
        warning_info = {
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        if user_id:
            warning_info['user_id'] = user_id
            
        if request:
            warning_info['request_info'] = {
                'method': request.method,
                'url': str(request.url),
                'ip_address': request.client.host if request.client else 'unknown'
            }
            
        if extra_data:
            warning_info['extra_data'] = extra_data
        
        full_message = f"Advertencia en {context}: {message}"
        
        record = error_logger.makeRecord(
            error_logger.name, logging.WARNING, __file__, 0, full_message, (), None
        )
        
        for key, value in warning_info.items():
            setattr(record, key, value)
            
        error_logger.handle(record)

# Funciones de conveniencia para usar en toda la aplicación
def log_user_action(action: str, **kwargs):
    """Función de conveniencia para logging de acciones de usuario.
    Acepta alias 'user' -> 'user_id' para compatibilidad retro.
    """
    # Compatibilidad: si alguien pasó 'user', mapear a user_id
    if 'user' in kwargs and 'user_id' not in kwargs:
        kwargs['user_id'] = kwargs.pop('user')
    try:
        UserActionLogger.log_action(action, **kwargs)
    except TypeError as e:
        # Log técnico silencioso para no romper flujo
        app_logger.error(f"log_user_action TypeError: {e} | kwargs={list(kwargs.keys())}")
        # Reintento minimal eliminando claves desconocidas comunes
        safe_keys = {k: v for k, v in kwargs.items() if k in {"user_id","resource","resource_id","request","extra_data","success"}}
        try:
            UserActionLogger.log_action(action, **safe_keys)
        except Exception:
            pass

def log_technical_error(error: Exception, context: str, **kwargs):
    """Función de conveniencia para logging de errores técnicos"""
    TechnicalErrorLogger.log_error(error, context, **kwargs)

def log_technical_warning(message: str, context: str, **kwargs):
    """Función de conveniencia para logging de advertencias técnicas"""
    TechnicalErrorLogger.log_warning(message, context, **kwargs)

# Decorador para logging automático de funciones
def log_function_call(action_name: str = None, log_errors: bool = True):
    """
    Decorador que automáticamente logea las llamadas a funciones
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            function_name = action_name or f"{func.__module__}.{func.__name__}"
            
            try:
                # Log de inicio de función (opcional, solo para funciones críticas)
                app_logger.debug(f"Iniciando función: {function_name}")
                
                result = func(*args, **kwargs)
                
                # Log de éxito
                app_logger.debug(f"Función completada exitosamente: {function_name}")
                
                return result
                
            except Exception as e:
                if log_errors:
                    log_technical_error(e, f"function_call:{function_name}")
                raise
                
        return wrapper
    return decorator
