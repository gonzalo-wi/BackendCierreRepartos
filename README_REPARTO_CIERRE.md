# Sistema de Cierre de Repartos

## Descripción General

Este sistema permite el cierre automático de repartos mediante integración con API SOAP. Los repartos con estado "LISTO" se envían al sistema externo y se marcan como "ENVIADO" con fecha y hora de envío.

## Características Principales

✅ **Filtrado por fecha específica**: Procesa solo los repartos del día seleccionado
✅ **Integración SOAP**: Envía repartos al sistema externo mediante API SOAP
✅ **Reintentos automáticos**: Sistema de reintentos con backoff exponencial
✅ **Rastreo de estados**: Actualiza automáticamente el estado y fecha de envío
✅ **Modo simulación**: Permite pruebas sin enviar a producción
✅ **Soporte para cheques y retenciones**: Incluye todos los datos financieros

## Estructura de Archivos

```
services/
├── reparto_cierre_service.py    # Servicio principal de cierre
routers/
├── reparto_cierre.py            # Endpoints REST API
models/
├── deposit.py                   # Modelo con campo fecha_envio
├── cheque_retencion.py         # Modelos de cheques y retenciones
```

## Endpoints Disponibles

### 1. Obtener Repartos Listos
```http
GET /reparto-cierre/repartos-listos?fecha=2025-07-24
```
**Parámetros:**
- `fecha` (opcional): Formato YYYY-MM-DD para filtrar por día específico

**Respuesta:**
```json
{
  "success": true,
  "total_repartos": 15,
  "fecha_filtro": "2025-07-24",
  "repartos": [...],
  "message": "Se encontraron 15 repartos listos para enviar para el día 2025-07-24"
}
```

### 2. Cerrar Repartos (Síncrono)
```http
POST /reparto-cierre/cerrar-repartos
Content-Type: application/json

{
  "fecha_especifica": "2025-07-24",
  "max_reintentos": 3,
  "delay_entre_envios": 1.0,
  "modo_test": true
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Proceso completado. 15 enviados, 0 errores",
  "fecha_procesada": "2025-07-24",
  "total_repartos": 15,
  "enviados": 15,
  "errores": 0,
  "resultados": [...],
  "timestamp": "2025-07-25T14:46:07.123456"
}
```

### 3. Cerrar Repartos (Asíncrono)
```http
POST /reparto-cierre/cerrar-repartos-async
```
Procesa en background para evitar timeouts en el frontend.

### 4. Resumen por Fechas
```http
GET /reparto-cierre/resumen-por-fechas
```
**Respuesta:**
```json
{
  "success": true,
  "resumen": {
    "total_fechas": 10,
    "total_repartos_listos": 877,
    "fechas": [
      {
        "fecha": "2025-07-24",
        "fecha_display": "24/07/2025",
        "total_repartos": 15,
        "plantas": {
          "jumillano": 15
        }
      }
    ]
  }
}
```

### 5. Estado General
```http
GET /reparto-cierre/estado-repartos
```

## Configuración de Producción

### 1. Activar Modo Producción

En `services/reparto_cierre_service.py`, línea ~175:

```python
# TODO: Descomentar cuando esté listo para producción
response = requests.post(
    self.soap_url,
    data=soap_envelope,
    headers=headers,
    timeout=30
)

# SIMULACIÓN para desarrollo - eliminar en producción
# print("⚠️ MODO SIMULACIÓN - No se envía a producción")
# response_mock = type('Response', (), {
#     'status_code': 200,
#     'text': '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:airtech="http://airtech-it.com.ar/"><soap:Body><airtech:reparto_cerrarResponse><airtech:reparto_cerrarResult>OK</airtech:reparto_cerrarResult></airtech:reparto_cerrarResponse></soap:Body></soap:Envelope>'
# })()
# 
# response = response_mock
# FIN SIMULACIÓN
```

### 2. Configurar URL del Servicio SOAP

En `services/reparto_cierre_service.py`, línea ~18:

```python
def __init__(self):
    self.soap_url = "http://your-production-server.com/Service1.asmx"  # URL real
    self.soap_namespace = "http://airtech-it.com.ar/"
```

### 3. Mapeo de Plantas

Actualizar el mapeo de identificadores a plantas según tu configuración:

```python
planta_mapping = {
    'L-EJU-001': 'jumillano',
    'L-EJU-002': 'jumillano', 
    'L-EJU-003': 'plata',
    'L-EJU-004': 'nafa'
    # Agregar más según necesidad
}
```

## Estados de Repartos

- **PENDIENTE**: Reparto recién creado
- **LISTO**: Reparto listo para enviar (puede ser procesado)
- **ENVIADO**: Reparto enviado exitosamente al sistema externo

## Flujo de Datos SOAP

### Envelope de Envío
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <reparto_cerrar xmlns="http://airtech-it.com.ar/">
      <idreparto>39146308</idreparto>
      <fecha>24/07/2025</fecha>
      <ajustar_envases>0</ajustar_envases>
      <efectivo_importe>184017</efectivo_importe>
      <retenciones>[{...}]</retenciones>
      <cheques>[{...}]</cheques>
      <usuario>SISTEMA</usuario>
    </reparto_cerrar>
  </soap12:Body>
</soap12:Envelope>
```

### Respuesta Esperada
```xml
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:airtech="http://airtech-it.com.ar/">
  <soap:Body>
    <airtech:reparto_cerrarResponse>
      <airtech:reparto_cerrarResult>OK</airtech:reparto_cerrarResult>
    </airtech:reparto_cerrarResponse>
  </soap:Body>
</soap:Envelope>
```

## Ejemplo de Uso

### Frontend JavaScript
```javascript
// Obtener fechas disponibles
const resumen = await fetch('/reparto-cierre/resumen-por-fechas').then(r => r.json());

// Mostrar selector de fecha al usuario
const fechaSeleccionada = '2025-07-24';

// Cerrar repartos del día seleccionado
const resultado = await fetch('/reparto-cierre/cerrar-repartos', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    fecha_especifica: fechaSeleccionada,
    max_reintentos: 3,
    delay_entre_envios: 1.0,
    modo_test: false  // Cambiar a false en producción
  })
});

console.log('Repartos enviados:', resultado.enviados);
```

## Consideraciones de Seguridad

1. **Validación de fechas**: Todas las fechas se validan en formato YYYY-MM-DD
2. **Transacciones de BD**: Rollback automático en caso de errores
3. **Timeouts**: Configurables para evitar bloqueos
4. **Logs detallados**: Para auditoría y debugging

## Monitoreo y Logs

El sistema genera logs detallados:
- ✅ Envíos exitosos
- ❌ Errores y reintentos
- 📊 Resúmenes de procesamiento
- ⏰ Timestamps de todas las operaciones

## Soporte

Para preguntas o problemas, revisar:
1. Logs del servidor
2. Estado de la base de datos
3. Conectividad con el servicio SOAP
4. Configuración de URLs y credenciales
