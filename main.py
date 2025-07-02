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
from services.pdf_service import generate_daily_closure_pdf, generate_detailed_repartos_pdf
from fastapi.responses import JSONResponse, Response

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

@app.get("/api/pdf/daily-closure")
def generate_daily_closure_pdf_endpoint(date: str = Query(...)):
    """
    Genera un PDF con el cierre de caja diario para todas las ubicaciones
    """
    try:
        # Obtener los totales para el día especificado
        totals = get_all_totals(date)
        
        # Generar el PDF
        pdf_content = generate_daily_closure_pdf(totals, date)
        
        # Crear el nombre del archivo
        filename = f"cierre_caja_{date.replace('-', '_')}.pdf"
        
        # Retornar el PDF como respuesta
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/pdf/daily-closure/preview")
def preview_daily_closure_pdf_endpoint(date: str = Query(...)):
    """
    Genera y muestra un PDF con el cierre de caja diario para previsualización en el navegador
    """
    try:
        # Obtener los totales para el día especificado
        totals = get_all_totals(date)
        
        # Generar el PDF
        pdf_content = generate_daily_closure_pdf(totals, date)
        
        # Retornar el PDF para visualización en el navegador
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline"
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/pdf/repartos")
def generate_repartos_pdf_endpoint(date: str = Query(...)):
    """
    Genera un PDF con todos los repartos detallados por planta
    """
    try:
        # Obtener los datos de depósitos de todas las máquinas
        repartos_data = get_all_deposits(date)
        
        # Generar el PDF
        pdf_content = generate_detailed_repartos_pdf(repartos_data, date)
        
        # Crear el nombre del archivo
        filename = f"repartos_detallados_{date.replace('-', '_')}.pdf"
        
        # Retornar el PDF como respuesta
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/pdf/repartos/preview")
def preview_repartos_pdf_endpoint(date: str = Query(...)):
    """
    Genera y muestra un PDF con todos los repartos detallados para previsualización en el navegador
    """
    try:
        # Obtener los datos de depósitos de todas las máquinas
        repartos_data = get_all_deposits(date)
        
        # Generar el PDF
        pdf_content = generate_detailed_repartos_pdf(repartos_data, date)
        
        # Retornar el PDF para visualización en el navegador
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline"
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/pdf/repartos/jumillano")
def generate_repartos_jumillano_pdf_endpoint(date: str = Query(...)):
    """
    Genera un PDF con los repartos detallados solo de Jumillano
    """
    try:
        # Obtener los datos de depósitos solo de Jumillano
        jumillano_data = get_jumillano_deposits(date)
        
        # Generar el PDF
        pdf_content = generate_detailed_repartos_pdf(jumillano_data, date)
        
        # Crear el nombre del archivo
        filename = f"repartos_jumillano_{date.replace('-', '_')}.pdf"
        
        # Retornar el PDF como respuesta
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/pdf/repartos/plata")
def generate_repartos_plata_pdf_endpoint(date: str = Query(...)):
    """
    Genera un PDF con los repartos detallados solo de La Plata
    """
    try:
        # Obtener los datos de depósitos solo de La Plata
        plata_data = get_plata_deposits(date)
        
        # Generar el PDF
        pdf_content = generate_detailed_repartos_pdf(plata_data, date)
        
        # Crear el nombre del archivo
        filename = f"repartos_plata_{date.replace('-', '_')}.pdf"
        
        # Retornar el PDF como respuesta
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/pdf/repartos/nafa")
def generate_repartos_nafa_pdf_endpoint(date: str = Query(...)):
    """
    Genera un PDF con los repartos detallados solo de Nafa
    """
    try:
        # Obtener los datos de depósitos solo de Nafa
        nafa_data = get_nafa_deposits(date)
        
        # Generar el PDF
        pdf_content = generate_detailed_repartos_pdf(nafa_data, date)
        
        # Crear el nombre del archivo
        filename = f"repartos_nafa_{date.replace('-', '_')}.pdf"
        
        # Retornar el PDF como respuesta
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})