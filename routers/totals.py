"""
Router para endpoints de totales y repartos
"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from services.deposits_service import (
    get_jumillano_deposits,
    get_jumillano_total,
    get_plata_total,
    get_nafa_total,
    get_all_totals,
)
from services.deposits_mapper import map_deposit_to_reparto

router = APIRouter(
    tags=["totals-repartos"]
)


# Endpoints de totales
@router.get("/totals/jumillano")
def totals_jumillano(date: str = Query(...)):
    try:
        total = get_jumillano_total(date)
        return JSONResponse(content={"total": total, "date": date})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/totals/plata")
def totals_plata(date: str = Query(...)):
    try:
        total = get_plata_total(date)
        return JSONResponse(content={"total": total, "date": date})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/totals/nafa")
def totals_nafa(date: str = Query(...)):
    try:
        total = get_nafa_total(date)
        return JSONResponse(content={"total": total, "date": date})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/totals/all")
def totals_all(date: str = Query(...)):
    try:
        totals = get_all_totals(date)
        return JSONResponse(content=totals)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/totals/sync")
def get_totals_with_sync(date: str = Query(None)):
    """
    Obtiene los totales y sincroniza automáticamente si es necesario
    """
    try:
        from datetime import datetime
        from services.deposits_service import get_all_deposits, save_deposits_to_db
        
        # Si no se proporciona fecha, usar hoy
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"🔄 Obteniendo totales con sincronización para: {date}")
        
        # Verificar si es hoy y sincronizar automáticamente
        today = datetime.now().strftime("%Y-%m-%d")
        if date == today:
            # Auto-sincronizar datos de hoy
            data = get_all_deposits(date)
            save_deposits_to_db(data)
            print("📊 Datos de hoy sincronizados automáticamente")
        
        # Obtener totales
        totals = get_all_totals(date)
        
        return {
            "status": "ok",
            "date": date,
            "auto_synced": date == today,
            **totals
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


# Endpoints de repartos
@router.get("/repartos/jumillano")
def get_repartos_jumillano(date: str = Query(...)):
    try:
        raw = get_jumillano_deposits(date)
        repartos = []

        for maquina in raw:
            deposits = raw[maquina].get("Deposits", {}).get("Deposit", [])
            if isinstance(deposits, dict):  # a veces viene como un solo objeto
                deposits = [deposits]
            for d in deposits:
                repartos.append(map_deposit_to_reparto(d))

        return JSONResponse(content=repartos)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
