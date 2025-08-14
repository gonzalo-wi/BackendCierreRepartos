# Sistema de Logging - Backend Cierre Repartos

## 📋 Descripción General

Este sistema de logging está diseñado para proporcionar **trazabilidad completa** de todas las acciones de usuario y errores técnicos en la aplicación, con **rotación automática** para evitar el colapso de memoria.

## 🏗️ Arquitectura del Sistema

### Tipos de Logs

1. **📊 Logs de Acciones de Usuario** (`user_actions.log`)
   - Registro de todas las acciones realizadas por usuarios
   - Formato JSON estructurado para fácil análisis
   - Incluye: IP, user-agent, timestamps, recursos afectados
   - **Rotación**: Diaria (medianoche) + 50MB máximo
   - **Retención**: 30 días

2. **🚨 Logs de Errores Técnicos** (`technical_errors.log`)
   - Registro de errores, excepciones y advertencias técnicas
   - Incluye stack traces completos y contexto
   - **Rotación**: Por tamaño (20MB por archivo)
   - **Retención**: 10 archivos (200MB total)

3. **📋 Logs Generales de Aplicación** (`application.log`)
   - Información general del funcionamiento de la aplicación
   - Inicio/parada de servicios, configuraciones, etc.
   - **Rotación**: Diaria
   - **Retención**: 7 días

### Ubicación de Archivos

```
/home/gonzalo/Documentos/BackendCierreRepartos/
├── logs/
│   ├── user_actions.log          # Acciones de usuario
│   ├── technical_errors.log      # Errores técnicos
│   ├── application.log           # Logs generales
│   └── archive/                  # Archivos comprimidos antiguos
├── config/
│   └── logging_config.py         # Configuración del sistema
├── utils/
│   └── logging_utils.py          # Utilidades de logging
├── middleware/
│   └── logging_middleware.py     # Middleware para FastAPI
└── scripts/
    ├── monitor_logs.py           # Monitor en tiempo real
    └── clean_logs.py             # Limpieza y mantenimiento
```

## 🚀 Configuración e Integración

### 1. Inicialización en `main.py`

```python
from config.logging_config import setup_application_logging
from middleware.logging_middleware import setup_request_logging

# Inicializar sistema de logging ANTES que todo lo demás
setup_application_logging()

# Configurar middleware de logging para requests HTTP
setup_request_logging(app)
```

### 2. Uso en Endpoints

```python
from utils.logging_utils import log_user_action, log_technical_error
from middleware.logging_middleware import log_endpoint_access

@router.post("/deposits")
@log_endpoint_access("CREATE_DEPOSIT", "deposits")
async def create_deposit(request: Request, deposit_data: DepositCreate):
    try:
        # Log de acción específica
        log_user_action(
            action="CREATE_DEPOSIT",
            resource="deposits",
            resource_id=deposit_data.id,
            request=request,
            extra_data={"amount": deposit_data.amount}
        )
        
        result = await create_deposit_service(deposit_data)
        return result
        
    except Exception as e:
        # Log de error técnico
        log_technical_error(
            e, 
            "create_deposit_endpoint",
            request=request,
            extra_data={"deposit_data": deposit_data.dict()}
        )
        raise
```

## 📊 Funciones Disponibles

### Logging de Acciones de Usuario

```python
log_user_action(
    action="ACTION_NAME",           # Nombre de la acción
    user_id="user123",             # ID del usuario (opcional)
    resource="resource_type",       # Tipo de recurso (deposits, cheques, etc.)
    resource_id="123",             # ID específico del recurso
    request=request_object,         # Objeto Request de FastAPI
    extra_data={"key": "value"},   # Datos adicionales
    success=True                   # Si la acción fue exitosa
)
```

### Logging de Errores Técnicos

