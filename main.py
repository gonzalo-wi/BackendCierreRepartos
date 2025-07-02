from fastapi import FastAPI, Query
from services.deposits_mapper import map_deposit_to_reparto
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
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/deposits")
def deposits(stIdentifier: str = Query(...), date: str = Query(...)):
    try:
        data = get_deposits(stIdentifier, date)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/api/deposits/jumillano")
def deposits_jumillano(date: str = Query(...)):
    try:
        data = get_jumillano_deposits(date)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/deposits/nafa")
def deposits_nafa(date: str = Query(...)):
    try:
        data = get_nafa_deposits(date)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/deposits/plata")
def deposits_plata(date: str = Query(...)):
    try:
        data = get_plata_deposits(date)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})    
    
@app.get("/api/deposits/all")
def deposits_all(date: str = Query(...)):
    try:
        data = get_all_deposits(date)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})    
    
@app.get("/api/repartos/jumillano")
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


@app.get("/api/totals/jumillano")
def totals_jumillano(date: str = Query(...)):
    try:
        total = get_jumillano_total(date)
        return JSONResponse(content={"total": total, "date": date})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/totals/plata")
def totals_plata(date: str = Query(...)):
    try:
        total = get_plata_total(date)
        return JSONResponse(content={"total": total, "date": date})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/totals/nafa")
def totals_nafa(date: str = Query(...)):
    try:
        total = get_nafa_total(date)
        return JSONResponse(content={"total": total, "date": date})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/totals/all")
def totals_all(date: str = Query(...)):
    try:
        totals = get_all_totals(date)
        return JSONResponse(content=totals)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})