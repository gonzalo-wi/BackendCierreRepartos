#!/usr/bin/env python3
"""
Script para simular el procesamiento de reparto y ver exactamente qué datos se enviarían
"""
import sys
sys.path.append('.')

from services.reparto_cierre_service import RepartoCierreService
from datetime import datetime
import json

def simular_procesamiento():
    """Simular el procesamiento para ver qué datos se enviarían"""
    print("🔍 SIMULANDO PROCESAMIENTO DE REPARTO")
    print("=" * 60)
    
    # Inicializar servicio en modo desarrollo (no envía realmente)
    servicio = RepartoCierreService(production_mode=False)
    
    try:
        # Obtener repartos listos (igual que hace el endpoint real)
        fecha = datetime.now().strftime("%Y-%m-%d")
        repartos = servicio.get_repartos_listos(fecha)
        
        print(f"📅 Fecha: {fecha}")
        print(f"📊 Repartos encontrados: {len(repartos)}")
        
        for i, reparto in enumerate(repartos[:3]):  # Solo primeros 3 para no saturar
            print(f"\n🏭 REPARTO {i+1}:")
            print(f"  ID: {reparto['idreparto']}")
            print(f"  Planta: {reparto['planta']}")
            print(f"  Efectivo: ${reparto['efectivo_importe']}")
            print(f"  Total Cheques: {len(reparto['cheques'])}")
            print(f"  Total Retenciones: {len(reparto['retenciones'])}")
            
            # Mostrar detalles de cheques
            if reparto['cheques']:
                print(f"  💳 CHEQUES:")
                for j, cheque in enumerate(reparto['cheques']):
                    print(f"    {j+1}. Nro: {cheque.get('nro_cheque', 'N/A')} | Banco: {cheque.get('banco', 'N/A')} | Importe: ${cheque.get('importe', 0)}")
            else:
                print(f"  💳 CHEQUES: Ninguno")
            
            # Mostrar detalles de retenciones
            if reparto['retenciones']:
                print(f"  🧾 RETENCIONES:")
                for j, retencion in enumerate(reparto['retenciones']):
                    print(f"    {j+1}. Nro: {retencion.get('nro_retencion', 'N/A')} | Concepto: {retencion.get('concepto', 'N/A')} | Importe: ${retencion.get('importe', 0)}")
            else:
                print(f"  🧾 RETENCIONES: Ninguna")
            
            # Mostrar cómo se vería en el XML SOAP
            print(f"\n  📋 ESTRUCTURA JSON QUE SE ENVIARÍA:")
            print(f"    Retenciones JSON: {json.dumps(reparto['retenciones'], indent=2)}")
            
            # Simular envío para ver el XML completo
            if i == 0:  # Solo el primero para no saturar
                print(f"\n  🔍 SIMULANDO ENVÍO...")
                try:
                    resultado = servicio.enviar_reparto(reparto)
                    print(f"  ✅ Simulación exitosa: {resultado.get('status', 'N/A')}")
                except Exception as e:
                    print(f"  ❌ Error en simulación: {e}")
        
        # Resumen general
        total_repartos = len(repartos)
        total_cheques = sum(len(r['cheques']) for r in repartos)
        total_retenciones = sum(len(r['retenciones']) for r in repartos)
        
        print(f"\n📊 RESUMEN GENERAL:")
        print(f"  Total Repartos: {total_repartos}")
        print(f"  Total Cheques: {total_cheques}")
        print(f"  Total Retenciones: {total_retenciones}")
        
        if total_retenciones == 0:
            print(f"  ❌ PROBLEMA: No se encontraron retenciones para enviar")
            print(f"     Esto significa que todos los depósitos LISTOS no tienen retenciones asociadas")
        else:
            print(f"  ✅ Se enviarían {total_retenciones} retenciones")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simular_procesamiento()
