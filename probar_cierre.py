#!/usr/bin/env python3
"""
Script simple para probar el cierre de repartos en producción
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8001"

def realizar_cierre_prueba(fecha=None):
    """
    Realiza una prueba de cierre de repartos
    """
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    
    print(f"🚀 Iniciando cierre de repartos para {fecha}")
    print("=" * 50)
    
    try:
        # Usar el endpoint sin autenticación para pruebas
        data = {
            "fecha_especifica": fecha,
            "max_reintentos": 3,
            "delay_entre_envios": 1.0
        }
        
        print("📤 Enviando solicitud de cierre...")
        response = requests.post(f"{BASE_URL}/api/reparto-cierre/cerrar-repartos-test", 
                               json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Cierre completado exitosamente!")
            print(f"🔧 Modo producción: {result.get('production_mode', 'N/A')}")
            print(f"📡 URL SOAP: {result.get('config', {}).get('soap_url', 'N/A')}")
            
            # Mostrar resultado detallado
            resultado = result.get('resultado', {})
            if resultado:
                print(f"\n📊 Estadísticas del proceso:")
                print(f"  - Repartos procesados: {resultado.get('total_procesados', 0)}")
                print(f"  - Exitosos: {resultado.get('exitosos', 0)}")
                print(f"  - Fallidos: {resultado.get('fallidos', 0)}")
                
                # Mostrar detalles de envíos
                envios = resultado.get('envios_detalle', [])
                if envios:
                    print(f"\n📋 Detalle de envíos:")
                    for envio in envios[:5]:  # Mostrar solo los primeros 5
                        status = "✅" if envio.get('success') else "❌"
                        print(f"  {status} Reparto {envio.get('idreparto')}: {envio.get('response', envio.get('error', 'N/A'))}")
                    
                    if len(envios) > 5:
                        print(f"  ... y {len(envios) - 5} más")
            
            return True
            
        else:
            print(f"❌ Error en el cierre: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Detalle: {error_detail.get('detail', 'Error desconocido')}")
            except:
                print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - el proceso tardó más de 60 segundos")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 Script de prueba de cierre de repartos")
    
    # Permitir especificar fecha como argumento
    fecha = None
    if len(sys.argv) > 1:
        fecha = sys.argv[1]
        print(f"📅 Fecha especificada: {fecha}")
    else:
        fecha = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Usando fecha de hoy: {fecha}")
    
    success = realizar_cierre_prueba(fecha)
    
    if success:
        print("\n🎉 ¡Prueba completada exitosamente!")
        return 0
    else:
        print("\n💥 La prueba falló")
        return 1

if __name__ == "__main__":
    sys.exit(main())
