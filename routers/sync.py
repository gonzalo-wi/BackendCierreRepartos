"""
Router para operaciones de sincronización con miniBank y API externa
"""
import traceback
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from services.deposits_service import (
    get_jumillano_deposits,
    get_all_deposits,
    get_plata_deposits,
    get_nafa_deposits,
    save_deposits_to_db
)
from services.repartos_api_service import actualizar_depositos_esperados

# Importar utilidades de logging
from utils.logging_utils import log_user_action, log_technical_error, log_technical_warning
from middleware.logging_middleware import log_endpoint_access

router = APIRouter(
    prefix="/sync",
    tags=["synchronization"]
)


@router.post("/deposits/jumillano")
@log_endpoint_access("SYNC_JUMILLANO_DEPOSITS", "synchronization")
def save_jumillano_deposits(request: Request, date: str = Query(...)):
    try:
        # Log inicio de sincronización
        log_user_action(
            action="START_SYNC_JUMILLANO",
            resource="synchronization",
            request=request,
            extra_data={
                "date": date,
                "plant": "jumillano",
                "sync_type": "deposits"
            }
        )
        
        print(f"🔄 Iniciando guardado de depósitos para fecha: {date}")
        data = get_jumillano_deposits(date)
        
        print("📊 Datos obtenidos, guardando en base de datos...")
        result = save_deposits_to_db(data)
        
        print("✅ Proceso completado exitosamente")
        
        # Log de sincronización exitosa
        log_user_action(
            action="SYNC_JUMILLANO_SUCCESS",
            resource="synchronization",
            request=request,
            success=True,
            extra_data={
                "date": date,
                "plant": "jumillano",
                "records_processed": len(data) if isinstance(data, list) else 1,
                "sync_duration": "completed"
            }
        )
        
        return {"status": "ok", "message": "Depósitos guardados correctamente"}
        
    except Exception as e:
        print(f"❌ Error en save_jumillano_deposits: {str(e)}")
        traceback.print_exc()
        
        # Log de error técnico
        log_technical_error(
            e,
            "sync_jumillano_deposits",
            request=request,
            extra_data={
                "date": date,
                "plant": "jumillano",
                "operation": "save_deposits"
            }
        )
        
        # Log de sincronización fallida
        log_user_action(
            action="SYNC_JUMILLANO_FAILED",
            resource="synchronization",
            request=request,
            success=False,
            extra_data={
                "date": date,
                "plant": "jumillano", 
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deposits/all")
@log_endpoint_access("SYNC_ALL_DEPOSITS", "synchronization")
def save_all_deposits(request: Request, date: str = Query(...)):
    try:
        # Log inicio de sincronización completa
        log_user_action(
            action="START_SYNC_ALL_PLANTS",
            resource="synchronization",
            request=request,
            extra_data={
                "date": date,
                "plants": "all",
                "sync_type": "full_deposits"
            }
        )
        
        print(f"🔄 Iniciando guardado de TODOS los depósitos para fecha: {date}")
        data = get_all_deposits(date)
        
        print("📊 Datos de todas las máquinas obtenidos, guardando en base de datos...")
        result = save_deposits_to_db(data)
        
        print("✅ Proceso completado exitosamente para todas las máquinas")
        
        # Log de sincronización exitosa
        log_user_action(
            action="SYNC_ALL_PLANTS_SUCCESS",
            resource="synchronization",
            request=request,
            success=True,
            extra_data={
                "date": date,
                "plants": "all",
                "records_processed": len(data) if isinstance(data, list) else 1,
                "sync_duration": "completed"
            }
        )
        
        return {"status": "ok", "message": "Todos los depósitos guardados correctamente"}
        
    except Exception as e:
        print(f"❌ Error en save_all_deposits: {str(e)}")
        traceback.print_exc()
        
        # Log de error técnico
        log_technical_error(
            e,
            "sync_all_deposits",
            request=request,
            extra_data={
                "date": date,
                "plants": "all",
                "operation": "save_all_deposits"
            }
        )
        
        # Log de sincronización fallida
        log_user_action(
            action="SYNC_ALL_PLANTS_FAILED",
            resource="synchronization",
            request=request,
            success=False,
            extra_data={
                "date": date,
                "plants": "all",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deposits/plata")
def save_plata_deposits(date: str = Query(...)):
    try:
        print(f"🔄 Iniciando guardado de depósitos de La Plata para fecha: {date}")
        data = get_plata_deposits(date)
        print("📊 Datos de La Plata obtenidos, guardando en base de datos...")
        save_deposits_to_db(data)
        print("✅ Proceso completado exitosamente para La Plata")
        return {"status": "ok", "message": "Depósitos de La Plata guardados correctamente"}
    except Exception as e:
        print(f"❌ Error en save_plata_deposits: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deposits/nafa")
def save_nafa_deposits(date: str = Query(...)):
    try:
        print(f"🔄 Iniciando guardado de depósitos de Nafa para fecha: {date}")
        data = get_nafa_deposits(date)
        print("📊 Datos de Nafa obtenidos, guardando en base de datos...")
        save_deposits_to_db(data)
        print("✅ Proceso completado exitosamente para Nafa")
        return {"status": "ok", "message": "Depósitos de Nafa guardados correctamente"}
    except Exception as e:
        print(f"❌ Error en save_nafa_deposits: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deposits/today")
def sync_deposits_today():
    """
    Sincroniza automáticamente los depósitos de hoy y los retorna
    """
    try:
        from services.deposits_service import get_all_totals
        
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"🔄 Auto-sincronizando depósitos para hoy: {today}")
        
        # Obtener datos
        data = get_all_deposits(today)
        
        # Guardar automáticamente
        save_deposits_to_db(data)
        print("📊 Datos sincronizados automáticamente")
        
        # Retornar los totales también
        totals = get_all_totals(today)
        
        return {
            "status": "ok", 
            "message": "Depósitos sincronizados automáticamente",
            "date": today,
            "data": data,
            "totals": totals
        }
    except Exception as e:
        print(f"❌ Error en sincronización automática: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expected-amounts")
def sync_expected_amounts(date: str = Query(...)):
    """
    Sincroniza los montos esperados desde la API externa de repartos
    """
    try:
        print(f"🔄 Iniciando sincronización de montos esperados para fecha: {date}")
        
        resultado = actualizar_depositos_esperados(date)
        
        if resultado["status"] == "error":
            raise HTTPException(status_code=500, detail=resultado["message"])
        
        print(f"✅ Sincronización completada: {resultado['actualizados']} depósitos actualizados")
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en sincronización de montos esperados: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
