#!/usr/bin/env python3
"""
Script de verificación para el sistema de cierre de repartos
Verifica que todo esté listo para producción
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8001"

def test_server_status():
    """Verifica que el servidor esté funcionando"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor FastAPI funcionando")
            return True
        else:
            print(f"❌ Servidor responde con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False

def test_soap_connection():
    """Verifica conectividad con el servidor SOAP"""
    try:
        # Login como SuperAdmin
        login_response = requests.post(f"{BASE_URL}/api/fix/login", 
                                     json={"username": "superadmin", "password": "admin123"})
        
        if login_response.status_code != 200:
            print("❌ No se puede hacer login como SuperAdmin")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Probar conexión SOAP
        soap_response = requests.post(f"{BASE_URL}/api/production-control/test-connection",
                                    headers=headers)
        
        if soap_response.status_code == 200:
            result = soap_response.json()
            if result["success"]:
                print("✅ Conexión SOAP funcionando")
                return True
            else:
                print(f"❌ Problema con SOAP: {result['message']}")
                return False
        else:
            print(f"❌ Error al probar SOAP: {soap_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error probando conexión SOAP: {e}")
        return False

def check_production_mode():
    """Verifica el modo de producción"""
    try:
        # Login como SuperAdmin
        login_response = requests.post(f"{BASE_URL}/api/fix/login", 
                                     json={"username": "superadmin", "password": "admin123"})
        
        if login_response.status_code != 200:
            print("❌ No se puede hacer login para verificar modo producción")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Obtener status de producción
        status_response = requests.get(f"{BASE_URL}/api/production-control/status",
                                     headers=headers)
        
        if status_response.status_code == 200:
            result = status_response.json()
            if result["production_mode"]:
                print("✅ Modo PRODUCCIÓN activado")
                print(f"📡 URL SOAP: {result['soap_url']}")
                return True
            else:
                print("⚠️ Modo DESARROLLO activo - cambiar a producción")
                return False
        else:
            print(f"❌ Error al verificar modo producción: {status_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error verificando modo producción: {e}")
        return False

def check_repartos_listos():
    """Verifica que hay repartos listos para procesar"""
    try:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/reparto-cierre/repartos-listos?fecha={fecha_hoy}")
        
        if response.status_code == 200:
            result = response.json()
            count = len(result.get("repartos", []))
            print(f"📊 {count} repartos listos para cerrar hoy ({fecha_hoy})")
            return count > 0
        else:
            print(f"❌ Error al obtener repartos listos: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error verificando repartos listos: {e}")
        return False

def main():
    """Ejecuta todas las verificaciones"""
    print("🔍 Verificando sistema de cierre de repartos...")
    print("=" * 50)
    
    checks = [
        ("Estado del servidor", test_server_status),
        ("Conexión SOAP", test_soap_connection),
        ("Modo producción", check_production_mode),
        ("Repartos listos", check_repartos_listos)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n🔧 Verificando: {name}")
        if check_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"📈 Resultado: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("🚀 ¡Sistema listo para producción!")
        return 0
    else:
        print("⚠️ Hay problemas que resolver antes de usar en producción")
        return 1

if __name__ == "__main__":
    sys.exit(main())
