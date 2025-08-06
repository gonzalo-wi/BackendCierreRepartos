from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, Optional
from pydantic import BaseModel
from models.user import User
from auth.dependencies import get_superadmin_user
from services.reparto_cierre_service import RepartoCierreService
import os

router = APIRouter(
    prefix="/production-control",
    tags=["production-control"]
)

class ProductionStatusResponse(BaseModel):
    production_mode: bool
    soap_url: str
    environment: str
    message: str

class ProductionToggleRequest(BaseModel):
    enable_production: bool
    confirmation_code: Optional[str] = None

# Instancia del servicio
cierre_service = RepartoCierreService()

@router.get("/status", response_model=ProductionStatusResponse)
def get_production_status(current_user: User = Depends(get_superadmin_user)):
    """
    Obtiene el estado actual del modo de producción
    Solo SuperAdmin puede acceder
    """
    return ProductionStatusResponse(
        production_mode=cierre_service.production_mode,
        soap_url=cierre_service.soap_url,
        environment="PRODUCCIÓN" if cierre_service.production_mode else "DESARROLLO",
        message="Cierre de repartos se enviará al sistema real" if cierre_service.production_mode else "Cierre de repartos en modo simulación"
    )

@router.post("/toggle-production")
def toggle_production_mode(
    request: ProductionToggleRequest,
    current_user: User = Depends(get_superadmin_user)
):
    """
    Activa o desactiva el modo de producción
    Requiere código de confirmación para activar producción
    Solo SuperAdmin puede acceder
    """
    # Código de confirmación requerido para activar producción
    CONFIRMATION_CODE = "ACTIVAR_PRODUCCION_2025"
    
    if request.enable_production:
        if request.confirmation_code != CONFIRMATION_CODE:
            raise HTTPException(
                status_code=400,
                detail=f"Código de confirmación requerido para activar producción. Use: {CONFIRMATION_CODE}"
            )
        
        # Activar modo producción
        os.environ["REPARTO_CIERRE_PRODUCTION"] = "true"
        cierre_service.production_mode = True
        
        message = "⚠️ MODO PRODUCCIÓN ACTIVADO - Los cierres se enviarán al sistema real"
        
    else:
        # Desactivar modo producción
        os.environ["REPARTO_CIERRE_PRODUCTION"] = "false"
        cierre_service.production_mode = False
        
        message = "✅ MODO DESARROLLO ACTIVADO - Los cierres serán simulados"
    
    return {
        "success": True,
        "message": message,
        "production_mode": cierre_service.production_mode,
        "changed_by": current_user.username,
        "soap_url": cierre_service.soap_url
    }

@router.post("/test-connection")
def test_soap_connection(current_user: User = Depends(get_superadmin_user)):
    """
    Prueba la conexión al servicio SOAP sin enviar datos
    Solo SuperAdmin puede acceder
    """
    import requests
    
    try:
        # Ping simple al servidor
        response = requests.get(f"http://192.168.0.8:97/service1.asmx", timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "✅ Conexión al servidor SOAP exitosa",
                "server_status": response.status_code,
                "server_url": cierre_service.soap_url
            }
        else:
            return {
                "success": False,
                "message": f"⚠️ Servidor responde pero con status {response.status_code}",
                "server_status": response.status_code,
                "server_url": cierre_service.soap_url
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "❌ No se puede conectar al servidor SOAP",
            "error": "Connection refused",
            "server_url": cierre_service.soap_url
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "❌ Timeout al conectar con el servidor SOAP",
            "error": "Timeout",
            "server_url": cierre_service.soap_url
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error inesperado: {str(e)}",
            "error": str(e),
            "server_url": cierre_service.soap_url
        }

@router.get("/soap-info")
def get_soap_info(current_user: User = Depends(get_superadmin_user)):
    """
    Obtiene información detallada del servicio SOAP
    Solo SuperAdmin puede acceder
    """
    return {
        "soap_url": cierre_service.soap_url,
        "soap_namespace": cierre_service.soap_namespace,
        "production_mode": cierre_service.production_mode,
        "default_usuario": cierre_service.default_usuario,
        "endpoint_methods": {
            "reparto_cerrar": {
                "url": f"{cierre_service.soap_url}/reparto_cerrar",
                "method": "POST",
                "content_type": "application/soap+xml; charset=utf-8",
                "soap_action": f"{cierre_service.soap_namespace}reparto_cerrar"
            }
        },
        "test_data_example": {
            "idreparto": 123,
            "fecha": "28/07/2025",
            "ajustar_envases": 0,
            "efectivo_importe": "15000",
            "retenciones": "[]",
            "cheques": "[]",
            "usuario": cierre_service.default_usuario
        }
    }
