"""Middleware de logging: agrega request_id y loguea inicio/fin/errores incluyendo usuario JWT si existe."""

import time
import uuid
import logging
import os
from typing import Callable, Optional
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

try:
    import jwt  # PyJWT
except ImportError:  # Si no está instalado, seguimos sin decodificar
    jwt = None

from utils.logging_utils import log_user_action, log_technical_error

app_logger = logging.getLogger('app')

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Intentar extraer usuario antes de procesar
        username, user_id = self._extract_user_from_authorization(request)
        if username:
            request.state.username = username
        if user_id:
            request.state.user_id = user_id

        start_time = time.time()
        client_ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('user-agent', 'unknown')

        app_logger.info(
            f"REQUEST_START - ID:{request_id} Method:{request.method} URL:{request.url} IP:{client_ip} User:{username or 'anonymous'} UA:{user_agent[:80]}"
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            app_logger.info(
                f"REQUEST_END - ID:{request_id} Status:{response.status_code} Time:{process_time:.3f}s Method:{request.method} URL:{request.url} User:{getattr(request.state,'username',username) or 'anonymous'}"
            )
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Process-Time'] = f"{process_time:.3f}"
            return response
        except Exception as e:
            process_time = time.time() - start_time
            app_logger.error(
                f"REQUEST_ERROR - ID:{request_id} User:{getattr(request.state,'username','anonymous')} Err:{type(e).__name__}:{str(e)} Time:{process_time:.3f}s Method:{request.method} URL:{request.url}"
            )
            log_technical_error(
                e,
                "http_request",
                request=request,
                extra_data={"request_id": request_id, "process_time": process_time}
            )
            raise

    def _extract_user_from_authorization(self, request: Request) -> tuple[Optional[str], Optional[str]]:
        auth_header = request.headers.get('authorization') or request.headers.get('Authorization')
        if not auth_header or ' ' not in auth_header:
            return None, None
        scheme, token = auth_header.split(' ', 1)
        if scheme.lower() != 'bearer' or not token or not jwt:
            return None, None
        secret_key = os.getenv("JWT_SECRET_KEY", "mi_clave_secreta_jwt_para_cierre_repartos_2025_desarrollo")
        try:
            decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
            return (decoded.get('sub') or decoded.get('username'), decoded.get('user_id'))
        except Exception:
            return None, None


def setup_request_logging(app: FastAPI):
    app.add_middleware(LoggingMiddleware)

    @app.middleware("http")
    async def _pass(request: Request, call_next):  # conserva compatibilidad si se quiere añadir algo luego
        return await call_next(request)


def log_endpoint_access(action_name: str, resource_type: str = None):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = next((a for a in args if isinstance(a, Request)), kwargs.get('request')) if (args or kwargs) else None
            try:
                result = await func(*args, **kwargs)
                log_user_action(
                    action=action_name,
                    resource=resource_type,
                    request=request,
                    success=True,
                    extra_data={"endpoint": str(getattr(request, 'url', ''))}
                )
                return result
            except Exception as e:
                log_user_action(
                    action=action_name,
                    resource=resource_type,
                    request=request,
                    success=False,
                    extra_data={"error": str(e)}
                )
                raise
        return wrapper
    return decorator
