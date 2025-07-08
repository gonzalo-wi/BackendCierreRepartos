# 📋 Documentación API - Backend Cierre Repartos

## 🚀 Base URL
```
http://localhost:8001
```

## 📊 Endpoints para Frontend - Datos desde Base de Datos

### 1. 🏢 **Datos por Planta**
```
GET /api/deposits/db/by-plant?date=2025-07-08
```

**Respuesta JSON:**
```json
{
  "status": "ok",
  "date": "2025-07-08",
  "source": "database",
  "plants": {
    "jumillano": {
      "name": "Jumillano",
      "machines": ["L-EJU-001", "L-EJU-002"],
      "deposits": [
        {
          "deposit_id": "39049819",
          "identifier": "L-EJU-001",
          "user_name": "104, RTO 104",
          "total_amount": 309150,
          "currency_code": "ARS",
          "deposit_type": "Deposito validado",
          "date_time": "2025-07-08T15:49:50",
          "pos_name": "Jumillano I",
          "st_name": "El Jumillano I"
        }
      ],
      "total": 7244250,
      "count": 19
    },
    "plata": {
      "name": "La Plata",
      "machines": ["L-EJU-003"],
      "deposits": [],
      "total": 0,
      "count": 0
    },
    "nafa": {
      "name": "Nafa",
      "machines": ["L-EJU-004"],
      "deposits": [...],
      "total": 1718620,
      "count": 4
    }
  },
  "summary": {
    "jumillano_total": 7244250,
    "jumillano_count": 19,
    "plata_total": 0,
    "plata_count": 0,
    "nafa_total": 1718620,
    "nafa_count": 4,
    "grand_total": 8962870,
    "total_deposits": 23
  }
}
```

### 2. 🏭 **Datos por Máquina**
```
GET /api/deposits/db/by-machine?date=2025-07-08
```

**Respuesta JSON:**
```json
{
  "status": "ok",
  "date": "2025-07-08",
  "source": "database",
  "machines": {
    "L-EJU-001": {
      "identifier": "L-EJU-001",
      "st_name": "El Jumillano I",
      "pos_name": "Jumillano I",
      "deposits": [...],
      "total": 3226150,
      "count": 9
    },
    "L-EJU-002": {
      "identifier": "L-EJU-002",
      "st_name": "El Jumillano II",
      "pos_name": "Jumillano II",
      "deposits": [...],
      "total": 4018100,
      "count": 10
    }
  },
  "summary": {
    "total_machines": 3,
    "grand_total": 8962870,
    "total_deposits": 23
  }
}
```

### 3. 📅 **Fechas Disponibles**
```
GET /api/deposits/db/dates
```

**Respuesta JSON:**
```json
{
  "status": "ok",
  "dates": [
    "2025-07-08",
    "2025-07-07"
  ],
  "count": 2
}
```

### 4. 📈 **Resumen General de BD**
```
GET /api/deposits/db/summary
```

**Respuesta JSON:**
```json
{
  "status": "ok",
  "summary": {
    "total_deposits": 23,
    "total_amount": 8962870.0,
    "unique_machines": 3,
    "date_range": {
      "from": "2025-07-07",
      "to": "2025-07-08"
    }
  },
  "machines": [
    {
      "identifier": "L-EJU-001",
      "st_name": "El Jumillano I",
      "deposit_count": 9,
      "total_amount": 3226150
    }
  ]
}
```

## 🔄 Endpoints de Sincronización Automática

### 5. 🔄 **Sincronización Completa de Hoy**
```
GET /api/deposits/sync
```
- Obtiene datos de hoy desde la API externa
- Los guarda automáticamente en la BD
- Retorna datos + totales

### 6. 📊 **Totales con Auto-sync**
```
GET /api/totals/sync
GET /api/totals/sync?date=2025-07-08
```
- Si es fecha de hoy, sincroniza automáticamente
- Retorna totales actualizados

### 7. 📋 **Depósitos con Auto-sync**
```
GET /api/deposits/all/sync
GET /api/deposits/all/sync?date=2025-07-08
```
- Si es fecha de hoy, sincroniza automáticamente
- Retorna todos los datos

## 💾 Endpoints de Guardado Manual

### 8. 💾 **Guardar Todos los Depósitos**
```
POST /api/deposits/all/save?date=2025-07-08
```

### 9. 💾 **Guardar por Planta**
```
POST /api/deposits/jumillano/save?date=2025-07-08
POST /api/deposits/plata/save?date=2025-07-08
POST /api/deposits/nafa/save?date=2025-07-08
```

## 🎯 Endpoints Recomendados para tu Frontend

### Para Dashboard Principal:
```javascript
// Obtener datos organizados por planta para mostrar en cards
fetch('/api/deposits/db/by-plant?date=2025-07-08')

// Selector de fechas disponibles
fetch('/api/deposits/db/dates')

// Resumen general
fetch('/api/deposits/db/summary')
```

### Para Auto-actualización:
```javascript
// Botón "Actualizar" - sincroniza datos de hoy
fetch('/api/deposits/sync')

// Vista de totales con auto-sync
fetch('/api/totals/sync')
```

### Para Vista Detallada:
```javascript
// Ver depósitos por máquina
fetch('/api/deposits/db/by-machine?date=2025-07-08')
```

## 📄 Endpoints de PDFs (ya existentes)

```
GET /api/pdf/daily-closure?date=2025-07-08
GET /api/pdf/daily-closure/preview?date=2025-07-08
GET /api/pdf/repartos?date=2025-07-08
GET /api/pdf/repartos/preview?date=2025-07-08
GET /api/pdf/repartos/jumillano?date=2025-07-08
GET /api/pdf/repartos/plata?date=2025-07-08
GET /api/pdf/repartos/nafa?date=2025-07-08
```

## 🏥 Endpoints de Salud

```
GET /api/health
GET /api/test-db
```

## 🎨 Ejemplo de Implementación Frontend

### React/JavaScript:
```javascript
// Componente Dashboard
const Dashboard = () => {
  const [selectedDate, setSelectedDate] = useState('2025-07-08');
  const [plants, setPlants] = useState({});
  
  const loadData = async () => {
    const response = await fetch(`/api/deposits/db/by-plant?date=${selectedDate}`);
    const data = await response.json();
    setPlants(data.plants);
  };
  
  const syncToday = async () => {
    await fetch('/api/deposits/sync');
    loadData(); // Recargar datos
  };
  
  return (
    <div>
      <button onClick={syncToday}>🔄 Actualizar Hoy</button>
      {Object.entries(plants).map(([key, plant]) => (
        <div key={key}>
          <h3>{plant.name}</h3>
          <p>Total: ${plant.total.toLocaleString()}</p>
          <p>Depósitos: {plant.count}</p>
        </div>
      ))}
    </div>
  );
};
```

## ✅ Todo Listo para tu Frontend!

Tienes todos los endpoints necesarios para:
- 📊 Mostrar datos por planta/empresa
- 📅 Selector de fechas
- 🔄 Auto-sincronización 
- 💾 Guardado manual
- 📄 Generación de PDFs
- 📈 Resúmenes y estadísticas

¡Tu backend está completamente funcional! 🚀
