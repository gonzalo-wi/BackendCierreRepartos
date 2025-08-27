#!/usr/bin/env python3
"""
Script para probar manualmente la API con datos conocidos
"""

import os
import sys
import requests

# Añadir el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_directa():
    """Probar la API directamente con la URL correcta"""
    
    print("🧪 Probando API externa directamente...")
    
    # URL correcta con idreparto=0
    url = "http://192.168.0.8:97/service1.asmx/reparto_get_valores"
    
    # Probar con diferentes fechas
    fechas_test = [
        "27/08/2025",  # Hoy
        "26/08/2025",  # Ayer
        "25/08/2025",  # Antier
        "23/08/2025",  # Viernes
        "22/08/2025",  # Jueves
    ]
    
    for fecha in fechas_test:
        try:
            params = {"idreparto": 0, "fecha": fecha}
            print(f"\n📅 Probando fecha: {fecha}")
            print(f"🔗 URL: {url}?idreparto=0&fecha={fecha}")
            
            response = requests.get(url, params=params, timeout=10)
            print(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Respuesta exitosa: {len(data)} repartos")
                    
                    if data:
                        print(f"🔍 Primer reparto: {data[0]}")
                        break  # Encontramos datos, no necesitamos probar más fechas
                    else:
                        print("⚠️ Respuesta vacía")
                        
                except Exception as json_error:
                    print(f"❌ Error parseando JSON: {json_error}")
                    print(f"📄 Contenido: {response.text[:200]}...")
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"📄 Contenido: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")

def test_reparto_especifico():
    """Probar con un reparto específico que sabemos que existe"""
    
    print(f"\n🎯 Probando reparto específico...")
    
    url = "http://192.168.0.8:97/service1.asmx/reparto_get_valores"
    params = {"idreparto": 199, "fecha": "27/08/2025"}
    
    try:
        print(f"🔗 URL: {url}?idreparto=199&fecha=27/08/2025")
        response = requests.get(url, params=params, timeout=10)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta exitosa: {data}")
        else:
            print(f"❌ Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBA DIRECTA DE API EXTERNA")
    print("=" * 60)
    
    test_api_directa()
    test_reparto_especifico()
    
    print("\n" + "=" * 60)
    print("🏁 Prueba completada")
    print("=" * 60)
