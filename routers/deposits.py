"""
Router para endpoints de consulta de depósitos desde miniBank
"""
from datetime import datetime
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional
from schemas.requests import StatusUpdateRequest, ExpectedAmountUpdateRequest

# Importar utilidades de logging
from utils.logging_utils import log_user_action, log_technical_error, log_technical_warning
from middleware.logging_middleware import log_endpoint_access
from services.deposits_service import (
    get_deposits,
    get_jumillano_deposits,
    get_plata_deposits,
    get_nafa_deposits,
    get_all_deposits,
    get_jumillano_total,
    get_plata_total,
    get_nafa_total,
    get_all_totals
)
from services.deposits_mapper import map_deposit_to_reparto
from services.repartos_api_service import actualizar_depositos_esperados

router = APIRouter(
    prefix="/deposits",
    tags=["deposits"]
)


# Helpers locales para normalizar campos numéricos provenientes del frontend
def _extract_int(value, default: int | None = None) -> Optional[int]:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        s = str(value).strip()
        if s.isdigit():
            return int(s)
        import re
        m = re.search(r"\d+", s)
        if m:
            return int(m.group(0))
    except Exception:
        pass
    return default


def _digits_str(value, default: str = "") -> str:
    """Devuelve solo dígitos en forma de string. Si no hay, retorna default."""
    if value is None:
        return default
    s = str(value)
    import re
    digits = "".join(re.findall(r"\d+", s))
    return digits if digits else default