```python
# Para errores/excepciones
log_technical_error(
    error=exception_object,
    context="database_connection",
    user_id="user123",
    request=request_object,
    extra_data={"query": "SELECT ..."}
)

# Para advertencias
log_technical_warning(
    message="Conexión lenta detectada",
    context="api_call",
    request=request_object,
    extra_data={"response_time": 5.2}
)
```

## 🔍 Monitoreo y Análisis

### Monitor en Tiempo Real

```bash
# Ver estadísticas de logs
python scripts/monitor_logs.py --action stats

# Ver últimas acciones de usuario
python scripts/monitor_logs.py --action user --lines 50

# Ver últimos errores técnicos
python scripts/monitor_logs.py --action errors --lines 20

# Monitoreo en tiempo real (todas las categorías)
python scripts/monitor_logs.py --action watch

# Monitoreo solo de errores
python scripts/monitor_logs.py --action watch --watch-type errors
```

### Ejemplos de Salida

#### Acciones de Usuario (JSON)
```json
{
    "timestamp": "2025-08-08T14:30:15.123456",
    "level": "INFO",
    "action": "CREATE_DEPOSIT",
    "user_id": "user123",
    "resource": "deposits",
    "resource_id": "456",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "method": "POST",
    "url": "http://localhost:8000/api/deposits",
    "request_id": "abc123-def456-ghi789",
    "success": true,
    "extra_data": {
        "amount": 15000.50,
        "plant": "jumillano"
    }
}
```

#### Errores Técnicos (JSON)
```json
{
    "timestamp": "2025-08-08T14:35:22.987654",
    "level": "ERROR",
    "error_type": "DatabaseConnectionError",
    "error_message": "Unable to connect to database",
    "context": "get_deposits_service",
    "traceback": "Traceback (most recent call last):\n...",
    "request_info": {
        "method": "GET",
        "url": "http://localhost:8000/api/deposits/jumillano",
        "ip_address": "192.168.1.100",
        "request_id": "xyz789-abc123-def456"
    },
    "extra_data": {
        "date": "2025-08-08",
        "identifier": "JUM001"
    }
}
```

## 🧹 Mantenimiento y Limpieza

### Script de Limpieza Automática

```bash
# Ver reporte de estado actual
python scripts/clean_logs.py --action report

# Archivar logs antiguos (más de 7 días)
python scripts/clean_logs.py --action archive --archive-days 7

# Limpiar archivos archivados antiguos (más de 30 días)
python scripts/clean_logs.py --action clean --delete-days 30

# Truncar logs muy grandes (más de 50MB)
python scripts/clean_logs.py --action truncate --max-size-mb 50

# Mantenimiento completo automático
python scripts/clean_logs.py --action full
```

### Configuración de Crontab para Automatización

```bash
# Editar crontab
crontab -e

# Agregar estas líneas para mantenimiento automático:

# Mantenimiento diario a las 2:00 AM
0 2 * * * cd /home/gonzalo/Documentos/BackendCierreRepartos && python scripts/clean_logs.py --action full

# Reporte semanal los lunes a las 9:00 AM
0 9 * * 1 cd /home/gonzalo/Documentos/BackendCierreRepartos && python scripts/monitor_logs.py --action stats
```

## 📈 Ejemplos de Uso en Diferentes Casos

### 1. CRUD de Depósitos

```python
@router.post("/deposits")
async def create_deposit(request: Request, deposit: DepositCreate):
    log_user_action("CREATE_DEPOSIT", resource="deposits", request=request)
    # ... lógica de creación
    
@router.put("/deposits/{deposit_id}")
async def update_deposit(request: Request, deposit_id: int, deposit: DepositUpdate):
    log_user_action("UPDATE_DEPOSIT", resource="deposits", resource_id=str(deposit_id), request=request)
    # ... lógica de actualización

@router.delete("/deposits/{deposit_id}")
async def delete_deposit(request: Request, deposit_id: int):
    log_user_action("DELETE_DEPOSIT", resource="deposits", resource_id=str(deposit_id), request=request)
    # ... lógica de eliminación
```

### 2. Operaciones Financieras

