#!/usr/bin/env python3
"""
Script simple para probar la API con fechas anteriores
"""

import os
import sys
import requests

def test_api_fechas():
    """Probar API con diferentes fechas"""
    
    fechas_test = [
        "26/08/2025",  # Ayer
        "25/08/2025",  # Antier
        "23/08/2025",  # Viernes
        "22/08/2025",  # Jueves
        "21/08/2025",  # Miércoles
    ]
    
    for fecha in fechas_test:
        try:
            url = f"http://192.168.0.8:97/service1.asmx/reparto_get_valores?fecha={fecha}"
            print(f"🔗 Probando: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Datos: {len(data)} repartos")
                if data:
                    print(f"   📋 Primer reparto: {data[0]}")
                    break
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Excepción: {str(e)}")
        
        print()

if __name__ == "__main__":
    print("🧪 Probando API externa con fechas anteriores...")
    print("=" * 60)
    test_api_fechas()
