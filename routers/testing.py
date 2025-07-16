"""
Router para endpoints de testing y diagnóstico
"""
from datetime import datetime
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/test",
    tags=["testing"]
)


@router.get("/health")
def health_check():
    """
    Endpoint de verificación de salud del servidor
    """
    return {
        "status": "ok", 
        "message": "Servidor funcionando correctamente", 
        "timestamp": datetime.now().isoformat()
    }


@router.get("/database")
def test_database():
    """
    Endpoint para probar la conexión a la base de datos
    """
    try:
        from database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        # Hacer una consulta simple
        result = db.execute(text("SELECT 1")).fetchone()
        db.close()
        return {"status": "ok", "message": "Base de datos funcionando correctamente", "result": result[0]}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/idreparto-extraction")
def test_idreparto_extraction():
    """
    Endpoint para probar la extracción de idreparto de diferentes formatos de user_name
    """
    from services.repartos_api_service import extraer_idreparto_de_user_name
    
    # Casos de prueba
    test_cases = [
        "42, RTO 042",
        "RTO 277, 277", 
        "1, algo más",
        "RTO 123, algo",
        "999, TEST",
        ", 456",  # edge case
        "ABC 789, XYZ",
        "123",  # sin coma
        "",  # vacío
        None,  # None
        "RTO, 321",  # texto y número separado por coma
        "100, RTO 200, 300"  # múltiples números
    ]
    
    resultados = []
    for case in test_cases:
        try:
            idreparto = extraer_idreparto_de_user_name(case)
            resultados.append({
                "user_name": case,
                "idreparto_extraido": idreparto,
                "status": "ok" if idreparto is not None else "no_extraido"
            })
        except Exception as e:
            resultados.append({
                "user_name": case,
                "idreparto_extraido": None,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "status": "ok",
        "message": "Prueba de extracción de idreparto completada",
        "resultados": resultados
    }


@router.get("/external-api")
def test_external_api(date: str = Query(...)):
    """
    Endpoint de prueba para verificar la conexión con la API externa
    """
    try:
        from services.repartos_api_service import get_repartos_valores
        from datetime import datetime as dt
        from fastapi import HTTPException
        import traceback
        
        # Convertir fecha de "YYYY-MM-DD" a "DD/MM/YYYY"
        fecha_obj = dt.strptime(date, "%Y-%m-%d")
        fecha_api = fecha_obj.strftime("%d/%m/%Y")
        
        print(f"🧪 Probando API externa para fecha: {fecha_api}")
        
        repartos = get_repartos_valores(fecha_api)
        
        return {
            "status": "ok",
            "fecha_consultada": fecha_api,
            "total_repartos": len(repartos),
            "repartos_cerrados": len([r for r in repartos if r.get("status") == 1]),
            "sample_data": repartos[:3] if repartos else [],
            "all_data": repartos
        }
        
    except Exception as e:
        print(f"❌ Error probando API externa: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
