#!/usr/bin/env python3
"""
Script de prueba para simular las llamadas del frontend al sistema de cierre de repartos
"""

import sys
import os
sys.path.append('.')

import sqlite3
import json
from datetime import datetime
from services.reparto_cierre_service import RepartoCierreService

def mostrar_separador(titulo):
    print("\n" + "="*60)
    print(f"🔧 {titulo}")
    print("="*60)

def test_estado_actual_db():
    """Prueba 1: Verificar estado actual de la base de datos"""
    mostrar_separador("PRUEBA 1: Estado actual de la base de datos")
    
    conn = sqlite3.connect('deposits.db')
    cursor = conn.cursor()
    
    # Contar repartos por estado
    cursor.execute('SELECT estado, COUNT(*) FROM deposits GROUP BY estado')
    estados = cursor.fetchall()
    
    print("📊 Estados actuales:")
    for estado, count in estados:
        print(f"   {estado}: {count} repartos")
    
    # Mostrar repartos LISTO por fecha
    cursor.execute('''
        SELECT 
            DATE(date_time) as fecha,
            COUNT(*) as total_repartos,
            identifier
        FROM deposits 
        WHERE estado = "LISTO"
        GROUP BY DATE(date_time), identifier
        ORDER BY fecha DESC
    ''')
    
    resultados = cursor.fetchall()
    
    if resultados:
        print("\n📅 Repartos LISTO disponibles:")
        for row in resultados:
            fecha, total, identifier = row
            print(f"   {fecha}: {total} repartos ({identifier})")
    else:
        print("\n⚠️ No hay repartos con estado LISTO")
    
    conn.close()

def test_frontend_resumen_fechas():
    """Prueba 2: Simular llamada GET /reparto-cierre/resumen-por-fechas"""
    mostrar_separador("PRUEBA 2: Frontend - Obtener fechas disponibles")
    
    print("🌐 Simulando: GET /reparto-cierre/resumen-por-fechas")
    
    servicio = RepartoCierreService()
    resumen = servicio.get_resumen_repartos_por_fecha()
    
    # Simular respuesta del endpoint
    respuesta_frontend = {
        "success": True,
        "resumen": resumen
    }
    
    print("\n📤 Respuesta JSON que recibiría el frontend:")
    print(json.dumps(respuesta_frontend, indent=2, ensure_ascii=False))
    
    return resumen

def test_frontend_obtener_repartos_fecha(fecha_seleccionada):
    """Prueba 3: Simular llamada GET /reparto-cierre/repartos-listos?fecha=YYYY-MM-DD"""
    mostrar_separador(f"PRUEBA 3: Frontend - Obtener repartos para {fecha_seleccionada}")
    
    print(f"🌐 Simulando: GET /reparto-cierre/repartos-listos?fecha={fecha_seleccionada}")
    
    servicio = RepartoCierreService()
    fecha_dt = datetime.strptime(fecha_seleccionada, "%Y-%m-%d")
    repartos = servicio.get_repartos_listos(fecha_dt)
    
    # Simular respuesta del endpoint
    respuesta_frontend = {
        "success": True,
        "total": len(repartos),
        "fecha": fecha_seleccionada,
        "repartos": repartos
    }
    
    print(f"\n📤 Respuesta: {len(repartos)} repartos encontrados")
    if repartos:
        print("🎯 Primeros 3 repartos:")
        for i, reparto in enumerate(repartos[:3]):
            print(f"   {i+1}. ID: {reparto['idreparto']} | Planta: {reparto['planta']} | Efectivo: ${reparto['efectivo_importe']}")
    
    return repartos

