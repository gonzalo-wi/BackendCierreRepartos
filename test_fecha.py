#!/usr/bin/env python3
"""
Script simple para probar una fecha específica
"""

import sys
sys.path.append('.')

from datetime import datetime
from services.reparto_cierre_service import RepartoCierreService
import json

def probar_fecha(fecha_str):
    """Probar una fecha específica"""
    print(f"🧪 PROBANDO FECHA: {fecha_str}")
    print("="*50)
    
    servicio = RepartoCierreService()
    fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
    
    # 1. Ver cuántos repartos hay
    repartos = servicio.get_repartos_listos(fecha_dt)
    print(f"📊 Repartos LISTO encontrados: {len(repartos)}")
    
    if len(repartos) == 0:
        print("⚠️ No hay repartos para procesar en esta fecha")
        return
    
    # 2. Mostrar resumen
    plantas = {}
    for r in repartos:
        planta = r['planta']
        if planta not in plantas:
            plantas[planta] = 0
        plantas[planta] += 1
    
    print("🏭 Por planta:")
    for planta, count in plantas.items():
        print(f"   {planta}: {count} repartos")
    
    # 3. Preguntar si procesar
    print(f"\n🤔 ¿Procesar estos {len(repartos)} repartos? (y/n): ", end="")
    respuesta = input()
    
    if respuesta.lower() == 'y':
        print("\n🚀 Procesando...")
        resultado = servicio.procesar_cola_repartos(fecha_dt)
        
        print(f"\n✅ Resultado:")
        print(f"   Total: {resultado['total_repartos']}")
        print(f"   Enviados: {resultado['enviados']}")
        print(f"   Errores: {resultado['errores']}")
    else:
        print("❌ Cancelado")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fecha = sys.argv[1]
    else:
        print("📅 Fechas disponibles:")
        servicio = RepartoCierreService()
        resumen = servicio.get_resumen_repartos_por_fecha()
        
        for fecha_info in resumen["fechas"][:5]:
            print(f"   {fecha_info['fecha']} ({fecha_info['total_repartos']} repartos)")
        
        print("\nUso: python3 test_fecha.py YYYY-MM-DD")
        print("Ejemplo: python3 test_fecha.py 2025-07-23")
        exit()
    
    probar_fecha(fecha)
