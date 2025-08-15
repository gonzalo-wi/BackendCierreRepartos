#!/bin/bash

# Script para cambiar entre SQLite (desarrollo) y SQL Server (producción)

echo "🔄 Configurador de Base de Datos - El Jumillano"
echo "================================================"
echo

case "$1" in
    "sqlserver"|"production"|"prod")
        echo "🏢 Configurando SQL Server (Producción)..."
        export DB_TYPE=sqlserver
        echo "export DB_TYPE=sqlserver" > .env
        echo "✅ Configurado para usar SQL Server"
        echo "📊 Servidor: 192.168.0.234"
        echo "🗄️ Base de datos: PAC"
        ;;
    "sqlite"|"development"|"dev")
        echo "💻 Configurando SQLite (Desarrollo)..."
        export DB_TYPE=sqlite
        echo "export DB_TYPE=sqlite" > .env
        echo "✅ Configurado para usar SQLite"
        echo "📁 Archivo: deposits.db"
        ;;
    *)
        echo "❓ Uso: $0 [sqlserver|sqlite]"
        echo
        echo "Opciones:"
        echo "  sqlserver, production, prod - Usar SQL Server (Producción)"
        echo "  sqlite, development, dev    - Usar SQLite (Desarrollo)"
        echo
        echo "Configuración actual:"
        if [ -f .env ]; then
            cat .env
        else
            echo "DB_TYPE no configurado"
        fi
        exit 1
        ;;
esac

echo
echo "🔄 Para aplicar los cambios, reinicia el servidor FastAPI"
echo "📋 Comando: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
