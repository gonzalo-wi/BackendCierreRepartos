#!/usr/bin/env python3
"""
Script de prueba para verificar el cálculo de valores esperados
"""

def test_calculo_valores():
    """
    Simula el JSON de ejemplo que mencionaste y verifica el cálculo
    """
    # JSON de ejemplo que proporcionaste
    repartos_ejemplo = [
        {
            "IdReparto": 199,
            "Efectivo": 1000.00,
            "Retenciones": 3000.00,
            "Cheques": 2000.00,
            "status": 0
        }
    ]
    
    print("🧪 Probando lógica de cálculo de valores esperados...")
    print()
    
    for r in repartos_ejemplo:
        id_reparto = r["IdReparto"]
        efectivo = float(r.get("Efectivo", 0) or 0)
        retenciones = float(r.get("Retenciones", 0) or 0)
        cheques = float(r.get("Cheques", 0) or 0)
        
        # Cálculo anterior (solo efectivo)
        valor_anterior = efectivo
        
        # Cálculo nuevo (suma total)
        valor_nuevo = efectivo + retenciones + cheques
        
        print(f"📊 Reparto {id_reparto}:")
        print(f"  💵 Efectivo: ${efectivo:,.2f}")
        print(f"  🧾 Retenciones: ${retenciones:,.2f}")
        print(f"  💳 Cheques: ${cheques:,.2f}")
        print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  📉 Valor Anterior (solo efectivo): ${valor_anterior:,.2f}")
        print(f"  📈 Valor Nuevo (total): ${valor_nuevo:,.2f}")
        print(f"  📊 Diferencia: ${valor_nuevo - valor_anterior:,.2f}")
        print()

if __name__ == "__main__":
    test_calculo_valores()
