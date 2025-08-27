#!/usr/bin/env python3
"""
Script de debug para probar la actualización de valores esperados
"""

import os
import sys
from datetime import datetime

# Añadir el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.repartos_api_service import actualizar_depositos_esperados, get_repartos_valores

def debug_actualizacion_valores():
    """Debug de la actualización de valores esperados"""
    
    print("🔍 DEBUG: Actualización de valores esperados")
    print("=" * 60)
    
    # Probar con fecha de hoy
    fecha_hoy = "2025-08-27"
    print(f"📅 Probando con fecha: {fecha_hoy}")
    
    # 1. Probar la API externa directamente
    try:
        print(f"\n1️⃣ Probando API externa directamente...")
        fecha_api = "27/08/2025"  # Formato DD/MM/YYYY
        datos_api = get_repartos_valores(fecha_api)
        
        print(f"   📡 URL consultada: http://192.168.0.8:97/service1.asmx/reparto_get_valores?idreparto=0&fecha={fecha_api}")
        print(f"   📊 Datos obtenidos: {len(datos_api) if datos_api else 0} repartos")
        
        if datos_api:
            print(f"   🔍 Primer reparto: {datos_api[0]}")
        else:
            print("   ⚠️ No se obtuvieron datos de la API")
            
    except Exception as e:
        print(f"   ❌ Error consultando API: {str(e)}")
    
    # 2. Probar la función de actualización
    try:
        print(f"\n2️⃣ Probando función de actualización...")
        resultado = actualizar_depositos_esperados(fecha_hoy)
        
        print(f"   ✅ Resultado: {resultado}")
        
    except Exception as e:
        print(f"   ❌ Error en actualización: {str(e)}")
        import traceback
        traceback.print_exc()

def test_formatos_fecha():
    """Probar diferentes formatos de fecha"""
    
    print(f"\n3️⃣ Probando conversión de formatos...")
    
    # Formato que llega del endpoint
    fecha_input = "2025-08-27"
    
    try:
        fecha_obj = datetime.strptime(fecha_input, "%Y-%m-%d")
        fecha_api = fecha_obj.strftime("%d/%m/%Y")
        
        print(f"   📥 Input: {fecha_input}")
        print(f"   📤 Para API: {fecha_api}")
        print(f"   ✅ Conversión exitosa")
        
    except Exception as e:
        print(f"   ❌ Error en conversión: {str(e)}")

if __name__ == "__main__":
    debug_actualizacion_valores()
    test_formatos_fecha()
