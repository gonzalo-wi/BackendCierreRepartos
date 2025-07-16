"""
Router para manejo de totales diarios y datos para gráficos
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from services.daily_totals_service import (
    save_daily_totals, 
    get_daily_totals_by_period, 
    get_monthly_chart_data,
    auto_save_today_totals
)
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter(
    prefix="/charts",
    tags=["charts-analytics"]
)

@router.post("/save-daily-totals")
def save_totals_for_date(date: str = Query(..., description="Fecha en formato YYYY-MM-DD")):
    """
    Guarda los totales del día especificado en la base de datos para análisis posterior
    """
    try:
        result = save_daily_totals(date)
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Totales guardados exitosamente para {date}",
                "data": result
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar totales: {str(e)}")

@router.post("/save-today-totals")
def save_today_totals():
    """
    Guarda los totales del día actual
    """
    try:
        result = auto_save_today_totals()
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Totales del día actual guardados exitosamente",
                "data": result
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar totales: {str(e)}")

@router.get("/daily-totals")
def get_daily_totals(
    start_date: str = Query(..., description="Fecha inicial en formato YYYY-MM-DD"),
    end_date: str = Query(..., description="Fecha final en formato YYYY-MM-DD"),
    plant: Optional[str] = Query(None, description="Planta específica (jumillano, plata, nafa, total)")
):
    """
    Obtiene los totales diarios para un período específico
    """
    try:
        totals = get_daily_totals_by_period(start_date, end_date, plant)
        return JSONResponse(
            status_code=200,
            content={
                "start_date": start_date,
                "end_date": end_date,
                "plant": plant,
                "totals": totals,
                "count": len(totals)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener totales: {str(e)}")

@router.get("/monthly-chart")
def get_monthly_chart(
    year: int = Query(..., description="Año"),
    month: int = Query(..., description="Mes (1-12)"),
    plant: Optional[str] = Query(None, description="Planta específica (jumillano, plata, nafa) o None para todas")
):
    """
    Obtiene datos formateados para gráficos mensuales (compatible con Chart.js)
    """
    try:
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="El mes debe estar entre 1 y 12")
            
        chart_data = get_monthly_chart_data(year, month, plant)
        return JSONResponse(
            status_code=200,
            content={
                "period": f"{year}-{month:02d}",
                "plant": plant,
                "chart_data": chart_data
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar datos del gráfico: {str(e)}")

@router.get("/current-month-chart")
def get_current_month_chart(
    plant: Optional[str] = Query(None, description="Planta específica (jumillano, plata, nafa)")
):
    """
    Obtiene datos del gráfico para el mes actual
    """
    now = datetime.now()
    return get_monthly_chart(year=now.year, month=now.month, plant=plant)

@router.get("/last-30-days")
def get_last_30_days_totals(
    plant: Optional[str] = Query(None, description="Planta específica (jumillano, plata, nafa, total)")
):
    """
    Obtiene los totales de los últimos 30 días
    """
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        totals = get_daily_totals_by_period(start_date, end_date, plant)
        
        # Calcular estadísticas
        if totals:
            amounts = [t["total_amount"] for t in totals]
            avg_daily = sum(amounts) / len(amounts) if amounts else 0
            max_day = max(totals, key=lambda x: x["total_amount"]) if totals else None
            min_day = min(totals, key=lambda x: x["total_amount"]) if totals else None
            
            stats = {
                "total_amount": sum(amounts),
                "average_daily": avg_daily,
                "best_day": max_day,
                "worst_day": min_day,
                "days_with_sales": len([a for a in amounts if a > 0])
            }
        else:
            stats = {
                "total_amount": 0,
                "average_daily": 0,
                "best_day": None,
                "worst_day": None,
                "days_with_sales": 0
            }
        
        return JSONResponse(
            status_code=200,
            content={
                "period": f"{start_date} to {end_date}",
                "plant": plant,
                "totals": totals,
                "statistics": stats
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos: {str(e)}")

@router.get("/stats/summary")
def get_summary_stats():
    """
    Obtiene un resumen de estadísticas generales
    """
    try:
        # Últimos 7 días
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date_7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        start_date_30 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        last_7_days = get_daily_totals_by_period(start_date_7, end_date, "total")
        last_30_days = get_daily_totals_by_period(start_date_30, end_date, "total")
        
        def calculate_total(totals):
            return sum(t["total_amount"] for t in totals)
        
        summary = {
            "last_7_days": {
                "total": calculate_total(last_7_days),
                "average": calculate_total(last_7_days) / 7 if last_7_days else 0,
                "days": len(last_7_days)
            },
            "last_30_days": {
                "total": calculate_total(last_30_days),
                "average": calculate_total(last_30_days) / 30 if last_30_days else 0,
                "days": len(last_30_days)
            },
            "current_month": get_monthly_chart_data(datetime.now().year, datetime.now().month, "total")
        }
        
        return JSONResponse(status_code=200, content=summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")
