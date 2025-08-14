#!/bin/bash
"""
Script de inicio rápido para el sistema de logging
Configura y verifica que todo esté funcionando correctamente
"""

echo "🚀 Configurando Sistema de Logging - Backend Cierre Repartos"
echo "============================================================="

# Crear directorios necesarios
echo "📁 Creando directorios de logs..."
mkdir -p logs/archive
echo "✅ Directorios creados"

# Verificar permisos
echo "🔒 Verificando permisos..."
chmod +x scripts/*.py
echo "✅ Permisos configurados"

# Ejecutar test básico del sistema
echo "🧪 Ejecutando test básico..."
python3 -c "
import sys
sys.path.append('.')
try:
    from config.logging_config import setup_application_logging
    setup_application_logging()
    print('✅ Sistema de logging configurado correctamente')
    
    from utils.logging_utils import log_user_action, log_technical_error
    print('✅ Utilidades de logging cargadas')
    
    import logging
    logger = logging.getLogger('app')
    logger.info('Test de logging inicial - Sistema funcionando')
    print('✅ Log de prueba generado')
    
except Exception as e:
    print(f'❌ Error en configuración: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "🎉 Sistema de logging configurado exitosamente!"
    echo ""
    echo "📋 Comandos disponibles:"
    echo "  • Ver estado:      python scripts/monitor_logs.py --action stats"
    echo "  • Monitor tiempo real: python scripts/monitor_logs.py --action watch"
    echo "  • Ver errores:     python scripts/monitor_logs.py --action errors"
    echo "  • Limpiar logs:    python scripts/clean_logs.py --action full"
    echo ""
    echo "📖 Ver documentación completa: docs/LOGGING_SYSTEM.md"
else
    echo "❌ Error en la configuración inicial"
    exit 1
fi
