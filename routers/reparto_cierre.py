from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse
from services.reparto_cierre_service import RepartoCierreService
from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime
from models.user import User
from auth.dependencies import get_admin_user, get_any_user

router = APIRouter(
    prefix="/reparto-cierre",
    tags=["reparto-cierre"]
)

class CierreConfigModel(BaseModel):
    fecha_especifica: Optional[str] = None  # Formato: "YYYY-MM-DD"
    max_reintentos: Optional[int] = 3
    delay_entre_envios: Optional[float] = 1.0
    modo_test: Optional[bool] = False  # por defecto, envío real (producción)

class RevertirConfigModel(BaseModel):
    fecha_especifica: Optional[str] = None  # YYYY-MM-DD
    idreparto: Optional[int] = None

# Instancia del servicio
cierre_service = RepartoCierreService()

@router.get("/repartos-listos")
def obtener_repartos_listos(
    fecha: Optional[str] = Query(None, description="Fecha en formato YYYY-MM-DD para filtrar repartos"),
    current_user: User = Depends(get_any_user)  # Cualquier usuario autenticado puede ver
):
    """
    Obtiene la lista de repartos con estado LISTO que están pendientes de envío
    Si se especifica fecha, filtra solo los repartos de ese día
    """
    try:
        fecha_obj = None
        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha inválido. Use YYYY-MM-DD"
                )
        
        repartos = cierre_service.get_repartos_listos(fecha_obj)
        
        mensaje = f"Se encontraron {len(repartos)} repartos listos para enviar"
        if fecha:
            mensaje += f" para el día {fecha}"
        
        return {
            "success": True,
            "total_repartos": len(repartos),
            "fecha_filtro": fecha,
            "repartos": repartos,
            "message": mensaje
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al obtener repartos listos: {str(e)}"
        )

