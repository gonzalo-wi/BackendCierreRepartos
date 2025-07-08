#!/bin/bash
"""
Script para configurar cron job para sincronización automática
"""

echo "🔧 Configurando sincronización automática con cron"

# Ruta del script
SCRIPT_PATH="/home/gonzalo/Documentos/BackendCierreRepartos/scripts/sync_deposits.py"
PYTHON_PATH="/home/gonzalo/Documentos/BackendCierreRepartos/venv/bin/python"

# Crear entrada de cron
CRON_ENTRY="# Sincronización automática de depósitos
0 */4 * * * cd /home/gonzalo/Documentos/BackendCierreRepartos && $PYTHON_PATH $SCRIPT_PATH >> /home/gonzalo/Documentos/BackendCierreRepartos/logs/sync.log 2>&1"

echo "📋 Entrada de cron que se agregará:"
echo "$CRON_ENTRY"
echo ""

# Crear directorio de logs si no existe
mkdir -p /home/gonzalo/Documentos/BackendCierreRepartos/logs

echo "⚙️ Para agregar esta tarea a cron, ejecuta:"
echo "crontab -e"
echo ""
echo "Y agrega esta línea:"
echo "$CRON_ENTRY"
echo ""
echo "📅 Esto ejecutará la sincronización cada 4 horas"
echo "🕐 Horarios: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00"
echo ""
echo "📝 Los logs se guardarán en: /home/gonzalo/Documentos/BackendCierreRepartos/logs/sync.log"
