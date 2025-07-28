import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
from database import SessionLocal
from models.deposit import Deposit
from models.cheque_retencion import Cheque, Retencion
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
import time
import xml.etree.ElementTree as ET

class RepartoCierreService:
    """
    Servicio para el cierre de repartos mediante API SOAP
    """
    
    def __init__(self):
        self.soap_url = "http://localhost/Service1.asmx"  # URL del servicio SOAP
        self.soap_namespace = "http://airtech-it.com.ar/"
        
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
                # Obtener cheques y retenciones asociados
                cheques = db.query(Cheque).filter(
                    Cheque.deposit_id == str(deposit.deposit_id)
                ).all()
                
                retenciones = db.query(Retencion).filter(
                    Retencion.deposit_id == str(deposit.deposit_id)
                ).all()
                
                # Determinar planta basada en identifier
                planta = self._get_planta_from_identifier(deposit.identifier)
                
                # Usar el valor esperado como efectivo (no el real)
                efectivo_importe = str(deposit.deposit_esperado or deposit.total_amount)
                
                reparto_data = {
                    "id": deposit.id,
                    "deposit_id": deposit.deposit_id,
                    "idreparto": self._clean_reparto_id(deposit.deposit_id),
                    "fecha": deposit.date_time.strftime("%d/%m/%Y") if deposit.date_time else datetime.now().strftime("%d/%m/%Y"),
                    "efectivo_importe": efectivo_importe,
                    "usuario": deposit.user_name or "SISTEMA",
                    "cheques": [self._format_cheque(c) for c in cheques],
                    "retenciones": [self._format_retencion(r) for r in retenciones],
                    "planta": planta,
                    "cajero": deposit.identifier,
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
        return {
            "nrocta": cheque.nrocta or 1,
            "concepto": "CHE",
            "banco": cheque.banco or "",
            "sucursal": cheque.sucursal or "001",
            "localidad": cheque.localidad or "1234",
            "nro_cheque": cheque.nro_cheque or "",
            "nro_cuenta": cheque.nro_cuenta or 1234,
            "titular": cheque.titular or "",
            "fecha": cheque.fecha if cheque.fecha else datetime.now().strftime("%d/%m/%Y"),
            "importe": float(cheque.importe)
        }
    
    def _format_retencion(self, retencion: Retencion) -> Dict:
        """
        Formatea una retención para el envío SOAP
        """
        return {
            "nrocta": retencion.nrocta or 1,
            "concepto": retencion.concepto or "RIB",
            "nro_retencion": retencion.nro_retencion or "",
            "fecha": retencion.fecha if retencion.fecha else datetime.now().strftime("%d/%m/%Y"),
            "importe": float(retencion.importe)
        }
    
    def _build_soap_envelope(self, reparto_data: Dict) -> str:
        """
        Construye el envelope SOAP para el cierre de reparto
        """
        # Convertir arrays a JSON strings para envío
        retenciones_json = json.dumps(reparto_data["retenciones"])
        cheques_json = json.dumps(reparto_data["cheques"])
        
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
      <retenciones>{retenciones_json}</retenciones>
      <cheques>{cheques_json}</cheques>
      <usuario>{reparto_data["usuario"]}</usuario>
    </reparto_cerrar>
  </soap12:Body>
</soap12:Envelope>"""
        
        return soap_envelope
    
    def enviar_reparto(self, reparto_data: Dict) -> Dict:
        """
        Envía un reparto individual a la API SOAP
        """
        try:
            soap_envelope = self._build_soap_envelope(reparto_data)
            
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': f'{self.soap_namespace}reparto_cerrar'
            }
            
            print(f"🔄 Enviando reparto ID: {reparto_data['idreparto']} (Planta: {reparto_data['planta']})")
            print(f"📦 Efectivo: ${reparto_data['efectivo_importe']}, Cheques: {len(reparto_data['cheques'])}, Retenciones: {len(reparto_data['retenciones'])}")
            
            # TODO: Descomentar cuando esté listo para producción
            # response = requests.post(
            #     self.soap_url,
            #     data=soap_envelope,
            #     headers=headers,
            #     timeout=30
            # )
            
            # SIMULACIÓN para desarrollo - eliminar en producción
            print("⚠️ MODO SIMULACIÓN - No se envía a producción")
            response_mock = type('Response', (), {
                'status_code': 200,
                'text': '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:airtech="http://airtech-it.com.ar/"><soap:Body><airtech:reparto_cerrarResponse><airtech:reparto_cerrarResult>OK</airtech:reparto_cerrarResult></airtech:reparto_cerrarResponse></soap:Body></soap:Envelope>'
            })()
            
            response = response_mock
            # FIN SIMULACIÓN
            
            if response.status_code == 200:
                # Parsear respuesta SOAP
                try:
                    root = ET.fromstring(response.text)
                    # Buscar el resultado en la respuesta
                    result_element = root.find('.//{http://airtech-it.com.ar/}reparto_cerrarResult')
                    result = result_element.text if result_element is not None else "UNKNOWN"
                    
                    if result == "OK":
                        # Actualizar estado a ENVIADO
                        self._actualizar_estado_reparto(reparto_data["id"], "ENVIADO")
                        
                        return {
                            "success": True,
                            "reparto_id": reparto_data["idreparto"],
                            "message": "Reparto enviado exitosamente",
                            "soap_result": result
                        }
                    else:
                        return {
                            "success": False,
                            "reparto_id": reparto_data["idreparto"],
                            "error": f"Error en respuesta SOAP: {result}",
                            "soap_response": response.text
                        }
                        
                except ET.ParseError as e:
                    return {
                        "success": False,
                        "reparto_id": reparto_data["idreparto"],
                        "error": f"Error al parsear respuesta SOAP: {e}",
                        "soap_response": response.text
                    }
            else:
                return {
                    "success": False,
                    "reparto_id": reparto_data["idreparto"],
                    "error": f"Error HTTP {response.status_code}",
                    "soap_response": response.text
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "reparto_id": reparto_data["idreparto"],
                "error": "Timeout al conectar con el servicio SOAP"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "reparto_id": reparto_data["idreparto"],
                "error": f"Error de conexión: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "reparto_id": reparto_data["idreparto"],
                "error": f"Error inesperado: {str(e)}"
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
