# Endpoints de Cheques y Retenciones

## 🏗️ **Estructura implementada**

### **Modelos actualizados:**
- ✅ [`Deposit`](models/deposit.py) - Tiene relaciones con cheques y retenciones
- ✅ [`Cheque`](models/cheque_retencion.py) - Modelo completo para SOAP
- ✅ [`Retencion`](models/cheque_retencion.py) - Modelo completo para SOAP

### **Endpoints disponibles:**

## 📋 **CHEQUES**

### GET `/api/deposits/{deposit_id}/cheques`
Obtiene todos los cheques de un depósito
```json
{
  "success": true,
  "deposit_id": "DEP123",
  "cheques": [
    {
      "id": 1,
      "numero": "001234",
      "banco": "Banco Nación",
      "importe": 5000,
      "fecha_cobro": "15/08/2025"
    }
  ],
  "total_cheques": 1
}
```

### POST `/api/deposits/{deposit_id}/cheques`
Crea un nuevo cheque
```json
// Request body:
{
  "numero": "001234",
  "banco": "Banco Nación", 
  "importe": 5000,
  "fecha_cobro": "15/08/2025"  // Opcional
}
```

### PUT `/api/deposits/{deposit_id}/cheques/{cheque_id}`
Actualiza un cheque existente
```json
// Request body (todos los campos opcionales):
{
  "numero": "001235",
  "banco": "Banco Provincia",
  "importe": 5500,
  "fecha_cobro": "16/08/2025"
}
```

### DELETE `/api/deposits/{deposit_id}/cheques/{cheque_id}`
Elimina un cheque

---

## 📋 **RETENCIONES**

### GET `/api/deposits/{deposit_id}/retenciones`
Obtiene todas las retenciones de un depósito
```json
{
  "success": true,
  "deposit_id": "DEP123",
  "retenciones": [
    {
      "id": 1,
      "tipo": "IIBB",
      "numero": "R001234",
      "importe": 1000,
      "concepto": "RIB"
    }
  ],
  "total_retenciones": 1
}
```

### POST `/api/deposits/{deposit_id}/retenciones`
Crea una nueva retención
```json
// Request body:
{
  "tipo": "IIBB",
  "numero": "R001234",
  "importe": 1000,
  "concepto": "RIB"  // Opcional
}
```

### PUT `/api/deposits/{deposit_id}/retenciones/{retencion_id}`
Actualiza una retención existente
```json
// Request body (todos los campos opcionales):
{
  "tipo": "Ganancias",
  "numero": "R001235", 
  "importe": 1200,
  "concepto": "RIB"
}
```

### DELETE `/api/deposits/{deposit_id}/retenciones/{retencion_id}`
Elimina una retención

---

## 📋 **DEPÓSITOS CON DETALLES**

### GET `/api/deposits/{deposit_id}/details`
Obtiene un depósito con todos sus cheques y retenciones
```json
{
  "success": true,
  "deposit": {
    "deposit_id": "DEP123",
    "user_name": "42, RTO 042",
    "total_amount": 10000,
    "deposit_esperado": 10000,
    "estado": "LISTO",
    "cheques": [...],
    "retenciones": [...],
    "total_cheques": 2,
    "total_retenciones": 1
  }
}
```

---

## 🔄 **Integración con envío de repartos**

Cuando se envía un reparto (POST `/api/reparto-cierre/cerrar-repartos`):

1. ✅ Se obtienen automáticamente todos los **cheques** y **retenciones** del depósito
2. ✅ Se formatean correctamente para el **SOAP API**
3. ✅ Se incluyen en el XML de envío
4. ✅ El estado del depósito se actualiza a **"ENVIADO"** si el envío es exitoso

---

## 🔧 **Notas técnicas**

### **Mapeo de campos Frontend ↔ Base de datos:**
- `numero` (frontend) ↔ `nro_cheque` (BD)
- `fecha_cobro` (frontend) ↔ `fecha` (BD)
- `numero` (retención frontend) ↔ `nro_retencion` (BD)

### **Campos automáticos en BD:**
- `nrocta`, `concepto`, `sucursal`, `localidad`, `nro_cuenta`, `titular` se llenan automáticamente
- `fecha` de retención se establece automáticamente si no se proporciona

### **Autenticación:**
- Todos los endpoints requieren usuario autenticado (`get_any_user`)

---

## 🚀 **Para el frontend:**

1. **Listar depósitos** con `/api/deposits/db/by-plant?date=2025-08-07`
2. **Ver detalles completos** con `/api/deposits/{deposit_id}/details`  
3. **Agregar cheques/retenciones** con POST a los endpoints correspondientes
4. **Enviar repartos** con POST `/api/reparto-cierre/cerrar-repartos` (incluirá automáticamente cheques y retenciones)

¡El sistema está completamente funcional! 🎉
