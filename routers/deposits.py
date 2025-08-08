"""
Router para endpoints de consulta de depósitos desde miniBank
"""
from datetime import datetime
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from schemas.requests import StatusUpdateRequest, ExpectedAmountUpdateRequest
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


@router.get("")
def deposits(stIdentifier: str = Query(...), date: str = Query(...)):
    try:
        data = get_deposits(stIdentifier, date)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/jumillano")
def deposits_jumillano(date: str = Query(...)):
    try:
        # Obtener datos de miniBank
        data = get_jumillano_deposits(date)
        
        # Auto-sincronizar valores esperados desde API externa
        try:
            print(f"🔄 Auto-sincronizando valores esperados para Jumillano {date}...")
            resultado_sync = actualizar_depositos_esperados(date)
            print(f"💰 Sincronización: {resultado_sync.get('actualizados', 0)} depósitos actualizados")
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            # Continuar aunque falle la sincronización
        
        return JSONResponse(content=data)
    except Exception as e:
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

class RetencionCreate(BaseModel):
    tipo: Optional[str] = None  # Campo del frontend
    numero: Optional[int] = None  # Se mapea a nro_retencion (acepta int)
    importe: float  # REQUERIDO
    concepto: Optional[str] = None

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
        
        nuevo_cheque = Cheque(
            deposit_id=deposit.deposit_id,
            nrocta=1,  # Valor por defecto
            concepto="CHE",  # Valor por defecto
            banco=cheque.banco,
            sucursal="001",  # Valor por defecto
            localidad="1234",  # Valor por defecto
            nro_cheque=nro_cheque_value,
            nro_cuenta=1234,  # Valor por defecto
            titular="",  # Valor por defecto
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
        nro_retencion_value = str(retencion.numero) if retencion.numero else "SIN_NUMERO"
        concepto_value = retencion.concepto or "RIB"
        
        nueva_retencion = Retencion(
        deposit_id=deposit_id,
        nrocta="",  # Default vacío
        concepto=retencion.concepto or "",
        nro_retencion=str(retencion.numero) if retencion.numero else "",  # Convertir a string
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
@router.delete("/{deposit_id}/cheques/{numero_cheque}")
def delete_cheque_by_numero(deposit_id: str, numero_cheque: str):
    """Elimina un cheque específico por su número"""
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
        
        # Buscar y eliminar el cheque por número
        cheque = db.query(Cheque).filter(
            Cheque.nro_cheque == numero_cheque,
            Cheque.deposit_id == deposit_id
        ).first()
        
        if not cheque:
            raise HTTPException(status_code=404, detail=f"Cheque número {numero_cheque} no encontrado")
        
        importe = cheque.importe
        cheque_id = cheque.id
        db.delete(cheque)
        db.commit()
        
        return {
            "success": True,
            "message": f"Cheque número {numero_cheque} eliminado exitosamente",
            "tipo": "cheque",
            "numero": numero_cheque,
            "id": cheque_id,
            "importe": importe
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        db.close()

@router.delete("/{deposit_id}/retenciones/{numero_retencion}")
def delete_retencion_by_numero(deposit_id: str, numero_retencion: str):
    """Elimina una retención específica por su número"""
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
        
        # Buscar y eliminar la retención por número
        retencion = db.query(Retencion).filter(
            Retencion.nro_retencion == numero_retencion,
            Retencion.deposit_id == deposit_id
        ).first()
        
        if not retencion:
            raise HTTPException(status_code=404, detail=f"Retención número {numero_retencion} no encontrada")
        
        importe = retencion.importe
        retencion_id = retencion.id
        db.delete(retencion)
        db.commit()
        
        return {
            "success": True,
            "message": f"Retención número {numero_retencion} eliminada exitosamente",
            "tipo": "retencion",
            "numero": numero_retencion,
            "id": retencion_id,
            "importe": importe
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
