#!/usr/bin/env python3
"""
Script de prueba para verificar que el servicio de cierre obtiene correctamente
solo el valor del efectivo (no el total) al cerrar repartos.
"""

import os
import sys
import requests
from datetime import datetime

# Añadir el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.reparto_cierre_service import RepartoCierreService

def test_obtener_efectivo():
    """
    Prueba la función de obtener efectivo para cierre
    """
    print("🧪 Probando obtención de efectivo para cierre de reparto...")
    
    # Crear instancia del servicio
    servicio = RepartoCierreService()
    
    # Simular un objeto deposit básico
    class MockDeposit:
        def __init__(self):
            self.date_time = datetime.now()
            self.total_amount = 1000  # Monto real del depósito
            self.deposit_esperado = 6000  # Total suma (efectivo + retenciones + cheques)
    
    mock_deposit = MockDeposit()
    
    # Probar con un idreparto de ejemplo
    idreparto = 42  # Usamos el mismo que en nuestras pruebas anteriores
    
    try:
        efectivo_para_cierre = servicio._obtener_efectivo_para_cierre(idreparto, mock_deposit)
        
        print(f"✅ Efectivo obtenido para cierre del reparto {idreparto}: ${efectivo_para_cierre}")
        print(f"📊 Comparación:")
        print(f"   - Total real del depósito: ${mock_deposit.total_amount}")
        print(f"   - Total esperado (suma): ${mock_deposit.deposit_esperado}")
        print(f"   - Efectivo para cierre: ${efectivo_para_cierre}")
        
        # Verificar que el efectivo no sea el total suma
        if float(efectivo_para_cierre) != mock_deposit.deposit_esperado:
            print("✅ CORRECTO: El efectivo para cierre NO es igual al total suma")
        else:
            print("❌ ERROR: El efectivo para cierre es igual al total suma")
            
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

def test_api_externa():
    """
    Prueba directa de la API externa para verificar los valores
    """
    print("\n🌐 Probando API externa directamente...")
    
    try:
        fecha = datetime.now().strftime("%d/%m/%Y")
        api_url = f"http://192.168.0.8:8097/service1.asmx/reparto_get_valores?fecha={fecha}"
        
        print(f"🔗 Consultando: {api_url}")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        valores_data = response.json()
        
        print(f"📊 Respuesta de la API:")
        for i, reparto in enumerate(valores_data[:3]):  # Mostrar solo los primeros 3
            idreparto = reparto.get("idreparto", "N/A")
            efectivo = reparto.get("Efectivo", 0) or reparto.get("efectivo", 0)
            retenciones = reparto.get("Retenciones", 0) or reparto.get("retenciones", 0)
            cheques = reparto.get("Cheques", 0) or reparto.get("cheques", 0)
            total = efectivo + retenciones + cheques
            
            print(f"   Reparto {idreparto}:")
            print(f"     - Efectivo: ${efectivo}")
            print(f"     - Retenciones: ${retenciones}")
            print(f"     - Cheques: ${cheques}")
            print(f"     - Total (suma): ${total}")
            print()
            
    except Exception as e:
        print(f"❌ Error consultando API externa: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBA: Efectivo para cierre de repartos")
    print("=" * 60)
    
    test_api_externa()
    test_obtener_efectivo()
    
    print("\n" + "=" * 60)
    print("🏁 Prueba completada")
    print("=" * 60)