```python
@router.post("/cheques")
async def create_cheque(request: Request, cheque_data: ChequeCreate):
    log_user_action(
        "CREATE_CHEQUE",
        resource="cheques",
        request=request,
        extra_data={
            "amount": cheque_data.importe,
            "bank": cheque_data.banco,
            "deposit_id": cheque_data.deposit_id
        }
    )
    # ... lógica
```

### 3. Integración con APIs Externas

```python
async def sync_with_external_api(date: str, request: Request = None):
    try:
        log_user_action("SYNC_EXTERNAL_API", resource="sync", request=request, extra_data={"date": date})
        
        result = await call_external_api(date)
        
        log_user_action("SYNC_EXTERNAL_API_SUCCESS", resource="sync", request=request, 
                       extra_data={"date": date, "records": len(result)})
        return result
        
    except Exception as e:
        log_technical_error(e, "external_api_sync", request=request, extra_data={"date": date})
        raise
```

## 🔧 Configuración Avanzada

### Personalizar Configuración de Rotación

En `config/logging_config.py`:

```python
# Modificar parámetros de rotación
handler = logging.handlers.TimedRotatingFileHandler(
    filename=self.user_actions_log,
    when='midnight',      # 'H' para horas, 'D' para días, 'midnight' para medianoche
    interval=1,           # Cada cuánto rotar
    backupCount=60,       # Cuántos archivos mantener (30 = 1 mes, 60 = 2 meses)
    encoding='utf-8'
)
```

### Agregar Nuevos Tipos de Logs

```python
def _setup_custom_logger(self):
    """Configura un logger personalizado"""
    logger = logging.getLogger('custom_operations')
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    handler = logging.handlers.RotatingFileHandler(
        filename=self.logs_dir / "custom_operations.log",
        maxBytes=30 * 1024 * 1024,  # 30MB
        backupCount=5,
        encoding='utf-8'
    )
    
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
```

## 🚨 Alertas y Notificaciones

### Monitor de Errores Críticos

```python
def check_critical_errors():
    """Revisa errores críticos en los últimos 5 minutos"""
    # Implementar lógica para enviar alertas por email/Slack
    # cuando se detecten errores críticos
    pass
```

## 📋 Mejores Prácticas

1. **🎯 Ser Específico**: Usa nombres de acción descriptivos (`CREATE_DEPOSIT_JUMILLANO` mejor que `CREATE`)

2. **📊 Incluir Contexto**: Siempre agrega `extra_data` relevante para análisis posterior

3. **🔍 Request ID**: El sistema automáticamente genera IDs únicos para cada request

4. **⚡ No Bloqueante**: El logging es asíncrono y no afecta el rendimiento

5. **🔒 Datos Sensibles**: Nunca logear passwords, tokens o información sensible

6. **📈 Métricas**: Usar los logs para generar métricas de uso y rendimiento

## 🎯 Casos de Uso Avanzados

### Análisis de Patrones de Uso

```bash
# Encontrar los usuarios más activos
grep "CREATE_DEPOSIT" logs/user_actions.log | jq '.user_id' | sort | uniq -c | sort -nr

# Analizar errores por contexto
grep "ERROR" logs/technical_errors.log | jq '.context' | sort | uniq -c

# Buscar operaciones en un rango de tiempo específico
grep "2025-08-08T14:" logs/user_actions.log | jq '.action' | sort | uniq -c
```

### Dashboard de Monitoreo

Los logs en formato JSON pueden ser fácilmente importados a herramientas como:
- **Grafana** para dashboards visuales
- **ELK Stack** (Elasticsearch, Logstash, Kibana) para análisis avanzado
- **Prometheus** para métricas y alertas

---

## 📞 Soporte

Para consultas sobre el sistema de logging:
- Revisar logs de errores técnicos para diagnóstico
- Usar `monitor_logs.py` para análisis en tiempo real
- Ejecutar `clean_logs.py --action report` para estado del sistema