@router.post("/cerrar-repartos")
def cerrar_repartos(
    config: CierreConfigModel = CierreConfigModel(),
    current_user: User = Depends(get_admin_user)  # Solo Admin y SuperAdmin
):
    """
    Procesa la cola de repartos y los envía al sistema de cierre
    
    Parámetros:
    - fecha_especifica: Fecha específica para procesar (formato YYYY-MM-DD). Si no se especifica, procesa todos
    - max_reintentos: Número máximo de reintentos por reparto (default: 3)
    - delay_entre_envios: Delay en segundos entre envíos (default: 1.0)
    - modo_test: Si está en modo test, simula el envío (default: True)
    """
    try:
        fecha_obj = None
        if config.fecha_especifica:
            try:
                fecha_obj = datetime.strptime(config.fecha_especifica, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")

        fecha_str = config.fecha_especifica or "todos los días"
        print("🎬 Iniciando cierre de repartos con configuración:")
        print(f"   - Usuario: {current_user.username} ({current_user.role.value})")
        print(f"   - Fecha: {fecha_str}")
        print(f"   - Max reintentos: {config.max_reintentos}")
        print(f"   - Delay entre envíos: {config.delay_entre_envios}s")
        # Forzar producción siempre para permitir pruebas desde el front
        force_production_override = True
        print(f"   - Modo test (solicitado): {config.modo_test}")
        print("   - Modo test (efectivo): False — envío REAL forzado")

        # Verificar si hay repartos listos antes de procesar
        repartos_listos = cierre_service.get_repartos_listos(fecha_obj)
        if not repartos_listos:
            mensaje = "No hay repartos listos para enviar"
            if config.fecha_especifica:
                mensaje += f" para la fecha {config.fecha_especifica}"
            return {
                "success": True,
                "message": mensaje,
                "fecha_procesada": config.fecha_especifica,
                "total_repartos": 0,
                "enviados": 0,
                "errores": 0
            }

        # Procesar la cola
        resultado = cierre_service.procesar_cola_repartos(
            fecha_especifica=fecha_obj,
            max_reintentos=config.max_reintentos,
            delay_entre_envios=config.delay_entre_envios,
            force_production=force_production_override
        )

        # Agregar información de fecha al resultado
        resultado["fecha_procesada"] = config.fecha_especifica

        # Determinar código de respuesta HTTP según el resultado
        status_code = 200 if resultado["success"] else 207  # 207 = Multi-Status

        return JSONResponse(status_code=status_code, content={**resultado, "forced_production": True})
    except HTTPException:
        raise
    except Exception as e:
        print(f"💥 Error crítico en cierre de repartos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar cierre de repartos: {str(e)}")

@router.post("/revertir-enviados")
def revertir_enviados(
    config: RevertirConfigModel = RevertirConfigModel(),
    current_user: User = Depends(get_admin_user)
):
    """
    Revierte depósitos ENVIADO -> LISTO por fecha (YYYY-MM-DD) y/o idreparto.
    Útil para reintentar el envío real inmediatamente.
    """
    try:
        fecha_obj = None
        if config.fecha_especifica:
            try:
                fecha_obj = datetime.strptime(config.fecha_especifica, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")

        resultado = cierre_service.revertir_enviados(fecha_obj, config.idreparto)
        if not resultado.get("success"):
            raise HTTPException(status_code=500, detail=resultado.get("error", "Error desconocido"))
        return {
            "success": True,
            "revertidos": resultado.get("revertidos", 0),
            "fecha": config.fecha_especifica,
            "idreparto": config.idreparto
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al revertir estados: {str(e)}")

@router.post("/cerrar-repartos-async")
def cerrar_repartos_async(
    background_tasks: BackgroundTasks, 
    config: CierreConfigModel = CierreConfigModel(),
    current_user: User = Depends(get_admin_user)  # Solo Admin y SuperAdmin
):
    """
    Procesa la cola de repartos de forma asíncrona (en background)
    Útil para evitar timeouts en el frontend
    """
    try:
        # Verificar si hay repartos listos
        repartos_listos = cierre_service.get_repartos_listos()
        
        if not repartos_listos:
            return {
                "success": True,
                "message": "No hay repartos listos para enviar",
                "total_repartos": 0,
                "task_started": False
            }
        
        # Agregar tarea al background
        # Forzar producción siempre
        background_tasks.add_task(
            cierre_service.procesar_cola_repartos,
            None,  # fecha_especifica
            config.max_reintentos,
            config.delay_entre_envios,
            True
        )
        
        return {
            "success": True,
            "message": f"Proceso de cierre iniciado en background para {len(repartos_listos)} repartos",
            "total_repartos": len(repartos_listos),
            "task_started": True,
            "forced_production": True,
            "note": "El proceso se ejecutará en segundo plano. Consulte los logs del servidor para seguir el progreso."
        }
        
    except Exception as e:
        print(f"💥 Error al iniciar cierre async: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al iniciar proceso asíncrono: {str(e)}"
        )

@router.get("/estado-repartos")
def obtener_estado_repartos(current_user: User = Depends(get_any_user)):
    """
    Obtiene un resumen del estado actual de todos los repartos
    """
    try:
        from database import SessionLocal
        from models.deposit import Deposit
        from sqlalchemy import func
        
        db = SessionLocal()
        
        try:
            # Contar repartos por estado
            estados = db.query(
                Deposit.estado,
                func.count(Deposit.id).label('cantidad')
            ).group_by(Deposit.estado).all()
            
            resumen = {
                "total_repartos": sum(estado.cantidad for estado in estados),
                "por_estado": {estado.estado: estado.cantidad for estado in estados},
                "listos_para_enviar": next((estado.cantidad for estado in estados if estado.estado == "LISTO"), 0),
                "enviados": next((estado.cantidad for estado in estados if estado.estado == "ENVIADO"), 0),
                "timestamp": _get_current_timestamp()
            }
            
            return {
                "success": True,
                "resumen": resumen
            }
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al obtener estado de repartos: {str(e)}"
        )

@router.get("/resumen-por-fechas")
def obtener_resumen_por_fechas(current_user: User = Depends(get_any_user)):
    """
    Obtiene un resumen de repartos LISTO agrupados por fecha
    Útil para mostrar al usuario qué días tienen repartos pendientes de envío
    """
    try:
        resumen = cierre_service.get_resumen_repartos_por_fecha()
        
        return {
            "success": True,
            "resumen": resumen
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al obtener resumen por fechas: {str(e)}"
        )

# Helper method para timestamp
def _get_current_timestamp():
    from datetime import datetime
    return datetime.now().isoformat()

@router.post("/cerrar-repartos-test")
def cerrar_repartos_test(
    config: CierreConfigModel = CierreConfigModel()
):
    """
    ENDPOINT PARA PRUEBAS DE PRODUCCIÓN - SIN AUTENTICACIÓN
    Úsalo para probar el cierre real mientras ajustas el frontend
    """
    try:
        fecha_obj = None
        if config.fecha_especifica:
            try:
                fecha_obj = datetime.strptime(config.fecha_especifica, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha inválido. Use YYYY-MM-DD"
                )
        
        # Forzar modo_test a False para pruebas reales
        resultado = cierre_service.procesar_cola_repartos(
            fecha_especifica=fecha_obj,
            max_reintentos=config.max_reintentos or 3,
            delay_entre_envios=config.delay_entre_envios or 1.0,
            force_production=True  # Siempre real para pruebas
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Proceso de cierre completado",
                "timestamp": _get_current_timestamp(),
                "production_mode": cierre_service.production_mode,
                "config": {
                    "fecha_especifica": config.fecha_especifica,
                    "max_reintentos": config.max_reintentos or 3,
                    "delay_entre_envios": config.delay_entre_envios or 1.0,
                    "modo_test": False,
                    "soap_url": cierre_service.soap_url
                },
                "resultado": resultado
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al procesar repartos: {str(e)}"
        )
