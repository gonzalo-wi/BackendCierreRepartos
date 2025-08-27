"""
Servicio para integrar con la API externa de repartos
"""
import requests
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

def get_repartos_valores(fecha: str) -> List[Dict]:
    """
    Obtiene los valores esperados de repartos desde la API externa
    
    Args:
        fecha: Fecha en formato "DD/MM/YYYY"
    
    Returns:
        Lista de diccionarios con los valores de repartos
    """
    try:
        url = "http://192.168.0.8:97/service1.asmx/reparto_get_valores"
        params = {"idreparto": 0, "fecha": fecha}
        
        logging.debug(f"🌐 Consultando API: {url}?idreparto=0&fecha={fecha}")
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Filtrar repartos que tienen valores (efectivo > 0 o retenciones > 0 o cheques > 0)
        repartos_con_valores = []
        for r in data:
            efectivo = float(r.get("Efectivo", 0) or 0)
            retenciones = float(r.get("Retenciones", 0) or 0)
            cheques = float(r.get("Cheques", 0) or 0)
            
            if efectivo > 0 or retenciones > 0 or cheques > 0:
                repartos_con_valores.append(r)
        
        logging.info(f"✅ API externa respondió: {len(data)} repartos total, {len(repartos_con_valores)} con valores > 0")
        
        return repartos_con_valores
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error al consultar API externa: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"❌ Error procesando respuesta de API externa: {str(e)}")
        return []

def extraer_idreparto_de_user_name(user_name: str) -> Optional[int]:
    """
    Extrae el idreparto del user_name usando patrones robustos
    
    Args:
        user_name: Nombre de usuario del depósito
    
    Returns:
        El idreparto extraído o None si no se pudo extraer
    
    Ejemplos:
        "42, RTO 042" -> 42
        "RTO 277, 277" -> 277
        "1, algo más" -> 1
        "RTO 123, algo" -> 123
    """
    if not user_name:
        return None
    
    try:
        # Buscar el primer número antes de la coma
        # Esto maneja casos como "42, RTO 042" y "RTO 277, 277"
        parte_antes_coma = user_name.split(",")[0].strip()
        
        # Buscar todos los números en la parte antes de la coma
        numeros = re.findall(r'\d+', parte_antes_coma)
        
        if numeros:
            # Tomar el primer número encontrado
            return int(numeros[0])
        
        # Si no hay números antes de la coma, buscar después de la coma
        # Esto maneja casos edge como ", 123"
        if "," in user_name:
            parte_despues_coma = user_name.split(",", 1)[1].strip()
            numeros_despues = re.findall(r'\d+', parte_despues_coma)
            if numeros_despues:
                return int(numeros_despues[0])
        
        return None
        
    except (ValueError, IndexError) as e:
        logging.warning(f"⚠️ Error al extraer idreparto de '{user_name}': {e}")
        return None

def mapear_idreparto_a_user_name(idreparto: int) -> str:
    """
    Mapea el idreparto de la API externa al user_name de nuestros depósitos
    
    Args:
        idreparto: ID del reparto desde la API externa
    
    Returns:
        String con formato de user_name esperado
    """
    # Formatear el idreparto como user_name
    # Ejemplo: idreparto=1 -> "1, RTO 001" o similar
    numero_formateado = str(idreparto).zfill(3)  # Rellenar con ceros
    return f"{idreparto}, RTO {numero_formateado}"

