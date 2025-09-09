#!/usr/bin/env python3
"""
Script para probar los semáforos de documentos en la API
"""

import requests
import json
from datetime import datetime

def test_semaforos_docs(fecha="2025-08-27"):
    """
    Prueba los semáforos de documentos en la respuesta de la API
    """
    
    base_url = "http://localhost:8001"
    endpoint = f"{base_url}/api/db/deposits/by-plant"
    
    print(f"🧪 Probando semáforos de documentos para fecha: {fecha}")
    print(f"📡 Endpoint: {endpoint}?date={fecha}")
    print("=" * 80)
    
    try:
        response = requests.get(endpoint, params={"date": fecha}, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"✅ Respuesta exitosa - Status: {data.get('status')}")
        print(f"📅 Fecha: {data.get('date')}")
        print(f"🔄 Auto sync minibank: {data.get('auto_synced_minibank')}")
        print(f"💰 Auto sync esperados: {data.get('auto_synced_expected')}")
        print()
        
        # Analizar cada planta
        plants = data.get("plants", {})
        total_deposits = 0
        deposits_with_docs = 0
        deposits_pending_docs = 0
        
        for plant_name, plant_data in plants.items():
            deposits = plant_data.get("deposits", [])
            total_deposits += len(deposits)
            
            print(f"🏭 {plant_data.get('name', plant_name).upper()}")
            print(f"   📊 Total depósitos: {len(deposits)}")
            
            if not deposits:
                print("   ⚪ Sin depósitos")
                print()
                continue
            
            for deposit in deposits:
                semaforo = deposit.get("semaforo_docs", {})
                deposit_id = deposit.get("deposit_id")
                composicion = deposit.get("composicion_esperado", "")
                
                print(f"   📦 Depósito {deposit_id}:")
                print(f"      💡 Composición esperada: '{composicion}'")
                print(f"      📄 Cheques: esperados={semaforo.get('cheques_esperados')}, cargados={semaforo.get('cheques_cargados')}")
                print(f"      🧾 Retenciones: esperadas={semaforo.get('retenciones_esperadas')}, cargadas={semaforo.get('retenciones_cargadas')}")
                
                if semaforo.get("tiene_docs_esperados"):
                    if semaforo.get("docs_completos"):
                        print(f"      ✅ DOCS COMPLETOS")
                        deposits_with_docs += 1
                    else:
                        print(f"      ⚠️  DOCS PENDIENTES:", end="")
                        if semaforo.get("cheques_pendientes"):
                            print(" 📄CHEQUES", end="")
                        if semaforo.get("retenciones_pendientes"):
                            print(" 🧾RETENCIONES", end="")
                        print()
                        deposits_pending_docs += 1
                else:
                    print(f"      ⚪ Sin documentos esperados")
                print()
        
        print("=" * 80)
        print("📈 RESUMEN DE SEMÁFOROS:")
        print(f"   📦 Total depósitos: {total_deposits}")
        print(f"   ✅ Con docs completos: {deposits_with_docs}")
        print(f"   ⚠️  Con docs pendientes: {deposits_pending_docs}")
        print(f"   ⚪ Sin docs esperados: {total_deposits - deposits_with_docs - deposits_pending_docs}")
        
        if deposits_pending_docs > 0:
            print(f"\n🚨 ATENCIÓN: {deposits_pending_docs} depósitos tienen documentos pendientes de carga!")
        else:
            print(f"\n🎉 PERFECTO: Todos los documentos esperados están cargados")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def test_machine_view(fecha="2025-08-27"):
    """
    Prueba la vista por máquina también
    """
    base_url = "http://localhost:8001"
    endpoint = f"{base_url}/api/db/deposits/by-machine"
    
    print(f"\n🏗️ Probando vista por máquina para fecha: {fecha}")
    print(f"📡 Endpoint: {endpoint}?date={fecha}")
    print("=" * 50)
    
    try:
        response = requests.get(endpoint, params={"date": fecha}, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        machines = data.get("machines", {})
        
        for machine_id, machine_data in machines.items():
            deposits = machine_data.get("deposits", [])
            docs_pendientes = sum(1 for d in deposits 
                                if d.get("semaforo_docs", {}).get("tiene_docs_esperados") 
                                and not d.get("semaforo_docs", {}).get("docs_completos"))
            
            print(f"🤖 {machine_id} ({machine_data.get('st_name', 'N/A')})")
            print(f"   📊 Depósitos: {len(deposits)}")
            if docs_pendientes > 0:
                print(f"   ⚠️  Docs pendientes: {docs_pendientes}")
            else:
                print(f"   ✅ Docs al día")
        
    except Exception as e:
        print(f"❌ Error en vista por máquina: {e}")

if __name__ == "__main__":
    # Probar con la fecha de hoy
    fecha_hoy = "2025-08-27"
    
    test_semaforos_docs(fecha_hoy)
    test_machine_view(fecha_hoy)
    
    print("\n" + "=" * 80)
    print("🎯 CÓMO USAR LOS SEMÁFOROS EN EL FRONTEND:")
    print("   • semaforo_docs.tiene_docs_esperados = true/false")
    print("   • semaforo_docs.docs_completos = true/false")
    print("   • semaforo_docs.cheques_pendientes = true/false") 
    print("   • semaforo_docs.retenciones_pendientes = true/false")
    print()
    print("💡 EJEMPLOS DE USO:")
    print("   🟢 Verde: docs_completos = true")
    print("   🟡 Amarillo: tiene_docs_esperados = true && docs_completos = false")
    print("   ⚪ Gris: tiene_docs_esperados = false")
