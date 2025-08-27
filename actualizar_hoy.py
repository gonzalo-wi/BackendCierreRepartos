#!/usr/bin/env python3
"""
Script para forzar la actualización de valores esperados para hoy
"""

import os
import sys
from datetime import datetime

# Añadir el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.repartos_api_service import actualizar_depositos_esperados

def actualizar_valores_hoy():
    """Actualiza los valores esperados para hoy"""
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    print(f"🔄 Actualizando valores esperados para {fecha_hoy}...")
    
    resultado = actualizar_depositos_esperados(fecha_hoy)
    
    print(f"✅ Resultado: {resultado}")
    print(f"📊 Depósitos actualizados: {resultado.get('actualizados', 0)}")
    
    if resultado.get('detalles'):
        print(f"\n📋 Detalles de depósitos actualizados:")
        for detalle in resultado['detalles']:
            print(f"   - Depósito {detalle['deposit_id']}: ${detalle['new_expected']} ({detalle['new_composicion']})")

if __name__ == "__main__":
    actualizar_valores_hoy()
