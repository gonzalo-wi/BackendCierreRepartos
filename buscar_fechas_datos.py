#!/usr/bin/env python3
"""
Script para buscar fechas con datos disponibles en la API externa
"""

import os
import sys
from datetime import datetime, timedelta

# Añadir el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.repartos_api_service import get_repartos_valores

def buscar_fechas_con_datos():
    """Buscar fechas que tienen datos en la API externa"""
    
    print("🔍 Buscando fechas con datos en la API externa...")
    print("=" * 60)
    
    # Probar las últimas 7 fechas
    fecha_base = datetime.now()
    
    for i in range(7):
        fecha_test = fecha_base - timedelta(days=i)
        fecha_str = fecha_test.strftime("%d/%m/%Y")
        
        try:
            datos = get_repartos_valores(fecha_str)
            count = len(datos) if datos else 0
            
            if count > 0:
                print(f"✅ {fecha_str}: {count} repartos encontrados")
                if count > 0:
                    print(f"   🔍 Primer reparto: {datos[0]}")
                    break
            else:
                print(f"❌ {fecha_str}: Sin datos")
                
        except Exception as e:
            print(f"❌ {fecha_str}: Error - {str(e)}")

def test_fecha_especifica():
    """Probar con una fecha específica que sabemos que tiene datos"""
    
    print(f"\n🎯 Probando con fecha específica...")
    
    # Probar con fechas de días laborables anteriores
    fechas_test = [
        "26/08/2025",  # Ayer
        "25/08/2025",  # Antier  
        "23/08/2025",  # Viernes pasado
        "22/08/2025",  # Jueves pasado
    ]
    
    for fecha in fechas_test:
        try:
            datos = get_repartos_valores(fecha)
            count = len(datos) if datos else 0
            
            if count > 0:
                print(f"✅ {fecha}: {count} repartos")
                print(f"   📋 Estructura: {list(datos[0].keys()) if datos else 'N/A'}")
                
                # Probar actualización con esta fecha
                from services.repartos_api_service import actualizar_depositos_esperados
                
                # Convertir a formato YYYY-MM-DD
                fecha_obj = datetime.strptime(fecha, "%d/%m/%Y")
                fecha_db = fecha_obj.strftime("%Y-%m-%d")
                
                print(f"   🔄 Probando actualización para {fecha_db}...")
                resultado = actualizar_depositos_esperados(fecha_db)
                print(f"   📊 Resultado: {resultado}")
                break
            else:
                print(f"❌ {fecha}: Sin datos")
                
        except Exception as e:
            print(f"❌ {fecha}: Error - {str(e)}")

if __name__ == "__main__":
    buscar_fechas_con_datos()
    test_fecha_especifica()
