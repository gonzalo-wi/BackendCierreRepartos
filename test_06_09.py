#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.repartos_api_service import get_repartos_valores
from services.deposits_service import get_all_deposits

print("🔍 Probando APIs para el 06/09/2025...")

# Probar API externa de valores
print("\n1️⃣ API Externa de Valores:")
try:
    valores = get_repartos_valores("06/09/2025")
    if valores:
        print(f"✅ Encontrados {len(valores)} repartos con valores esperados")
        # Mostrar algunos ejemplos
        for i, reparto in enumerate(valores[:3]):
            print(f"   Reparto {i+1}: {reparto}")
    else:
        print("❌ No hay valores esperados para esta fecha")
except Exception as e:
    print(f"❌ Error: {e}")

# Probar API de miniBank
print("\n2️⃣ API de miniBank:")
try:
    deposits = get_all_deposits("2025-09-06")
    if deposits:
        print(f"✅ Encontrados {len(deposits)} depósitos reales")
        # Mostrar algunos ejemplos
        for i, deposit in enumerate(deposits[:3]):
            print(f"   Depósito {i+1}: {deposit.get('identifier', 'N/A')} - ${deposit.get('totalAmount', 0)}")
    else:
        print("❌ No hay depósitos reales para esta fecha")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🎯 Conclusión:")
print("Para que aparezcan datos en el endpoint principal necesitas:")
print("- Depósitos REALES de miniBank (para que aparezcan en la lista)")
print("- Valores ESPERADOS de la API externa (para calcular diferencias)")
