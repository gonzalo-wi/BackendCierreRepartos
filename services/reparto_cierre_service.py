import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from database import SessionLocal
from models.deposit import Deposit
from models.cheque_retencion import Cheque, Retencion
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
import time
import xml.etree.ElementTree as ET
import logging

class RepartoCierreService:
    """
    Servicio para el cierre de repartos mediante API SOAP
    """
    
    def __init__(self):
        self.soap_url = "http://192.168.0.8:8097/service1.asmx"  
        self.soap_namespace = "http://airtech-it.com.ar/"
        
        self.production_mode = os.getenv("REPARTO_CIERRE_PRODUCTION", "False").lower() == "true"
        self.default_usuario = "BACKEND_SYSTEM"  
        
        
        modo = "PRODUCCIÓN" if self.production_mode else "DESARROLLO"
        logging.info(f"🔧 RepartoCierreService inicializado en modo {modo}")
        logging.info(f"📡 URL SOAP: {self.soap_url}")
        
    def get_repartos_listos(self, fecha_especifica: Optional[datetime] = None) -> List[Dict]:
        """
        Obtiene todos los depósitos con estado LISTO para enviar
        Si se especifica fecha_especifica, filtra solo los de ese día
        """
        db = SessionLocal()
        try:
            # Construir query base
            query = db.query(Deposit).filter(Deposit.estado == "LISTO")
            
            # Si se especifica una fecha, filtrar por ese día
            if fecha_especifica:
                fecha_inicio = fecha_especifica.replace(hour=0, minute=0, second=0, microsecond=0)
                fecha_fin = fecha_inicio.replace(hour=23, minute=59, second=59, microsecond=999999)
                query = query.filter(
                    Deposit.date_time >= fecha_inicio,
                    Deposit.date_time <= fecha_fin
                )
            
            deposits = query.order_by(Deposit.date_time).all()
            
            repartos_listos = []
            
            for deposit in deposits:
                # Obtener cheques y retenciones asociados usando la relación ORM
                cheques = deposit.cheques
                retenciones = deposit.retenciones
                
                # Determinar planta basada en identifier
                planta = self._get_planta_from_identifier(deposit.identifier)
                
                # Extraer idreparto del user_name
                idreparto = self._extract_idreparto_from_user_name(deposit.user_name)
                if idreparto is None:
                    # Fallback: usar deposit_id si no se puede extraer del user_name
                    idreparto = self._clean_reparto_id(deposit.deposit_id)
                    logging.warning(f"⚠️ No se pudo extraer idreparto de user_name '{deposit.user_name}', usando deposit_id: {idreparto}")
                
                # Usar el valor esperado como efectivo (no el real)
                efectivo_importe = str(deposit.deposit_esperado or deposit.total_amount)
                
                reparto_data = {
                    "id": deposit.id,
                    "deposit_id": deposit.deposit_id,
                    "idreparto": idreparto,
                    "fecha": deposit.date_time.strftime("%d/%m/%Y") if deposit.date_time else datetime.now().strftime("%d/%m/%Y"),
                    "efectivo_importe": efectivo_importe,
                    "usuario": self.default_usuario,  # Usar usuario del sistema
                    "cheques": [self._format_cheque(c) for c in cheques],
                    "retenciones": [self._format_retencion(r) for r in retenciones],
                    "planta": planta,
                    "cajero": deposit.identifier,
                    "user_name_original": deposit.user_name,  # Guardar para debug
                    "diferencia": deposit.diferencia if hasattr(deposit, 'diferencia') else 0,
                    "monto_real": deposit.total_amount,
                    "monto_esperado": deposit.deposit_esperado
                }
                
                repartos_listos.append(reparto_data)
            
            return repartos_listos
            
        except Exception as e:
            print(f"Error al obtener repartos listos: {e}")
            return []
        finally:
            db.close()
    
    def _extract_idreparto_from_user_name(self, user_name: str) -> Optional[int]:
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
            import re
            
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

    def _get_planta_from_identifier(self, identifier: str) -> str:
        """
        Determina la planta basada en el identifier del cajero
        """
        if not identifier:
            return "unknown"
            
        planta_mapping = {
            'L-EJU-001': 'jumillano',
            'L-EJU-002': 'jumillano', 
            'L-EJU-003': 'plata',
            'L-EJU-004': 'nafa'
        }
        
        return planta_mapping.get(identifier, "unknown")
    
    def _clean_reparto_id(self, deposit_id: str) -> int:
        """
        Limpia el ID del reparto eliminando ceros a la izquierda
        Ejemplo: "009" -> 9
        """
        try:
            return int(str(deposit_id).lstrip('0')) if deposit_id else 0
        except (ValueError, TypeError):
            return 0
    
    def _format_cheque(self, cheque: Cheque) -> Dict:
        """
        Formatea un cheque para el envío SOAP
        """
        # Formatear fecha correctamente - siempre en formato dd/MM/yyyy
        fecha_formateada = datetime.now().strftime("%d/%m/%Y")
        if cheque.fecha:
            if isinstance(cheque.fecha, str):
                try:
                    # Si es string, intentar parsearlo y reformatearlo
                    fecha_obj = datetime.strptime(cheque.fecha, "%Y-%m-%d")
                    fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
                except ValueError:
                    try:
                        # Intentar otro formato común
                        fecha_obj = datetime.strptime(cheque.fecha, "%d/%m/%Y")
                        fecha_formateada = cheque.fecha  # Ya está en formato correcto
                    except ValueError:
                        # Si no se puede parsear, usar fecha actual
                        fecha_formateada = datetime.now().strftime("%d/%m/%Y")
            elif hasattr(cheque.fecha, 'strftime'):
                # Si es datetime object
                fecha_formateada = cheque.fecha.strftime("%d/%m/%Y")
        
        return {
            "nrocta": cheque.nrocta or 1,
            "concepto": cheque.concepto or "CHE",
            "banco": cheque.banco or "",
            "sucursal": cheque.sucursal or "001",
            "localidad": cheque.localidad or "1234",
            "nro_cheque": cheque.nro_cheque or "",
            "nro_cuenta": cheque.nro_cuenta or 1234,
            "titular": cheque.titular or "",
            "fecha": fecha_formateada,
            "importe": float(cheque.importe) if cheque.importe else 0.0
        }
    
    def _format_retencion(self, retencion: Retencion) -> Dict:
        """
        Formatea una retención para el envío SOAP
        """
        # Formatear fecha correctamente - siempre en formato dd/MM/yyyy
        fecha_formateada = datetime.now().strftime("%d/%m/%Y")
        if retencion.fecha:
            if isinstance(retencion.fecha, str):
                try:
                    # Si es string, intentar parsearlo y reformatearlo
                    fecha_obj = datetime.strptime(retencion.fecha, "%Y-%m-%d")
                    fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
                except ValueError:
                    try:
                        # Intentar otro formato común
                        fecha_obj = datetime.strptime(retencion.fecha, "%d/%m/%Y")
                        fecha_formateada = retencion.fecha  # Ya está en formato correcto
                    except ValueError:
                        # Si no se puede parsear, usar fecha actual
                        fecha_formateada = datetime.now().strftime("%d/%m/%Y")
            elif hasattr(retencion.fecha, 'strftime'):
                # Si es datetime object
                fecha_formateada = retencion.fecha.strftime("%d/%m/%Y")
        
        return {
            "nrocta": retencion.nrocta or 1,
            "concepto": retencion.concepto or "RIB",
            "nro_retencion": retencion.nro_retencion or "",
            "fecha": fecha_formateada,
            "importe": float(retencion.importe) if retencion.importe else 0.0
        }
    
    def _build_soap_envelope(self, reparto_data: Dict) -> str:
        """
        Construye el envelope SOAP para el cierre de reparto según documentación oficial
        """
        # Formatear retenciones y cheques como strings JSON
        retenciones_str = json.dumps(reparto_data["retenciones"]) if reparto_data["retenciones"] else "[]"
        cheques_str = json.dumps(reparto_data["cheques"]) if reparto_data["cheques"] else "[]"
        
        # Usar SOAP 1.2 según documentación
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <reparto_cerrar xmlns="{self.soap_namespace}">
      <idreparto>{reparto_data["idreparto"]}</idreparto>
      <fecha>{reparto_data["fecha"]}</fecha>
      <ajustar_envases>0</ajustar_envases>
      <efectivo_importe>{reparto_data["efectivo_importe"]}</efectivo_importe>
      <retenciones>{retenciones_str}</retenciones>
      <cheques>{cheques_str}</cheques>
      <usuario>{reparto_data["usuario"]}</usuario>
    </reparto_cerrar>
  </soap12:Body>
