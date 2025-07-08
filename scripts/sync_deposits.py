#!/usr/bin/env python3
"""
Script para sincronizar depósitos automáticamente
"""
import sys
import os
import requests
from datetime import datetime, timedelta

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def sync_deposits_for_date(date_str, base_url="http://localhost:8001"):
    """
    Sincroniza depósitos para una fecha específica
    """
    try:
        print(f"🔄 Sincronizando depósitos para fecha: {date_str}")
        
        # Hacer POST request al endpoint de guardado
        response = requests.post(
            f"{base_url}/api/deposits/all/save",
            params={"date": date_str},
            timeout=120  # 2 minutos de timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result.get('message', 'Sincronización exitosa')}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error al sincronizar: {str(e)}")
        return False

def main():
    """
    Función principal del script
    """
    # Por defecto sincronizar la fecha actual (hoy)
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        # Fecha de hoy
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
    
    print(f"🚀 Iniciando sincronización automática")
    print(f"📅 Fecha a sincronizar: {date_str}")
    
    success = sync_deposits_for_date(date_str)
    
    if success:
        print("🎉 Sincronización completada exitosamente")
        sys.exit(0)
    else:
        print("💥 Falló la sincronización")
        sys.exit(1)

if __name__ == "__main__":
    main()
