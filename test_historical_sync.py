#!/usr/bin/env python3
"""
Test de funcionalidad de sincronización automática para datos históricos
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.repartos_api_service import get_repartos_valores, actualizar_depositos_esperados
from services.deposits_service import get_all_deposits

def test_external_api_connection():
    """Probar conexión con API externa de valores"""
    print("🔌 Probando conexión con API externa de valores...")
    
    # Probar con fecha de ayer
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    print(f"📅 Fecha de prueba: {yesterday}")
    
    try:
        valores = get_repartos_valores(yesterday)
        if valores:
            print(f"✅ API externa respondió con {len(valores)} repartos")
            if len(valores) > 0:
                print(f"🔍 Estructura del primer reparto: {list(valores[0].keys())}")
                print(f"📊 Datos del primer reparto: {valores[0]}")
            return True
        else:
            print("⚠️ API externa no devolvió datos")
            return False
    except Exception as e:
        print(f"❌ Error conectando con API externa: {e}")
        return False

def test_minibank_api_connection():
    """Probar conexión con API de miniBank"""
    print("\n🏦 Probando conexión con API de miniBank...")
    
    # Probar con fecha de hoy
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Fecha de prueba: {today}")
    
    try:
        deposits = get_all_deposits(today)
        if deposits:
            print(f"✅ API miniBank respondió con {len(deposits)} depósitos")
            return True
        else:
            print("⚠️ API miniBank no devolvió datos")
            return False
    except Exception as e:
        print(f"❌ Error conectando con API miniBank: {e}")
        return False

def test_backend_endpoint():
    """Probar endpoint del backend con auto-sincronización"""
    print("\n🚀 Probando endpoint del backend...")
    
    # Probar con fecha de ayer (para forzar sincronización histórica)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"📅 Fecha de prueba (histórica): {yesterday}")
    
    try:
        url = f"http://localhost:8000/api/db/deposits/by-plant?date={yesterday}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint respondió correctamente")
            print(f"🔄 Auto-sync miniBank: {data.get('auto_synced_minibank', False)}")
            print(f"💰 Auto-sync valores esperados: {data.get('auto_synced_expected', False)}")
            
            # Mostrar resumen
            summary = data.get('summary', {})
            print(f"\n📊 Resumen de datos:")
            print(f"  - Total depósitos: {summary.get('total_deposits', 0)}")
            print(f"  - Total general: ${summary.get('grand_total', 0):,.2f}")
            print(f"  - Jumillano: ${summary.get('jumillano_total', 0):,.2f} ({summary.get('jumillano_count', 0)} depósitos)")
            print(f"  - La Plata: ${summary.get('plata_total', 0):,.2f} ({summary.get('plata_count', 0)} depósitos)")
            print(f"  - Nafa: ${summary.get('nafa_total', 0):,.2f} ({summary.get('nafa_count', 0)} depósitos)")
            
            return True
        else:
            print(f"❌ Error en endpoint: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error llamando endpoint: {e}")
        return False

def test_direct_sync_function():
    """Probar función de sincronización directa"""
    print("\n🔧 Probando función de sincronización directa...")
    
    # Probar con fecha de ayer
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"📅 Fecha de prueba: {yesterday}")
    
    try:
        resultado = actualizar_depositos_esperados(yesterday)
        print(f"✅ Sincronización completada")
        print(f"📊 Resultado: {json.dumps(resultado, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error en sincronización directa: {e}")
        return False

def main():
    print("🧪 PRUEBA DE FUNCIONALIDAD DE SINCRONIZACIÓN HISTÓRICA")
    print("=" * 60)
    
    tests = [
        ("API Externa de Valores", test_external_api_connection),
        ("API de miniBank", test_minibank_api_connection),
        ("Endpoint del Backend", test_backend_endpoint),
        ("Función de Sincronización Directa", test_direct_sync_function)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\n🎯 Resultado general: {'✅ TODAS LAS PRUEBAS PASARON' if all_passed else '❌ ALGUNAS PRUEBAS FALLARON'}")
    
    if all_passed:
        print("\n🚀 La funcionalidad de sincronización automática está funcionando correctamente!")
        print("📈 Los datos históricos se pueden recuperar automáticamente cuando se consultan fechas anteriores.")
    else:
        print("\n⚠️ Hay problemas que necesitan ser resueltos antes de que la funcionalidad esté completamente operativa.")

if __name__ == "__main__":
    main()
