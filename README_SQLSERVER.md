# Migración a SQL Server - El Jumillano

## 🎉 ¡Migración Completada!

El sistema ahora está configurado para funcionar con **SQL Server** en lugar de SQLite, preparándolo para producción.

## 📋 Configuración Actual

- **Servidor SQL Server**: `192.168.0.234:1433`
- **Base de Datos**: `PAC`
- **Usuario**: `h2o`
- **Driver**: `pymssql` (sin dependencias ODBC)

## 🔧 Scripts Disponibles

### 1. **Cambiar Base de Datos**
```bash
# Usar SQL Server (Producción)
./switch_database.sh sqlserver

# Usar SQLite (Desarrollo)
./switch_database.sh sqlite
```

### 2. **Probar Conexión**
```bash
# Verificar conectividad a SQL Server
python test_sqlserver_connection.py
```

### 3. **Configurar SQL Server desde Cero**
```bash
# Solo crear tablas y usuario admin
python setup_sqlserver.py
```

## 🚀 Iniciar el Servidor

```bash
# Cargar variables de entorno y iniciar
source .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔑 Credenciales Iniciales

- **Usuario**: `superadmin`
- **Contraseña**: `admin123` ⚠️ **¡CAMBIAR INMEDIATAMENTE!**

## 📊 Estructura de Base de Datos

### Tablas Creadas
- ✅ `users` - Usuarios del sistema
- ✅ `deposits` - Depósitos principales  
- ✅ `cheques` - Cheques asociados
- ✅ `retenciones` - Retenciones asociadas
- ✅ `daily_totals` - Totales diarios por planta

### Mejoras Implementadas
- ✅ **Campos con longitud específica** (compatible con SQL Server)
- ✅ **Conversión automática de fechas** (YYYY-MM-DD → dd/MM/yyyy)
- ✅ **Tolerancia configurable** (actualmente $10,000)
- ✅ **Estados de depósito mejorados** (LISTO/PENDIENTE/ENVIADO)

## 🔄 Flujo de Trabajo

### Para Desarrollo
```bash
./switch_database.sh sqlite
# Usar SQLite local para desarrollo
```

### Para Producción
```bash
./switch_database.sh sqlserver  
# Usar SQL Server en 192.168.0.234
```

## ⚠️ Notas Importantes

1. **Datos Existentes**: Las tablas están vacías. El sistema empezará desde cero.
2. **Migración Manual**: Si necesitas datos de SQLite, deberás migrarlos manualmente.
3. **Formato de Fechas**: Los cheques ahora usan formato dd/MM/yyyy automáticamente.
4. **Conectividad**: Verifica que el puerto 1433 esté accesible desde tu red.

## 🐛 Resolución de Problemas

### Error de Conexión
```bash
# Verificar conectividad
python test_sqlserver_connection.py
```

### Tablas No Creadas
```bash
# Recrear tablas
python setup_sqlserver.py
```

### Cambiar a SQLite Temporalmente
```bash
./switch_database.sh sqlite
# Para desarrollar sin conectividad SQL Server
```

## 📞 Soporte

- **Servidor**: SQL Server 2019 RTM
- **IP**: 192.168.0.234
- **Puerto**: 1433  
- **Base**: PAC

---
**✨ ¡El sistema está listo para producción con SQL Server!**