def actualizar_depositos_esperados(fecha_str: str) -> Dict:
    """
    Actualiza los valores esperados de todos los depósitos para una fecha
    
    Args:
        fecha_str: Fecha en formato "YYYY-MM-DD"
    
    Returns:
        Diccionario con el resultado de la operación
    """
    from database import SessionLocal
    from models.deposit import Deposit
    from sqlalchemy import and_, func, text
    from sqlalchemy.types import Date
    from datetime import datetime as dt
    
    try:
        # Convertir fecha de "YYYY-MM-DD" a "DD/MM/YYYY" para la API externa
        fecha_obj = dt.strptime(fecha_str, "%Y-%m-%d")
        fecha_api = fecha_obj.strftime("%d/%m/%Y")
        
        # Obtener valores de la API externa
        repartos_valores = get_repartos_valores(fecha_api)
        
        if not repartos_valores:
            return {
                "status": "warning",
                "message": "No se obtuvieron datos de la API externa",
                "actualizados": 0
            }
        
        db = SessionLocal()
        
        # Convertir fecha para consultar depósitos
        query_date = fecha_obj.date()
        
        # Obtener depósitos de la fecha especificada
        # Compatibilidad SQL Server: usar CAST(datetime AS date)
        deposits = db.query(Deposit).filter(
            func.cast(Deposit.date_time, Date) == query_date
        ).all()
        
        actualizados = 0
        detalles = []
        extracciones_exitosas = 0
        coincidencias_encontradas = 0
        
        # Crear mapas de idreparto -> valores y composiciones para búsqueda rápida
        # Asegurar que los keys sean enteros para comparación correcta
        try:
            # Debug: mostrar estructura de los datos
            if repartos_valores:
                logging.info(f"🔍 Estructura de primer reparto: {repartos_valores[0].keys()}")
            
            valores_map = {}
            efectivos_map = {}  # Mapa para guardar solo los efectivos
            composiciones_map = {}
            
            for r in repartos_valores:
                # Buscar la clave correcta para idreparto (puede variar)
                id_key = None
                for key in ['idreparto', 'IdReparto', 'id_reparto', 'idReparto', 'ID', 'id']:
                    if key in r:
                        id_key = key
                        break
                
                if id_key:
                    idreparto = int(r[id_key])
                    
                    # Calcular el valor esperado total: Efectivo + Retenciones + Cheques
                    efectivo = float(r.get("Efectivo", 0) or r.get("efectivo", 0) or 0)
                    retenciones = float(r.get("Retenciones", 0) or r.get("retenciones", 0) or 0)
                    cheques = float(r.get("Cheques", 0) or r.get("cheques", 0) or 0)
                    
                    total_esperado = efectivo + retenciones + cheques
                    
                    if total_esperado > 0:
                        valores_map[idreparto] = int(total_esperado)
                        efectivos_map[idreparto] = int(efectivo)  # Guardar efectivo por separado
                        composiciones_map[idreparto] = generar_composicion_esperado(r)
                        logging.debug(f"💰 Reparto {idreparto}: Efectivo={efectivo}, Retenciones={retenciones}, Cheques={cheques}, Total={total_esperado}")
                else:
                    logging.warning(f"⚠️ No se encontró clave de ID en reparto: {r.keys()}")
                    
        except Exception as e:
            logging.error(f"❌ Error al procesar estructura de repartos: {str(e)}")
            # Continuar con mapas vacíos en lugar de fallar
            valores_map = {}
            composiciones_map = {}
        
        logging.info(f"📊 IDs de reparto disponibles en API: {sorted(valores_map.keys())}")
        
        for deposit in deposits:
            # Intentar extraer el idreparto del user_name
            if deposit.user_name:
                idreparto = extraer_idreparto_de_user_name(deposit.user_name)
                
                if idreparto is not None:
                    extracciones_exitosas += 1
                    logging.debug(f"🔍 Extraído idreparto {idreparto} de '{deposit.user_name}'")
                    
                    # Buscar el valor esperado en los datos de la API
                    if idreparto in valores_map:
                        coincidencias_encontradas += 1
                        total_esperado = int(valores_map[idreparto])
                        efectivo_esperado = int(efectivos_map.get(idreparto, 0))
                        composicion = composiciones_map.get(idreparto, "E")
                        
                        logging.debug(f"💰 Depósito {deposit.deposit_id}: actual={deposit.deposit_esperado}, esperado={total_esperado}, efectivo={efectivo_esperado}, composición={composicion}")
                        
                        # Actualizar solo si el valor o composición cambió
                        if deposit.deposit_esperado != total_esperado or deposit.composicion_esperado != composicion:
                            old_value = deposit.deposit_esperado
                            old_composicion = deposit.composicion_esperado
                            
                            deposit.deposit_esperado = total_esperado
                            deposit.efectivo_esperado = efectivo_esperado  # Guardar efectivo por separado
                            deposit.composicion_esperado = composicion
                            
                            # Actualizar estado automáticamente
                            deposit.actualizar_estado()
                            
                            actualizados += 1
                            detalles.append({
                                "deposit_id": deposit.deposit_id,
                                "user_name": deposit.user_name,
                                "idreparto": idreparto,
                                "old_expected": old_value,
                                "new_expected": total_esperado,
                                "old_composicion": old_composicion,
                                "new_composicion": composicion,
                                "estado": deposit.estado.value
                            })
                            
                            logging.info(f"💰 Actualizado {deposit.deposit_id}: {old_value} -> {total_esperado}, composición: {old_composicion} -> {composicion} (idreparto: {idreparto})")
                        else:
                            logging.debug(f"✓ Depósito {deposit.deposit_id} ya tiene el valor y composición correctos: {total_esperado} ({composicion})")
                    else:
                        logging.warning(f"⚠️ No se encontró valor para idreparto {idreparto} en API externa (user_name: '{deposit.user_name}')")
                else:
                    logging.warning(f"⚠️ No se pudo extraer idreparto de user_name '{deposit.user_name}'")
        
        # Guardar cambios
        db.commit()
        db.close()
        
        logging.info(f"📈 Estadísticas de procesamiento:")
        logging.info(f"  - Depósitos procesados: {len(deposits)}")
        logging.info(f"  - Extracciones exitosas: {extracciones_exitosas}")
        logging.info(f"  - Coincidencias encontradas: {coincidencias_encontradas}")
        logging.info(f"  - Actualizaciones realizadas: {actualizados}")
        
        resultado = {
            "status": "ok",
            "message": f"Procesamiento completado para {fecha_str}",
            "fecha": fecha_str,
            "repartos_api": len(repartos_valores),
            "depositos_encontrados": len(deposits),
            "extracciones_exitosas": extracciones_exitosas,
            "coincidencias_encontradas": coincidencias_encontradas,
            "actualizados": actualizados,
            "detalles": detalles
        }
        
        logging.info(f"✅ Actualización completada: {actualizados} depósitos actualizados")
        
        return resultado
        
    except Exception as e:
        logging.error(f"❌ Error al actualizar depósitos esperados: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "actualizados": 0
        }

