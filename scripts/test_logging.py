#!/usr/bin/env python3
"""
Script de prueba para verificar que el sistema de logging esté funcionando
correctamente con los endpoints implementados.
"""

import requests
import json
import time
from datetime import datetime

# Configuración de la API
BASE_URL = "http://localhost:8000/api"
HEADERS = {"Content-Type": "application/json"}

def test_logging_system():
    """
    Ejecuta pruebas de los endpoints con logging implementado
    """
    print("🧪 Iniciando pruebas del sistema de logging...")
    print("=" * 60)
    
    # Test 1: Login (debe fallar sin credenciales válidas)
    print("\n1️⃣  Probando endpoint de login...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": "test_user",
                "password": "wrong_password"
            },
            headers=HEADERS
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Sincronización (debe fallar sin datos válidos)
    print("\n2️⃣  Probando endpoint de sincronización...")
    try:
        response = requests.post(
            f"{BASE_URL}/sync/deposits/jumillano?date=2025-08-08",
            headers=HEADERS
        )
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Crear cheque (debe fallar sin autenticación)
    print("\n3️⃣  Probando endpoint de crear cheque...")
    try:
        response = requests.post(
            f"{BASE_URL}/cheques-retenciones/cheques",
            json={
                "deposit_id": "TEST123",
                "importe": 5000.0,
                "banco": "Banco Test",
                "nro_cheque": "123456"
            },
            headers=HEADERS
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Crear retención (debe fallar sin autenticación)
    print("\n4️⃣  Probando endpoint de crear retención...")
    try:
        response = requests.post(
            f"{BASE_URL}/cheques-retenciones/retenciones",
            json={
                "deposit_id": "TEST123",
                "importe": 1000.0,
                "concepto": "RIB",
                "nro_retencion": 789
            },
            headers=HEADERS
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas. Verificar logs en:")
    print("   📊 Acciones de usuario: logs/user_actions.log")
    print("   🚨 Errores técnicos: logs/technical_errors.log") 
    print("   📋 Logs generales: logs/application.log")
    print("\n💡 Para ver los logs en tiempo real:")
    print("   python3 scripts/monitor_logs.py --action watch")

def check_log_files():
    """Verificar que los archivos de log existen y tienen contenido"""
    import os
    
    print("\n🔍 Verificando archivos de log...")
    
    log_files = [
        "logs/user_actions.log",
        "logs/technical_errors.log", 
        "logs/application.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"   ✅ {log_file}: {size} bytes")
        else:
            print(f"   ❌ {log_file}: No existe")

if __name__ == "__main__":
    print("🚀 Sistema de Logging - Pruebas de Integración")
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar archivos de log
    check_log_files()
    
    # Ejecutar pruebas
    test_logging_system()
    
    # Esperar un momento para que se procesen los logs
    print("\n⏳ Esperando 2 segundos para que se procesen los logs...")
    time.sleep(2)
    
    # Verificar archivos de log después de las pruebas
    check_log_files()
    
    print("\n🎉 ¡Pruebas completadas!")
    print("\n📋 Comandos útiles:")
    print("   Ver estadísticas: python3 scripts/monitor_logs.py --action stats")
    print("   Ver errores: python3 scripts/monitor_logs.py --action errors")
    print("   Monitor en vivo: python3 scripts/monitor_logs.py --action watch")