def test_frontend_cerrar_repartos(fecha_seleccionada, modo_test=True):
    """Prueba 4: Simular llamada POST /reparto-cierre/cerrar-repartos"""
    mostrar_separador(f"PRUEBA 4: Frontend - Cerrar repartos {fecha_seleccionada}")
    
    print(f"🌐 Simulando: POST /reparto-cierre/cerrar-repartos")
    print(f"📦 Payload: {{'fecha_especifica': '{fecha_seleccionada}', 'modo_test': {modo_test}}}")
    
    servicio = RepartoCierreService()
    fecha_dt = datetime.strptime(fecha_seleccionada, "%Y-%m-%d")
    
    # Simular el procesamiento
    resultado = servicio.procesar_cola_repartos(fecha_dt)
    
    # Simular respuesta del endpoint
    respuesta_frontend = {
        "success": resultado["success"],
        "message": resultado["message"],
        "total_repartos": resultado["total_repartos"],
        "enviados": resultado["enviados"],
        "errores": resultado["errores"],
        "timestamp": resultado["timestamp"]
    }
    
    print("\n📤 Respuesta JSON que recibiría el frontend:")
    print(json.dumps(respuesta_frontend, indent=2, ensure_ascii=False))
    
    return resultado

def test_verificar_cambios_db():
    """Prueba 5: Verificar cambios en la base de datos después del envío"""
    mostrar_separador("PRUEBA 5: Verificar cambios en la base de datos")
    
    conn = sqlite3.connect('deposits.db')
    cursor = conn.cursor()
    
    # Contar repartos por estado
    cursor.execute('SELECT estado, COUNT(*) FROM deposits GROUP BY estado')
    estados = cursor.fetchall()
    
    print("📊 Estados después del proceso:")
    for estado, count in estados:
        print(f"   {estado}: {count} repartos")
    
    # Mostrar repartos ENVIADO con fecha
    cursor.execute('''
        SELECT 
            deposit_id,
            DATE(date_time) as fecha_reparto,
            DATE(fecha_envio) as fecha_envio,
            identifier,
            total_amount
        FROM deposits 
        WHERE estado = "ENVIADO"
        ORDER BY fecha_envio DESC
        LIMIT 10
    ''')
    
    enviados = cursor.fetchall()
    
    if enviados:
        print("\n📤 Últimos 10 repartos ENVIADO:")
        for row in enviados:
            deposit_id, fecha_reparto, fecha_envio, identifier, amount = row
            print(f"   ID: {deposit_id} | Reparto: {fecha_reparto} | Enviado: {fecha_envio} | Cajero: {identifier} | ${amount}")
    
    conn.close()

def main():
    print("🚀 SIMULADOR DE FRONTEND - Sistema de Cierre de Repartos")
    print("=" * 70)
    
    # Prueba 1: Estado actual
    test_estado_actual_db()
    
    # Prueba 2: Obtener fechas disponibles (primer llamada del frontend)
    resumen = test_frontend_resumen_fechas()
    
    if resumen["total_repartos_listos"] == 0:
        print("\n⚠️ No hay repartos LISTO para procesar")
        return
    
    # Seleccionar la primera fecha disponible para las pruebas
    if resumen["fechas"]:
        fecha_seleccionada = resumen["fechas"][0]["fecha"]
        print(f"\n🎯 Usando fecha de prueba: {fecha_seleccionada}")
        
        # Prueba 3: Obtener repartos de esa fecha
        repartos = test_frontend_obtener_repartos_fecha(fecha_seleccionada)
        
        if repartos:
            # Prueba 4: Procesar solo UNO para prueba (simular modo test)
            print(f"\n⚠️ MODO PRUEBA: Solo se procesará 1 reparto de {len(repartos)} disponibles")
            input("Presiona ENTER para continuar...")
            
            # Modificar temporalmente para procesar solo uno
            test_frontend_cerrar_repartos(fecha_seleccionada, modo_test=True)
            
            # Prueba 5: Verificar cambios
            test_verificar_cambios_db()
    
    print(f"\n🏁 Simulación completada")
    print("\n💡 Para usar en producción desde el frontend:")
    print("   1. Obtener fechas: GET /reparto-cierre/resumen-por-fechas")
    print("   2. Mostrar selector al usuario")
    print("   3. Al seleccionar: POST /reparto-cierre/cerrar-repartos")
    print("   4. Mostrar resultado al usuario")

if __name__ == "__main__":
    main()