def generar_composicion_esperado(reparto_data: Dict) -> str:
    """
    Genera la composición del valor esperado usando E (efectivo), C (cheques), R (retenciones)
    
    Args:
        reparto_data: Diccionario con los datos del reparto de la API externa
        
    Returns:
        String con la composición (ej: "E", "ECR", "ER", etc.)
    """
    composicion = ""
    
    # Verificar efectivo
    efectivo = reparto_data.get("efectivo", 0) or reparto_data.get("Efectivo", 0)
    if efectivo and efectivo > 0:
        composicion += "E"
    
    # Verificar cheques
    cheques = reparto_data.get("cheques", 0) or reparto_data.get("Cheques", 0)
    if cheques and cheques > 0:
        composicion += "C"
    
    # Verificar retenciones
    retenciones = reparto_data.get("retenciones", 0) or reparto_data.get("Retenciones", 0)
    if retenciones and retenciones > 0:
        composicion += "R"
    
    return composicion if composicion else "E"  # Default a "E" si no hay nada

def obtener_composicion_por_idreparto(fecha: str) -> Dict[int, str]:
    """
    Obtiene un mapa de idreparto -> composición para una fecha específica
    
    Args:
        fecha: Fecha en formato "DD/MM/YYYY"
        
    Returns:
        Diccionario con idreparto como clave y composición como valor
    """
    repartos = get_repartos_valores(fecha)
    composiciones = {}
    
    for reparto in repartos:
        # Buscar la clave correcta para idreparto
        id_key = None
        for key in ['idreparto', 'IdReparto', 'id_reparto', 'ID', 'id']:
            if key in reparto:
                id_key = key
                break
        
        if id_key:
            idreparto = int(reparto[id_key])
            composicion = generar_composicion_esperado(reparto)
            composiciones[idreparto] = composicion
    
    return composiciones
