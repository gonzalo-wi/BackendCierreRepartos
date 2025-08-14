"""
Configuración del sistema de logging para la aplicación
Maneja logs de usuario y errores técnicos con rotación automática
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class JSONFormatter(logging.Formatter):
    """
    Formatter personalizado para crear logs en formato JSON estructurado
    """
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Agregar información adicional si existe
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'action'):
            log_entry['action'] = record.action
        if hasattr(record, 'resource'):
            log_entry['resource'] = record.resource
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

class LoggingConfig:
    """
    Configurador del sistema de logging de la aplicación
    """
    
    def __init__(self, base_dir: str = "/home/gonzalo/Documentos/BackendCierreRepartos"):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Configurar diferentes tipos de logs
        self.user_actions_log = self.logs_dir / "user_actions.log"
        self.technical_errors_log = self.logs_dir / "technical_errors.log"
        self.general_log = self.logs_dir / "application.log"
        
    def setup_logging(self):
        """
        Configura todos los loggers de la aplicación
        """
        # Configuración básica
        logging.basicConfig(level=logging.INFO)
        
        # Logger para acciones de usuario
        self._setup_user_actions_logger()
        
        # Logger para errores técnicos
        self._setup_technical_errors_logger()
        
        # Logger general de la aplicación
        self._setup_general_logger()
    
    def _setup_user_actions_logger(self):
        """
        Configura el logger para acciones de usuario (audit trail)
        """
        logger = logging.getLogger('user_actions')
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        # Handler con rotación por tamaño y tiempo
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.user_actions_log,
            when='midnight',  # Rotar a medianoche
            interval=1,       # Cada día
            backupCount=30,   # Mantener 30 días
            encoding='utf-8'
        )
        
        # También rotar si el archivo supera 50MB
        handler.maxBytes = 50 * 1024 * 1024  # 50MB
        
        # Formato JSON para fácil análisis
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
    def _setup_technical_errors_logger(self):
        """
        Configura el logger para errores técnicos
        """
        logger = logging.getLogger('technical_errors')
        logger.setLevel(logging.ERROR)
        logger.propagate = False
        
        # Handler con rotación por tamaño
        handler = logging.handlers.RotatingFileHandler(
            filename=self.technical_errors_log,
            maxBytes=20 * 1024 * 1024,  # 20MB por archivo
            backupCount=10,              # Mantener 10 archivos (200MB total)
            encoding='utf-8'
        )
        
        # Formato JSON para errores
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
    def _setup_general_logger(self):
        """
        Configura el logger general de la aplicación
        """
        logger = logging.getLogger('app')
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        # Handler con rotación diaria
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.general_log,
            when='midnight',
            interval=1,
            backupCount=7,    # Mantener 1 semana
            encoding='utf-8'
        )
        
        # Formato más simple para logs generales
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # También log a consola en desarrollo
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.addHandler(console_handler)

# Instancia global del configurador
logging_config = LoggingConfig()

def setup_application_logging():
    """
    Función para inicializar el sistema de logging de la aplicación
    Llamar al inicio de la aplicación
    """
    logging_config.setup_logging()
    
    # Log de inicio de la aplicación
    app_logger = logging.getLogger('app')
    app_logger.info("Sistema de logging inicializado correctamente")
    
    return logging_config