</soap12:Envelope>"""
        
        logging.debug(f"📋 SOAP Envelope generado para idreparto {reparto_data['idreparto']}")
        return soap_envelope
    
    def enviar_reparto(self, reparto_data: Dict) -> Dict:
        """
        Envía un reparto individual a la API SOAP
        """
        try:
            soap_envelope = self._build_soap_envelope(reparto_data)
            
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': f'{self.soap_namespace}reparto_cerrar',
                'Host': '192.168.0.8',
                'Content-Length': str(len(soap_envelope))
            }
            
            logging.info(f"🔄 Enviando reparto ID: {reparto_data['idreparto']} (Planta: {reparto_data['planta']})")
            logging.info(f"📦 Efectivo: ${reparto_data['efectivo_importe']}, Cheques: {len(reparto_data['cheques'])}, Retenciones: {len(reparto_data['retenciones'])}")
            
            # LOGGING TEMPORAL PARA DEBUG - Ver qué datos se están enviando
            if reparto_data['cheques']:
                logging.info(f"💳 Cheques a enviar: {reparto_data['cheques']}")
                for cheque in reparto_data['cheques']:
                    logging.info(f"   📅 Fecha cheque {cheque.get('nro_cheque', 'N/A')}: '{cheque.get('fecha', 'N/A')}'")
            if reparto_data['retenciones']:
                logging.info(f"🧾 Retenciones a enviar: {reparto_data['retenciones']}")
                for retencion in reparto_data['retenciones']:
                    logging.info(f"   📅 Fecha retención {retencion.get('nro_retencion', 'N/A')}: '{retencion.get('fecha', 'N/A')}'")
            
            logging.info(f"📋 XML SOAP completo:\n{soap_envelope}")
            logging.info("=" * 80)
            
            if self.production_mode:
                # MODO PRODUCCIÓN - Envío real a la API
                logging.info("🚀 MODO PRODUCCIÓN - Enviando a API real")
                response = requests.post(
                    self.soap_url,
                    data=soap_envelope,
                    headers=headers,
                    timeout=30
                )
                
                logging.info(f"📡 Respuesta del servidor: Status {response.status_code}")
                logging.debug(f"📡 Contenido respuesta: {response.text[:500]}...")
                
            else:
                # MODO DESARROLLO - Simulación
                logging.warning("⚠️ MODO DESARROLLO - Simulando envío (no se envía a producción)")
                logging.info(f"🔍 SOAP Envelope que se enviaría:\n{soap_envelope}")
                
                # Crear respuesta simulada
                response = type('Response', (), {
                    'status_code': 200,
                    'text': f'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <reparto_cerrarResponse xmlns="http://airtech-it.com.ar/">
      <reparto_cerrarResult>OK - SIMULADO</reparto_cerrarResult>
    </reparto_cerrarResponse>
  </soap12:Body>
</soap12:Envelope>''',
                    'raise_for_status': lambda: None
                })()
            
            response.raise_for_status()
            
            # Logging detallado de la respuesta para debug
            logging.info(f"📡 Respuesta completa del servidor:")
            logging.info(f"📡 Status: {response.status_code}")
            logging.info(f"📡 Headers: {dict(response.headers)}")
            logging.info(f"📡 Contenido (primeros 1000 chars): {response.text[:1000]}")
            
            # Parsear respuesta XML
            try:
                # Intentar limpiar el XML antes de parsearlo
                xml_content = response.text.strip()
                
                if not xml_content.startswith('<?xml') and not xml_content.startswith('<soap'):
                    logging.warning(f"⚠️ Respuesta no parece ser XML válido. Contenido: {xml_content[:200]}...")
                    
                    if "OK" in xml_content.upper() or response.status_code == 200:
                        return {
                            "success": True,
                            "idreparto": reparto_data["idreparto"],
                            "response": "OK - Respuesta no XML pero status 200",
                            "production_mode": self.production_mode,
                            "timestamp": datetime.now().isoformat(),
                            "raw_response": xml_content[:500]
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Respuesta no XML y no contiene OK: {xml_content[:200]}",
                            "idreparto": reparto_data["idreparto"],
                            "raw_response": xml_content[:500]
                        }
                
                root = ET.fromstring(xml_content)
                # Buscar el resultado en la respuesta SOAP
                result_element = root.find('.//{http://airtech-it.com.ar/}reparto_cerrarResult')
                if result_element is not None:
                    result = result_element.text
                else:
                    result = "OK"  
                    
                modo = "PRODUCCIÓN" if self.production_mode else "DESARROLLO"
                logging.info(f"✅ Reparto {reparto_data['idreparto']} enviado exitosamente ({modo}): {result}")
                
                return {
                    "success": True,
                    "idreparto": reparto_data["idreparto"],
                    "response": result,
                    "production_mode": self.production_mode,
                    "timestamp": datetime.now().isoformat()
                }
                
            except ET.ParseError as e:
                logging.error(f"❌ Error parseando respuesta XML: {str(e)}")
                logging.error(f"❌ Contenido XML problemático: {response.text[:500]}...")
                
                # Si el status es 200, podríamos considerar que fue exitoso aunque el XML esté mal
                if response.status_code == 200:
                    logging.warning("⚠️ XML malformado pero status 200 - considerando como éxito")
                    return {
                        "success": True,
                        "idreparto": reparto_data["idreparto"],
                        "response": "OK - XML malformado pero status 200",
                        "production_mode": self.production_mode,
                        "timestamp": datetime.now().isoformat(),
                        "xml_error": str(e),
                        "raw_response": response.text[:500]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error parseando respuesta: {str(e)}",
                        "idreparto": reparto_data["idreparto"],
                        "xml_error": str(e),
                        "raw_response": response.text[:500]
                    }
                
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Error de conexión enviando reparto {reparto_data['idreparto']}: {str(e)}")
            return {
                "success": False,
                "error": f"Error de conexión: {str(e)}",
                "idreparto": reparto_data["idreparto"]
            }
        except Exception as e:
            logging.error(f"❌ Error inesperado enviando reparto {reparto_data['idreparto']}: {str(e)}")
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
                "idreparto": reparto_data["idreparto"]
            }
    
    def _actualizar_estado_reparto(self, deposit_db_id: int, nuevo_estado: str) -> bool:
        """
        Actualiza el estado de un reparto en la base de datos
        """
        db = SessionLocal()
        try:
            deposit = db.query(Deposit).filter(Deposit.id == deposit_db_id).first()
            if deposit:
                deposit.estado = nuevo_estado
                deposit.fecha_envio = datetime.now() if nuevo_estado == "ENVIADO" else None
                db.commit()
                print(f"✅ Estado actualizado a {nuevo_estado} para depósito ID: {deposit.deposit_id}")
                return True
            else:
                print(f"⚠️ No se encontró depósito con ID: {deposit_db_id}")
                return False
        except Exception as e:
            db.rollback()
            print(f"❌ Error al actualizar estado: {e}")
            return False
        finally:
            db.close()
    
    def procesar_cola_repartos(self, fecha_especifica: Optional[datetime] = None, max_reintentos: int = 3, delay_entre_envios: float = 1.0) -> Dict:
        """
        Procesa la cola completa de repartos listos para enviar
        Si se especifica fecha_especifica, solo procesa los repartos de ese día
        """
        fecha_str = fecha_especifica.strftime("%d/%m/%Y") if fecha_especifica else "todos los días"
        print(f"🚀 Iniciando proceso de cierre de repartos para: {fecha_str}")
        
        repartos_listos = self.get_repartos_listos(fecha_especifica)
        
        if not repartos_listos:
            return {
                "success": True,
                "message": "No hay repartos listos para enviar",
                "total_repartos": 0,
                "enviados": 0,
                "errores": 0,
                "resultados": []
            }
        
        print(f"📋 Se encontraron {len(repartos_listos)} repartos listos para enviar")
        
        resultados = []
        enviados = 0
        errores = 0
        
        for reparto in repartos_listos:
            print(f"\n--- Procesando reparto {reparto['idreparto']} ---")
            
            # Intentar envío con reintentos
            resultado = None
            for intento in range(max_reintentos):
                resultado = self.enviar_reparto(reparto)
                
                if resultado["success"]:
                    enviados += 1
                    print(f"✅ Reparto {reparto['idreparto']} enviado exitosamente")
                    
                    # Actualizar estado de los depósitos a ENVIADO
                    self._actualizar_estado_depositos_enviados(reparto['idreparto'])
                    
                    break
                else:
                    print(f"❌ Intento {intento + 1}/{max_reintentos} falló: {resultado['error']}")
                    if intento < max_reintentos - 1:
                        print(f"⏳ Esperando {delay_entre_envios}s antes del siguiente intento...")
                        time.sleep(delay_entre_envios)
            
            if not resultado["success"]:
                errores += 1
                print(f"💥 Reparto {reparto['idreparto']} falló después de {max_reintentos} intentos")
            
            resultados.append({
                "reparto_id": reparto['idreparto'],
                "planta": reparto['planta'],
                "efectivo": reparto['efectivo_importe'],
                "cheques_count": len(reparto['cheques']),
                "retenciones_count": len(reparto['retenciones']),
                "resultado": resultado
            })
            
            # Pequeña pausa entre envíos para no sobrecargar el servidor
            if delay_entre_envios > 0:
                time.sleep(delay_entre_envios)
        
        resumen = {
            "success": errores == 0,
            "message": f"Proceso completado. {enviados} enviados, {errores} errores",
            "total_repartos": len(repartos_listos),
            "enviados": enviados,
            "errores": errores,
            "resultados": resultados,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n🏁 Resumen final:")
        print(f"📊 Total: {len(repartos_listos)} | ✅ Enviados: {enviados} | ❌ Errores: {errores}")
        
        return resumen
    
    def _get_current_timestamp(self):
        """Helper method para obtener timestamp actual"""
        return datetime.now().isoformat()
    
    def get_resumen_repartos_por_fecha(self) -> Dict:
        """
        Obtiene un resumen de repartos LISTO agrupados por fecha
        """
        db = SessionLocal()
        try:
            deposits = db.query(Deposit).filter(Deposit.estado == "LISTO").all()
            
            resumen_por_fecha = {}
            
            for deposit in deposits:
                if deposit.date_time:
                    fecha_str = deposit.date_time.strftime("%Y-%m-%d")
                    if fecha_str not in resumen_por_fecha:
                        resumen_por_fecha[fecha_str] = {
                            "fecha": fecha_str,
                            "fecha_display": deposit.date_time.strftime("%d/%m/%Y"),
                            "total_repartos": 0,
                            "plantas": {}
                        }
                    
                    resumen_por_fecha[fecha_str]["total_repartos"] += 1
                    
                    # Agrupar por planta
                    planta = self._get_planta_from_identifier(deposit.identifier)
                    if planta not in resumen_por_fecha[fecha_str]["plantas"]:
                        resumen_por_fecha[fecha_str]["plantas"][planta] = 0
                    resumen_por_fecha[fecha_str]["plantas"][planta] += 1
            
            # Convertir a lista y ordenar por fecha
            resumen_lista = list(resumen_por_fecha.values())
            resumen_lista.sort(key=lambda x: x["fecha"], reverse=True)
            
            return {
                "total_fechas": len(resumen_lista),
                "total_repartos_listos": sum(item["total_repartos"] for item in resumen_lista),
                "fechas": resumen_lista
            }
            
        except Exception as e:
            print(f"Error al obtener resumen por fechas: {e}")
            return {"total_fechas": 0, "total_repartos_listos": 0, "fechas": []}
        finally:
            db.close()

    def _actualizar_estado_depositos_enviados(self, idreparto: int):
        """
        Actualiza el estado de los depósitos de un reparto específico a ENVIADO
        después de que el envío SOAP haya sido exitoso
        """
        from database import SessionLocal
        from models.deposit import Deposit, EstadoDeposito
        from services.repartos_api_service import extraer_idreparto_de_user_name
        
        db = SessionLocal()
        try:
            # Buscar todos los depósitos que están en estado LISTO
            depositos_listo = db.query(Deposit).filter(
                Deposit.estado == EstadoDeposito.LISTO
            ).all()
            
            actualizados = 0
            for deposito in depositos_listo:
                # Usar la función existente para extraer idreparto del user_name
                idreparto_extraido = extraer_idreparto_de_user_name(deposito.user_name)
                
                if idreparto_extraido == idreparto:
                    deposito.estado = EstadoDeposito.ENVIADO
                    actualizados += 1
                    logging.info(f"🔄 Depósito {deposito.deposit_id} (user_name: '{deposito.user_name}') actualizado a ENVIADO")
            
            db.commit()
            
            if actualizados > 0:
                logging.info(f"✅ {actualizados} depósitos actualizados a ENVIADO para reparto {idreparto}")
            else:
                logging.warning(f"⚠️ No se encontraron depósitos LISTO para reparto {idreparto}")
                
        except Exception as e:
            logging.error(f"❌ Error al actualizar estado de depósitos para reparto {idreparto}: {str(e)}")
            db.rollback()
        finally:
            db.close()
