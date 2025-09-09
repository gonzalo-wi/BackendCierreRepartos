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
        # Verificar si son objetos o diccionarios
        if len(deposits) > 0:
            first_deposit = deposits[0]
            print(f"   Tipo de depósito: {type(first_deposit)}")
            if hasattr(first_deposit, 'identifier'):
                print(f"   Primer depósito: {first_deposit.identifier} - ${first_deposit.total_amount}")
            elif isinstance(first_deposit, dict):
                print(f"   Primer depósito: {first_deposit.get('identifier', 'N/A')} - ${first_deposit.get('totalAmount', 0)}")
            else:
                print(f"   Primer depósito: {first_deposit}")
    else:
        print("❌ No hay depósitos reales para esta fecha")
except Exception as e:
    print(f"❌ Error en miniBank: {e}")

print("\n3️⃣ Verificación de lógica:")
print("El endpoint principal muestra depósitos cuando:")
print("- HAY depósitos reales de miniBank (base de datos o API)")
print("- Los valores esperados se sincronizan automáticamente si están disponibles")
print("- Si no hay depósitos reales, la respuesta estará vacía aunque haya valores esperados")
