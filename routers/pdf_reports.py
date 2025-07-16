"""
Router para generación de PDFs
"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response
from services.deposits_service import get_all_totals, get_all_deposits, get_jumillano_deposits, get_plata_deposits, get_nafa_deposits
from services.pdf_service import generate_daily_closure_pdf, generate_detailed_repartos_pdf

router = APIRouter(
    prefix="/pdf",
    tags=["pdf-reports"]
)


@router.get("/daily-closure")
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


@router.get("/daily-closure/preview")
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


@router.get("/repartos")
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


@router.get("/repartos/preview")
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


@router.get("/repartos/jumillano")
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


@router.get("/repartos/plata")
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


@router.get("/repartos/nafa")
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
