"""
Router para endpoints de consulta de depósitos desde miniBank
"""
from datetime import datetime
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
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