@router.get("")
@log_endpoint_access("VIEW_DEPOSITS", "deposits")
def deposits(request: Request, stIdentifier: str = Query(...), date: str = Query(...)):
    try:
        # Log de la acción específica
        log_user_action(
            action="VIEW_DEPOSITS_BY_IDENTIFIER",
            resource="deposits",
            request=request,
            extra_data={
                "identifier": stIdentifier,
                "date": date,
                "query_type": "by_identifier"
            }
        )
        
        data = get_deposits(stIdentifier, date)
        
        return JSONResponse(content=data)
    except Exception as e:
        # Log del error técnico
        log_technical_error(
            e, 
            "get_deposits_endpoint",
            request=request,
            extra_data={
                "identifier": stIdentifier,
                "date": date
            }
        )
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/jumillano")
@log_endpoint_access("VIEW_JUMILLANO_DEPOSITS", "deposits")
def deposits_jumillano(request: Request, date: str = Query(...)):
    try:
        # Log de inicio de consulta
        log_user_action(
            action="VIEW_JUMILLANO_DEPOSITS",
            resource="deposits",
            request=request,
            extra_data={"date": date, "plant": "jumillano"}
        )
        
        # Obtener datos de miniBank
        data = get_jumillano_deposits(date)
        
        # Auto-sincronizar valores esperados desde API externa
        try:
            print(f"🔄 Auto-sincronizando valores esperados para Jumillano {date}...")
            resultado_sync = actualizar_depositos_esperados(date)
            print(f"💰 Sincronización: {resultado_sync.get('actualizados', 0)} depósitos actualizados")
            
            # Log de sincronización exitosa
            log_user_action(
                action="AUTO_SYNC_EXPECTED_AMOUNTS",
                resource="deposits",
                request=request,
                extra_data={
                    "date": date,
                    "plant": "jumillano", 
                    "updated_deposits": resultado_sync.get('actualizados', 0)
                }
            )
            
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            # Log de advertencia técnica
            log_technical_warning(
                f"Fallo en auto-sincronización de valores esperados: {str(sync_error)}",
                "auto_sync_expected_amounts",
                request=request,
                extra_data={"date": date, "plant": "jumillano"}
            )
        
        return JSONResponse(content=data)
    except Exception as e:
        # Log del error técnico
        log_technical_error(
            e,
            "get_jumillano_deposits_endpoint", 
            request=request,
            extra_data={"date": date, "plant": "jumillano"}
        )
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/nafa")
def deposits_nafa(date: str = Query(...)):
    try:
        # Obtener datos de miniBank
        data = get_nafa_deposits(date)
        
        # Auto-sincronizar valores esperados desde API externa
        try:
            print(f"🔄 Auto-sincronizando valores esperados para Nafa {date}...")
            resultado_sync = actualizar_depositos_esperados(date)
            print(f"💰 Sincronización: {resultado_sync.get('actualizados', 0)} depósitos actualizados")
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            # Continuar aunque falle la sincronización
        
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/plata")
def deposits_plata(date: str = Query(...)):
    try:
        # Obtener datos de miniBank
        data = get_plata_deposits(date)
        
        # Auto-sincronizar valores esperados desde API externa
        try:
            print(f"🔄 Auto-sincronizando valores esperados para La Plata {date}...")
            resultado_sync = actualizar_depositos_esperados(date)
            print(f"💰 Sincronización: {resultado_sync.get('actualizados', 0)} depósitos actualizados")
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            # Continuar aunque falle la sincronización
        
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/all")
def deposits_all(date: str = Query(...)):
    try:
        # Obtener datos de miniBank
        data = get_all_deposits(date)
        
        # Auto-sincronizar valores esperados desde API externa
        try:
            print(f"🔄 Auto-sincronizando valores esperados para {date}...")
            resultado_sync = actualizar_depositos_esperados(date)
            print(f"💰 Sincronización: {resultado_sync.get('actualizados', 0)} depósitos actualizados")
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            # Continuar aunque falle la sincronización
        
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/all/sync")
def get_all_deposits_with_sync(date: str = Query(None)):
    """
    Obtiene todos los depósitos y sincroniza automáticamente si es hoy
    """
    try:
        from services.deposits_service import save_deposits_to_db
        
        # Si no se proporciona fecha, usar hoy
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"🔄 Obteniendo depósitos con auto-sync para: {date}")
        
        # Obtener datos
        data = get_all_deposits(date)
        
        # Si es hoy, sincronizar automáticamente
        today = datetime.now().strftime("%Y-%m-%d")
        if date == today:
            save_deposits_to_db(data)
            print("📊 Datos de hoy sincronizados automáticamente en BD")
        
        return {
            "status": "ok",
            "date": date,
            "auto_synced": date == today,
            "data": data
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


# ENDPOINTS DE COMPATIBILIDAD HACIA ATRÁS
# Para mantener URLs que el frontend espera

@router.get("/db/by-plant")
def get_deposits_from_db_by_plant_compat(date: str = Query(...)):
    """
    COMPATIBILIDAD: Redirige a la nueva ubicación en /api/db/deposits/by-plant
    """
    from routers.database import get_deposits_from_db_by_plant
    return get_deposits_from_db_by_plant(date)


@router.get("/db/by-machine") 
def get_deposits_from_db_by_machine_compat(date: str = Query(...)):
    """
    COMPATIBILIDAD: Redirige a la nueva ubicación en /api/db/deposits/by-machine
    """
    from routers.database import get_deposits_from_db_by_machine
    return get_deposits_from_db_by_machine(date)


@router.get("/db/dates")
def get_available_dates_compat():
    """
    COMPATIBILIDAD: Redirige a la nueva ubicación en /api/db/deposits/dates
    """
    from routers.database import get_available_dates
    return get_available_dates()


@router.get("/db/summary")
def get_db_summary_compat():
    """
    COMPATIBILIDAD: Redirige a la nueva ubicación en /api/db/deposits/summary
    """
    from routers.database import get_db_summary
    return get_db_summary()


@router.put("/db/{deposit_id}/status")
def update_deposit_status_compat(deposit_id: str, request: dict):
    """
    COMPATIBILIDAD: Redirige a la nueva ubicación en /api/db/deposits/{id}/status
    """
    from routers.database import update_deposit_status
    from schemas.requests import StatusUpdateRequest
    status_request = StatusUpdateRequest(**request)
    return update_deposit_status(deposit_id, status_request)


@router.put("/db/{deposit_id}/expected-amount")
def update_deposit_expected_amount_compat(deposit_id: str, request: dict):
    """
    COMPATIBILIDAD: Redirige a la nueva ubicación en /api/db/deposits/{id}/expected-amount
    """
    from routers.database import update_deposit_expected_amount
    from schemas.requests import ExpectedAmountUpdateRequest
    amount_request = ExpectedAmountUpdateRequest(**request)
    return update_deposit_expected_amount(deposit_id, amount_request)


# ENDPOINTS PARA COMPATIBILIDAD CON FRONTEND
# El frontend espera estos endpoints en /api/deposits/

@router.put("/{deposit_id}/status")
def update_deposit_status_frontend(deposit_id: str, request: StatusUpdateRequest):
    """
    FRONTEND COMPATIBILITY: Actualiza el estado de un depósito
    El frontend espera este endpoint en /api/deposits/{id}/status
    """
    from routers.database import update_deposit_status
    return update_deposit_status(deposit_id, request)


@router.put("/{deposit_id}/expected-amount")
def update_deposit_expected_amount_frontend(deposit_id: str, request: ExpectedAmountUpdateRequest):
    """
    FRONTEND COMPATIBILITY: Actualiza el monto esperado de un depósito
    El frontend espera este endpoint en /api/deposits/{id}/expected-amount
    """
    from routers.database import update_deposit_expected_amount
    return update_deposit_expected_amount(deposit_id, request)


@router.put("/{deposit_id}/mark-sent")
def mark_deposit_as_sent_frontend(deposit_id: str):
    """
    FRONTEND COMPATIBILITY: Marca un depósito como ENVIADO
    El frontend espera este endpoint en /api/deposits/{id}/mark-sent
    """
    from routers.database import mark_deposit_as_sent
    return mark_deposit_as_sent(deposit_id)


@router.get("/states")
def get_available_states_frontend():
    """
    FRONTEND COMPATIBILITY: Obtiene los estados disponibles
    El frontend espera este endpoint en /api/deposits/states
    """
    from routers.database import get_available_states
    return get_available_states()


# TAMBIÉN AGREGAR ENDPOINTS DE SINCRONIZACIÓN QUE EL FRONTEND PODRÍA USAR

@router.post("/sync-expected-amounts")
def sync_expected_amounts_frontend(date: str = Query(...)):
    """
    FRONTEND COMPATIBILITY: Sincroniza los montos esperados desde la API externa
    """
    from routers.sync import sync_expected_amounts
    return sync_expected_amounts(date)


# ============================================================================
# MODELOS PYDANTIC PARA CHEQUES Y RETENCIONES (COMPATIBLES CON FRONTEND)
# ============================================================================

# Modelos que el frontend actual envía
class ChequeCreate(BaseModel):
    numero: Optional[str] = None  # Se mapea a nro_cheque
    banco: str  # REQUERIDO
    importe: float  # REQUERIDO
    fecha_cobro: Optional[str] = None  # Se mapea a fecha
    nrocta: Optional[int] = None  # Número de cuenta del cliente
    nro_cuenta: Optional[int] = None  # Número de cuenta del cheque
    sucursal: Optional[str] = None  # Sucursal del banco
    localidad: Optional[str] = None  # Localidad
    # Campos adicionales que el usuario ingresa en el modal
    nrocta: Optional[int] = None  # Número de cuenta del cliente
    nro_cuenta: Optional[int] = None  # Número de cuenta del cheque
    sucursal: Optional[str] = None  # Sucursal del banco
    localidad: Optional[str] = None  # Localidad

class RetencionCreate(BaseModel):
    tipo: Optional[str] = None  # Campo del frontend
    numero: Optional[object] = None  # Acepta int o str; se mapea a nro_retencion
    importe: object  # Acepta float o str numérico
    concepto: Optional[str] = None
    numero_cuenta: Optional[object] = None  # Acepta int o str; se mapea a nrocta

    # Normaliza strings vacíos a None en campos de texto
    @field_validator('tipo', 'concepto', mode='before')
    @classmethod
    def _empty_str_to_none(cls, v):
        if isinstance(v, str):
            v2 = v.strip()
            return v2 if v2 != '' else None
        return v

    # Permite que 'numero' sea int, str numérico o str libre; '' -> None
    @field_validator('numero', mode='before')
    @classmethod
    def _normalize_numero(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v2 = v.strip()
            if v2 == '':
                return None
            # Dejar strings no numéricos tal cual (el modelo de BD guarda string)
            if v2.isdigit():
                try:
                    return int(v2)
                except Exception:
                    return v2
            return v2
        return v

    # Permite que 'numero_cuenta' sea int o str numérico; otros -> None
    @field_validator('numero_cuenta', mode='before')
    @classmethod
    def _normalize_numero_cuenta(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v2 = v.strip()
            if v2 == '':
                return None
            if v2.isdigit():
                try:
                    return int(v2)
                except Exception:
                    return None
            return None
        return v

    # Acepta importe como float o str (con coma o punto). '' -> error claro
    @field_validator('importe', mode='before')
    @classmethod
    def _normalize_importe(cls, v):
        if v is None:
            raise ValueError('importe es requerido')
        if isinstance(v, str):
            v2 = v.replace(',', '.').strip()
            if v2 == '':
                raise ValueError('importe es requerido')
            try:
                return float(v2)
            except Exception:
                raise ValueError('importe debe ser numérico')
        return v

# ============================================================================
# ENDPOINTS PARA CREAR CHEQUES Y RETENCIONES
# ============================================================================

@router.post("/{deposit_id}/cheques")
def create_deposit_cheque(deposit_id: str, cheque: ChequeCreate):
    """
    Crea un nuevo cheque asociado a un depósito (COMPATIBLE CON FRONTEND)
    """
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Cheque
    from fastapi import HTTPException
    from typing import Optional
    
    db = SessionLocal()
    try:
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")
        
        # Mapear campos del frontend a campos de BD (compatibilidad)
        nro_cheque_value = cheque.numero or "SIN_NUMERO"
        fecha_value = cheque.fecha_cobro or datetime.now().strftime("%d/%m/%Y")
        
        # Convertir formato de fecha si viene como YYYY-MM-DD
        if fecha_value and "-" in fecha_value:
            try:
                fecha_obj = datetime.strptime(fecha_value, "%Y-%m-%d")
                fecha_value = fecha_obj.strftime("%d/%m/%Y")
            except:
                pass  # Mantener formato original si falla conversión
        
        # Normalizar numericos requeridos por SOAP: banco/sucursal/localidad deben ser numéricos
        banco_norm = _extract_int(cheque.banco, 0)
        sucursal_norm = _extract_int(cheque.sucursal, 0) if cheque.sucursal is not None else 0
        localidad_norm = _extract_int(cheque.localidad, 0) if cheque.localidad is not None else 0

        nuevo_cheque = Cheque(
            deposit_id=deposit.deposit_id,
            nrocta=cheque.nrocta or 1,  # Usar valor del frontend o default
            concepto="CHE",  # Valor por defecto
            banco=str(banco_norm),
            sucursal=str(sucursal_norm or 0).zfill(1),  # guardamos como string numérica
            localidad=str(localidad_norm or 0),  # string numérica
            nro_cheque=nro_cheque_value,
            nro_cuenta=cheque.nro_cuenta or 1234,  # Usar valor del frontend o default
            titular="",  # Valor por defecto (vacío como está en el modelo)
            fecha=fecha_value,
            importe=float(cheque.importe)
        )
        
        db.add(nuevo_cheque)
        db.commit()
        db.refresh(nuevo_cheque)
        
        return {
            "success": True,
            "message": "Cheque creado exitosamente",
            "cheque": {
                "nrocta": nuevo_cheque.nrocta,
                "concepto": nuevo_cheque.concepto,
                "banco": nuevo_cheque.banco,
                "sucursal": nuevo_cheque.sucursal,
                "localidad": nuevo_cheque.localidad,
                "nro_cheque": nuevo_cheque.nro_cheque,
                "nro_cuenta": nuevo_cheque.nro_cuenta,
                "titular": nuevo_cheque.titular,
                "fecha": nuevo_cheque.fecha,
                "importe": float(nuevo_cheque.importe)
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear cheque: {str(e)}")
    finally:
        db.close()


@router.post("/{deposit_id}/retenciones")
def create_deposit_retencion(deposit_id: str, retencion: RetencionCreate):
    """
    Crea una nueva retención asociada a un depósito (COMPATIBLE CON FRONTEND)
    """
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Retencion
    from fastapi import HTTPException
    from typing import Optional
    
    db = SessionLocal()
    try:
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")

        # Mapear campos del frontend a campos de BD (compatibilidad)
        # nro_retencion debe ser numérico para SOAP
        nro_retencion_value = _digits_str(retencion.numero, default="")
        concepto_value = retencion.concepto or "RIB"

        # DEBUG: Log para ver qué datos llegan del frontend
        print(f"🔍 DEBUG RETENCIÓN - Datos recibidos:")
        print(f"   numero: {retencion.numero}")
        print(f"   importe: {retencion.importe}")
        print(f"   concepto: {retencion.concepto}")
        print(f"   numero_cuenta: {getattr(retencion, 'numero_cuenta', 'NO_PRESENTE')}")
        print(f"   hasattr numero_cuenta: {hasattr(retencion, 'numero_cuenta')}")
        
        # Manejar numero_cuenta
        nrocta_value = 1  # Default
        if hasattr(retencion, 'numero_cuenta') and retencion.numero_cuenta is not None:
            try:
                nrocta_value = int(retencion.numero_cuenta)
                print(f"✅ Usando numero_cuenta del frontend: {nrocta_value}")
            except (ValueError, TypeError):
                nrocta_value = 1  # Default fallback
                print(f"⚠️ Error al convertir numero_cuenta, usando default: 1")
        else:
            print(f"⚠️ No se encontró numero_cuenta en los datos, usando default: 1")
        
        nueva_retencion = Retencion(
            deposit_id=deposit_id,
            nrocta=nrocta_value,
            concepto=retencion.concepto or "RIB",
            nro_retencion=nro_retencion_value,
            fecha=datetime.now(),
            importe=retencion.importe
        )
        
        db.add(nueva_retencion)
        db.commit()
        db.refresh(nueva_retencion)
        
        return {
            "success": True,
            "message": "Retención creada exitosamente",
            "retencion": {
                "nrocta": nueva_retencion.nrocta,
                "concepto": nueva_retencion.concepto,
                "nro_retencion": nueva_retencion.nro_retencion,
                "fecha": nueva_retencion.fecha,
                "importe": float(nueva_retencion.importe)
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear retención: {str(e)}")
    finally:
        db.close()


# ============================================================================
# ENDPOINT PARA ELIMINAR MOVIMIENTOS FINANCIEROS
# ============================================================================

# Modelo para eliminar movimiento específico
class EliminarMovimiento(BaseModel):
    tipo: str  # "cheque" o "retencion"
    id: int    # ID del movimiento a eliminar

# Endpoint alternativo más flexible - eliminar por número de cheque/retención
@router.delete("/{deposit_id}/cheques/{cheque_identifier}")
def delete_cheque_by_identifier(deposit_id: str, cheque_identifier: str):
    """Elimina un cheque específico por ID o número de cheque"""
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Cheque
    from fastapi import HTTPException
    
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")
        
        cheque = None
        
        # Intentar buscar por ID primero (si es numérico)
        if cheque_identifier.isdigit():
            cheque_id = int(cheque_identifier)
            cheque = db.query(Cheque).filter(
                Cheque.id == cheque_id,
                Cheque.deposit_id == deposit_id
            ).first()
        
        # Si no se encontró por ID, buscar por número de cheque
        if not cheque:
            cheque = db.query(Cheque).filter(
                Cheque.nro_cheque == cheque_identifier,
                Cheque.deposit_id == deposit_id
            ).first()
        
        if not cheque:
            raise HTTPException(status_code=404, detail=f"Cheque {cheque_identifier} no encontrado")
        
        importe = cheque.importe
        cheque_id = cheque.id
        nro_cheque = cheque.nro_cheque
        
        db.delete(cheque)
        db.commit()
        
        return {
            "success": True,
            "message": f"Cheque eliminado exitosamente",
            "tipo": "cheque",
            "numero": nro_cheque,
            "id": cheque_id,
            "importe": importe,
            "searched_by": cheque_identifier
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close()

@router.delete("/{deposit_id}/retenciones/{retencion_identifier}")
def delete_retencion_by_identifier(deposit_id: str, retencion_identifier: str):
    """Elimina una retención específica por ID o número de retención"""
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Retencion
    from fastapi import HTTPException
    
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")
        
        retencion = None
        
        # Intentar buscar por ID primero (si es numérico)
        if retencion_identifier.isdigit():
            retencion_id = int(retencion_identifier)
            retencion = db.query(Retencion).filter(
                Retencion.id == retencion_id,
                Retencion.deposit_id == deposit_id
            ).first()
        
        # Si no se encontró por ID, buscar por número de retención (si es numérico)
        if not retencion and retencion_identifier.isdigit():
            numero_retencion = int(retencion_identifier)
            retencion = db.query(Retencion).filter(
                Retencion.nro_retencion == numero_retencion,
                Retencion.deposit_id == deposit_id
            ).first()
        
        if not retencion:
            raise HTTPException(status_code=404, detail=f"Retención {retencion_identifier} no encontrada")
        
        importe = retencion.importe
        retencion_id = retencion.id
        nro_retencion = retencion.nro_retencion
        
        db.delete(retencion)
        db.commit()
        
        return {
            "success": True,
            "message": f"Retención eliminada exitosamente",
            "tipo": "retencion",
            "numero": nro_retencion,
            "id": retencion_id,
            "importe": importe,
            "searched_by": retencion_identifier
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close()

@router.delete("/{deposit_id}/movimiento")
def delete_movimiento_financiero(deposit_id: str, movimiento: Optional[EliminarMovimiento] = None):
    """
    Elimina movimientos financieros de un depósito:
    - CON body: { "tipo": "cheque", "id": 123 } - Elimina movimiento específico
    - SIN body: {} - Elimina TODOS los movimientos del depósito
    """
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Cheque, Retencion
    from fastapi import HTTPException
    
    db = SessionLocal()
    try:
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")
        
        # Si NO se envía body, eliminar TODOS los movimientos
        if movimiento is None:
            # Obtener todos los movimientos del depósito
            cheques = db.query(Cheque).filter(Cheque.deposit_id == deposit_id).all()
            retenciones = db.query(Retencion).filter(Retencion.deposit_id == deposit_id).all()
            
            if not cheques and not retenciones:
                return {
                    "success": True,
                    "message": "No hay movimientos financieros para eliminar en este depósito",
                    "cheques_eliminados": 0,
                    "retenciones_eliminadas": 0,
                    "importe_total": 0
                }
            
            # Calcular importes
            importe_cheques = sum(float(c.importe) for c in cheques)
            importe_retenciones = sum(float(r.importe) for r in retenciones)
            importe_total = importe_cheques + importe_retenciones
            
            # Eliminar todos los movimientos
            for cheque in cheques:
                db.delete(cheque)
            for retencion in retenciones:
                db.delete(retencion)
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Se eliminaron todos los movimientos del depósito {deposit_id}",
                "cheques_eliminados": len(cheques),
                "retenciones_eliminadas": len(retenciones),
                "importe_total": importe_total
            }
        
        # Si SÍ se envía body, eliminar movimiento específico
        if movimiento.tipo.lower() == "cheque":
            # Eliminar cheque específico
            cheque = db.query(Cheque).filter(
                Cheque.id == movimiento.id, 
                Cheque.deposit_id == deposit.deposit_id
            ).first()
            
            if not cheque:
                raise HTTPException(status_code=404, detail="Cheque no encontrado")
            
            importe = cheque.importe
            db.delete(cheque)
            db.commit()
            
            return {
                "success": True,
                "message": f"Cheque ID {movimiento.id} eliminado exitosamente",
                "tipo": "cheque",
                "id": movimiento.id,
                "importe": importe
            }
            
        elif movimiento.tipo.lower() == "retencion":
            # Eliminar retención específica
            retencion = db.query(Retencion).filter(
                Retencion.id == movimiento.id,
                Retencion.deposit_id == deposit.deposit_id
            ).first()
            
            if not retencion:
                raise HTTPException(status_code=404, detail="Retención no encontrada")
            
            importe = retencion.importe
            db.delete(retencion)
            db.commit()
            
            return {
                "success": True,
                "message": f"Retención ID {movimiento.id} eliminada exitosamente",
                "tipo": "retencion", 
                "id": movimiento.id,
                "importe": importe
            }
        else:
            raise HTTPException(status_code=400, detail="Tipo debe ser 'cheque' o 'retencion'")
            
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar movimiento: {str(e)}")
    finally:
        db.close()

# ============================================================================
# ENDPOINTS PARA ELIMINAR TODOS LOS MOVIMIENTOS DE UN DEPÓSITO
# ============================================================================

@router.delete("/{deposit_id}/retenciones")
def delete_all_retenciones(deposit_id: str):
    """Elimina TODAS las retenciones de un depósito específico"""
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Retencion
    from fastapi import HTTPException
    
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")
        
        # Obtener todas las retenciones del depósito
        retenciones = db.query(Retencion).filter(Retencion.deposit_id == deposit_id).all()
        
        if not retenciones:
            return {
                "success": True,
                "message": "No hay retenciones para eliminar en este depósito",
                "eliminadas": 0,
                "importe_total": 0
            }
        
        # Calcular importe total antes de eliminar
        importe_total = sum(float(r.importe) for r in retenciones)
        count = len(retenciones)
        
        # Eliminar todas las retenciones
        for retencion in retenciones:
            db.delete(retencion)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Se eliminaron {count} retenciones del depósito {deposit_id}",
            "eliminadas": count,
            "importe_total": importe_total
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close()

@router.delete("/{deposit_id}/cheques")
def delete_all_cheques(deposit_id: str):
    """Elimina TODOS los cheques de un depósito específico"""
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Cheque
    from fastapi import HTTPException
    
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")
        
        # Obtener todos los cheques del depósito
        cheques = db.query(Cheque).filter(Cheque.deposit_id == deposit_id).all()
        
        if not cheques:
            return {
                "success": True,
                "message": "No hay cheques para eliminar en este depósito",
                "eliminados": 0,
                "importe_total": 0
            }
        
        # Calcular importe total antes de eliminar
        importe_total = sum(float(c.importe) for c in cheques)
        count = len(cheques)
        
        # Eliminar todos los cheques
        for cheque in cheques:
            db.delete(cheque)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Se eliminaron {count} cheques del depósito {deposit_id}",
            "eliminados": count,
            "importe_total": importe_total
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close()

@router.delete("/{deposit_id}/movimientos")
def delete_all_movimientos(deposit_id: str):
    """Elimina TODOS los movimientos financieros (cheques Y retenciones) de un depósito"""
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Cheque, Retencion
    from fastapi import HTTPException
    
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")
        
        # Obtener todos los movimientos del depósito
        cheques = db.query(Cheque).filter(Cheque.deposit_id == deposit_id).all()
        retenciones = db.query(Retencion).filter(Retencion.deposit_id == deposit_id).all()
        
        if not cheques and not retenciones:
            return {
                "success": True,
                "message": "No hay movimientos financieros para eliminar en este depósito",
                "cheques_eliminados": 0,
                "retenciones_eliminadas": 0,
                "importe_total": 0
            }
        
        # Calcular importes
        importe_cheques = sum(float(c.importe) for c in cheques)
        importe_retenciones = sum(float(r.importe) for r in retenciones)
        importe_total = importe_cheques + importe_retenciones
        
        # Eliminar todos los movimientos
        for cheque in cheques:
            db.delete(cheque)
        for retencion in retenciones:
            db.delete(retencion)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Se eliminaron todos los movimientos del depósito {deposit_id}",
            "cheques_eliminados": len(cheques),
            "retenciones_eliminadas": len(retenciones),
            "importe_total": importe_total
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close()


# ============================================================================
# ENDPOINTS PARA EDITAR CHEQUES Y RETENCIONES
# ============================================================================

@router.put("/{deposit_id}/cheques/{cheque_id}")
def update_deposit_cheque(deposit_id: str, cheque_id: int, cheque_data: ChequeCreate):
    """
    Actualiza un cheque específico por su ID
    """
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Cheque
    from fastapi import HTTPException
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")
        
        # Buscar el cheque específico
        cheque = db.query(Cheque).filter(
            Cheque.id == cheque_id,
            Cheque.deposit_id == deposit_id
        ).first()
        
        if not cheque:
            raise HTTPException(status_code=404, detail=f"Cheque con ID {cheque_id} no encontrado")
        
        # Guardar valores anteriores para el log
        valores_anteriores = {
            "nro_cheque": cheque.nro_cheque,
            "banco": cheque.banco,
            "importe": float(cheque.importe) if cheque.importe else 0.0,
            "fecha": cheque.fecha
        }
        
        # Actualizar los campos
        if cheque_data.numero is not None:
            cheque.nro_cheque = str(cheque_data.numero)
            
        if cheque_data.banco is not None:
            cheque.banco = str(_extract_int(cheque_data.banco, 0))
            
        if cheque_data.importe is not None:
            cheque.importe = cheque_data.importe
            
        # Manejar fecha correctamente
        if cheque_data.fecha_cobro is not None:
            fecha_value = cheque_data.fecha_cobro
            # Convertir formato de fecha si viene como YYYY-MM-DD
            if fecha_value and "-" in fecha_value:
                try:
                    fecha_obj = datetime.strptime(fecha_value, "%Y-%m-%d")
                    fecha_value = fecha_obj.strftime("%d/%m/%Y")
                except:
                    pass  # Mantener formato original si falla conversión
            cheque.fecha = fecha_value
        
        # Actualizar sucursal/localidad si vinieron en la petición
        if hasattr(cheque_data, 'sucursal') and cheque_data.sucursal is not None:
            cheque.sucursal = str(_extract_int(cheque_data.sucursal, 0))
        if hasattr(cheque_data, 'localidad') and cheque_data.localidad is not None:
            cheque.localidad = str(_extract_int(cheque_data.localidad, 0))

        db.commit()
        db.refresh(cheque)
        
        # Log de la acción
        log_user_action(
            action="UPDATE_CHEQUE",
            resource="cheques",
            resource_id=str(cheque_id), 
            extra_data={
                "deposit_id": deposit_id,
                "valores_anteriores": valores_anteriores,
                "valores_nuevos": {
                    "nro_cheque": cheque.nro_cheque,
                    "banco": cheque.banco,
                    "importe": float(cheque.importe),
                    "fecha": cheque.fecha
                }
            }
        )
        
        return {
            "success": True,
            "message": f"Cheque {cheque_id} actualizado exitosamente",
            "cheque": {
                "id": cheque.id,
                "nrocta": cheque.nrocta,
                "concepto": cheque.concepto,
                "banco": cheque.banco,
                "sucursal": cheque.sucursal,
                "localidad": cheque.localidad,
                "nro_cheque": cheque.nro_cheque,
                "nro_cuenta": cheque.nro_cuenta,
                "titular": cheque.titular,
                "fecha": cheque.fecha,
                "importe": float(cheque.importe)
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        log_technical_error(
            message=f"Error al actualizar cheque {cheque_id}",
            context={
                "deposit_id": deposit_id,
                "cheque_id": cheque_id,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close()


@router.put("/{deposit_id}/retenciones/{retencion_id}")
def update_deposit_retencion(deposit_id: str, retencion_id: int, retencion_data: RetencionCreate):
    """
    Actualiza una retención específica por su ID
    """
    from database import SessionLocal
    from models.deposit import Deposit
    from models.cheque_retencion import Retencion
    from fastapi import HTTPException
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")
        
        # Buscar la retención específica
        retencion = db.query(Retencion).filter(
            Retencion.id == retencion_id,
            Retencion.deposit_id == deposit_id
        ).first()
        
        if not retencion:
            raise HTTPException(status_code=404, detail=f"Retención con ID {retencion_id} no encontrada")
        
        # Guardar valores anteriores para el log
        valores_anteriores = {
            "nro_retencion": retencion.nro_retencion,
            "concepto": retencion.concepto,
            "importe": float(retencion.importe) if retencion.importe else 0.0,
            "nrocta": retencion.nrocta
        }
        
        # Actualizar los campos
        if retencion_data.numero is not None:
            retencion.nro_retencion = _digits_str(retencion_data.numero, default="")
        
        if retencion_data.concepto is not None:
            retencion.concepto = retencion_data.concepto
        
        if retencion_data.importe is not None:
            retencion.importe = retencion_data.importe
        
        # Manejar numero_cuenta en actualización
        if hasattr(retencion_data, 'numero_cuenta') and retencion_data.numero_cuenta is not None:
            try:
                retencion.nrocta = int(retencion_data.numero_cuenta)
            except (ValueError, TypeError):
                retencion.nrocta = 1  # Default fallback
        
        # Actualizar fecha de modificación
        retencion.fecha = datetime.now()
        
        db.commit()
        db.refresh(retencion)
        
        # Log de la acción
        log_user_action(
            action="UPDATE_RETENCION",
            resource="retenciones", 
            resource_id=str(retencion_id),
            extra_data={
                "deposit_id": deposit_id,
                "valores_anteriores": valores_anteriores,
                "valores_nuevos": {
                    "nro_retencion": retencion.nro_retencion,
                    "concepto": retencion.concepto,
                    "importe": float(retencion.importe),
                    "nrocta": retencion.nrocta
                }
            }
        )
        
        return {
            "success": True,
            "message": f"Retención {retencion_id} actualizada exitosamente",
            "retencion": {
                "id": retencion.id,
                "nrocta": retencion.nrocta,
                "concepto": retencion.concepto,
                "nro_retencion": retencion.nro_retencion,
                "fecha": retencion.fecha,
                "importe": float(retencion.importe)
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        log_technical_error(
            message=f"Error al actualizar retención {retencion_id}",
            context={
                "deposit_id": deposit_id,
                "retencion_id": retencion_id,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close()
