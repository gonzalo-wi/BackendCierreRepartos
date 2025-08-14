from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from database import SessionLocal
from models.deposit import Deposit
from models.cheque_retencion import Cheque, Retencion
from models.user import User
from auth.dependencies import get_any_user
from datetime import datetime

# Importar utilidades de logging
from utils.logging_utils import log_user_action, log_technical_error, log_technical_warning
from middleware.logging_middleware import log_endpoint_access

router = APIRouter(
    prefix="/cheques-retenciones",
    tags=["cheques-retenciones"]
)

# Schemas para Pydantic
class ChequeCreate(BaseModel):
    deposit_id: str
    nrocta: Optional[int] = None
    concepto: Optional[str] = None
    banco: Optional[str] = None
    sucursal: Optional[str] = None
    localidad: Optional[str] = None
    nro_cheque: Optional[str] = None
    nro_cuenta: Optional[int] = None
    titular: Optional[str] = None
    fecha: Optional[str] = None
    importe: float

class RetencionCreate(BaseModel):
    deposit_id: str
    nrocta: Optional[int] = None
    concepto: Optional[str] = None
    nro_retencion: Optional[int] = None
    fecha: Optional[str] = None
    importe: float

class ChequeUpdate(BaseModel):
    nrocta: Optional[int] = None
    concepto: Optional[str] = None
    banco: Optional[str] = None
    sucursal: Optional[str] = None
    localidad: Optional[str] = None
    nro_cheque: Optional[str] = None
    nro_cuenta: Optional[int] = None
    titular: Optional[str] = None
    fecha: Optional[str] = None
    importe: Optional[float] = None

class RetencionUpdate(BaseModel):
    nrocta: Optional[int] = None
    concepto: Optional[str] = None
    nro_retencion: Optional[int] = None
    fecha: Optional[str] = None
    importe: Optional[float] = None

# ENDPOINTS PARA CHEQUES
@router.post("/cheques")
@log_endpoint_access("CREATE_CHEQUE", "cheques")
def crear_cheque(
    request: Request,
    cheque_data: ChequeCreate,
    current_user: User = Depends(get_any_user)
):
    """Crear un nuevo cheque asociado a un depósito"""
    db = SessionLocal()
    try:
        # Log del intento de creación
        log_user_action(
            action="ATTEMPT_CREATE_CHEQUE",
            user_id=current_user.username,
            resource="cheques",
            request=request,
            extra_data={
                "deposit_id": cheque_data.deposit_id,
                "importe": cheque_data.importe,
                "banco": cheque_data.banco,
                "nro_cheque": cheque_data.nro_cheque
            }
        )
        
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == cheque_data.deposit_id).first()
        if not deposit:
            log_technical_warning(
                f"Intento de crear cheque para depósito inexistente: {cheque_data.deposit_id}",
                "cheque_creation_validation",
                user_id=current_user.username,
                request=request,
                extra_data={"deposit_id": cheque_data.deposit_id}
            )
            
            raise HTTPException(
                status_code=404,
                detail=f"Depósito {cheque_data.deposit_id} no encontrado"
            )
        
        # Convertir fecha si es necesario (de YYYY-MM-DD a dd/MM/yyyy)
        if cheque_data.fecha and "-" in cheque_data.fecha and len(cheque_data.fecha) == 10:
            try:
                fecha_obj = datetime.strptime(cheque_data.fecha, "%Y-%m-%d")
                cheque_data.fecha = fecha_obj.strftime("%d/%m/%Y")
            except ValueError:
                # Si falla, mantener el valor original
                pass
        
        # Crear el cheque
        cheque = Cheque(**cheque_data.dict())
        db.add(cheque)
        db.commit()
        db.refresh(cheque)
        
        # Log de creación exitosa
        log_user_action(
            action="CREATE_CHEQUE_SUCCESS",
            user_id=current_user.username,
            resource="cheques",
            resource_id=str(cheque.id),
            request=request,
            success=True,
            extra_data={
                "cheque_id": cheque.id,
                "deposit_id": cheque.deposit_id,
                "importe": cheque.importe,
                "banco": cheque.banco,
                "nro_cheque": cheque.nro_cheque
            }
        )
        
        return {
            "success": True,
            "message": "Cheque creado exitosamente",
            "cheque_id": cheque.id,
            "deposit_id": cheque.deposit_id,
            "importe": cheque.importe
        }
        
    except HTTPException:
        # Re-lanzar HTTPExceptions sin modificar
        raise
    except Exception as e:
        db.rollback()
        
        # Log del error técnico
        log_technical_error(
            e,
            "create_cheque_endpoint",
            user_id=current_user.username,
            request=request,
            extra_data={
                "deposit_id": cheque_data.deposit_id,
                "importe": cheque_data.importe
            }
        )
        
        # Log de creación fallida
        log_user_action(
            action="CREATE_CHEQUE_FAILED",
            user_id=current_user.username,
            resource="cheques",
            request=request,
            success=False,
            extra_data={
                "deposit_id": cheque_data.deposit_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear cheque: {str(e)}"
        )
    finally:
        db.close()

@router.get("/cheques/deposit/{deposit_id}")
def obtener_cheques_por_deposito(
    deposit_id: str,
    current_user: User = Depends(get_any_user)
):
    """Obtener todos los cheques de un depósito específico"""
    db = SessionLocal()
    try:
        cheques = db.query(Cheque).filter(Cheque.deposit_id == deposit_id).all()
        
        cheques_data = []
        for cheque in cheques:
            cheques_data.append({
                "id": cheque.id,
                "deposit_id": cheque.deposit_id,
                "nrocta": cheque.nrocta,
                "concepto": cheque.concepto,
                "banco": cheque.banco,
                "sucursal": cheque.sucursal,
                "localidad": cheque.localidad,
                "nro_cheque": cheque.nro_cheque,
                "nro_cuenta": cheque.nro_cuenta,
                "titular": cheque.titular,
                "fecha": cheque.fecha,
                "importe": cheque.importe
            })
        
        return {
            "success": True,
            "total": len(cheques_data),
            "cheques": cheques_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener cheques: {str(e)}"
        )
    finally:
        db.close()

@router.put("/cheques/{cheque_id}")
def actualizar_cheque(
    cheque_id: int,
    cheque_data: ChequeUpdate,
    current_user: User = Depends(get_any_user)
):
    """Actualizar un cheque existente"""
    db = SessionLocal()
    try:
        cheque = db.query(Cheque).filter(Cheque.id == cheque_id).first()
        if not cheque:
            raise HTTPException(
                status_code=404,
                detail=f"Cheque {cheque_id} no encontrado"
            )
        
        # Actualizar solo los campos proporcionados
        for field, value in cheque_data.dict(exclude_unset=True).items():
            # Conversión especial para fechas
            if field == "fecha" and value:
                # Convertir de YYYY-MM-DD a dd/MM/yyyy si es necesario
                if "-" in value and len(value) == 10:
                    try:
                        fecha_obj = datetime.strptime(value, "%Y-%m-%d")
                        value = fecha_obj.strftime("%d/%m/%Y")
                    except ValueError:
                        # Si falla, mantener el valor original
                        pass
            
            setattr(cheque, field, value)
        
        db.commit()
        db.refresh(cheque)
        
        return {
            "success": True,
            "message": "Cheque actualizado exitosamente",
            "cheque_id": cheque.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar cheque: {str(e)}"
        )
    finally:
        db.close()

@router.delete("/cheques/{cheque_identifier}")
@log_endpoint_access("DELETE_CHEQUE", "cheques")
def eliminar_cheque(
    request: Request,
    cheque_identifier: str,
    current_user: User = Depends(get_any_user)
):
    """Eliminar un cheque por ID o número de cheque"""
    db = SessionLocal()
    try:
        cheque = None
        
        # Intentar buscar por ID primero (si es numérico)
        if cheque_identifier.isdigit():
            cheque_id = int(cheque_identifier)
            cheque = db.query(Cheque).filter(Cheque.id == cheque_id).first()
        
        # Si no se encontró por ID, buscar por número de cheque
        if not cheque:
            cheque = db.query(Cheque).filter(Cheque.nro_cheque == cheque_identifier).first()
        
        if not cheque:
            log_technical_warning(
                f"Intento de eliminar cheque inexistente: {cheque_identifier}",
                "delete_cheque_validation",
                user_id=current_user.username,
                request=request,
                extra_data={"cheque_identifier": cheque_identifier}
            )
            
            raise HTTPException(
                status_code=404,
                detail=f"Cheque {cheque_identifier} no encontrado"
            )
        
        # Guardar información del cheque antes de eliminarlo para el log
        cheque_info = {
            "cheque_id": cheque.id,
            "deposit_id": cheque.deposit_id,
            "importe": cheque.importe,
            "banco": cheque.banco,
            "nro_cheque": cheque.nro_cheque,
            "searched_by": cheque_identifier
        }
        
        db.delete(cheque)
        db.commit()
        
        # Log de eliminación exitosa
        log_user_action(
            action="DELETE_CHEQUE_SUCCESS",
            user_id=current_user.username,
            resource="cheques",
            resource_id=str(cheque.id),
            request=request,
            success=True,
            extra_data=cheque_info
        )
        
        return {
            "success": True,
            "message": "Cheque eliminado exitosamente"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar cheque: {str(e)}"
        )
    finally:
        db.close()

# ENDPOINTS PARA RETENCIONES
@router.post("/retenciones")
@log_endpoint_access("CREATE_RETENCION", "retenciones")
def crear_retencion(
    request: Request,
    retencion_data: RetencionCreate,
    current_user: User = Depends(get_any_user)
):
    """Crear una nueva retención asociada a un depósito"""
    db = SessionLocal()
    try:
        # Log del intento de creación
        log_user_action(
            action="ATTEMPT_CREATE_RETENCION",
            user_id=current_user.username,
            resource="retenciones",
            request=request,
            extra_data={
                "deposit_id": retencion_data.deposit_id,
                "importe": retencion_data.importe,
                "concepto": retencion_data.concepto,
                "nro_retencion": retencion_data.nro_retencion
            }
        )
        
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == retencion_data.deposit_id).first()
        if not deposit:
            log_technical_warning(
                f"Intento de crear retención para depósito inexistente: {retencion_data.deposit_id}",
                "retencion_creation_validation",
                user_id=current_user.username,
                request=request,
                extra_data={"deposit_id": retencion_data.deposit_id}
            )
            
            raise HTTPException(
                status_code=404,
                detail=f"Depósito {retencion_data.deposit_id} no encontrado"
            )
        
        # Crear la retención
        retencion = Retencion(**retencion_data.dict())
        db.add(retencion)
        db.commit()
        db.refresh(retencion)
        
        # Log de creación exitosa
        log_user_action(
            action="CREATE_RETENCION_SUCCESS",
            user_id=current_user.username,
            resource="retenciones",
            resource_id=str(retencion.id),
            request=request,
            success=True,
            extra_data={
                "retencion_id": retencion.id,
                "deposit_id": retencion.deposit_id,
                "importe": retencion.importe,
                "concepto": retencion.concepto,
                "nro_retencion": retencion.nro_retencion
            }
        )
        
        return {
            "success": True,
            "message": "Retención creada exitosamente",
            "retencion_id": retencion.id,
            "deposit_id": retencion.deposit_id,
            "importe": retencion.importe
        }
        
    except HTTPException:
        # Re-lanzar HTTPExceptions sin modificar
        raise
    except Exception as e:
        db.rollback()
        
        # Log del error técnico
        log_technical_error(
            e,
            "create_retencion_endpoint",
            user_id=current_user.username,
            request=request,
            extra_data={
                "deposit_id": retencion_data.deposit_id,
                "importe": retencion_data.importe
            }
        )
        
        # Log de creación fallida
        log_user_action(
            action="CREATE_RETENCION_FAILED",
            user_id=current_user.username,
            resource="retenciones",
            request=request,
            success=False,
            extra_data={
                "deposit_id": retencion_data.deposit_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear retención: {str(e)}"
        )
    finally:
        db.close()

@router.get("/retenciones/deposit/{deposit_id}")
def obtener_retenciones_por_deposito(
    deposit_id: str,
    current_user: User = Depends(get_any_user)
):
    """Obtener todas las retenciones de un depósito específico"""
    db = SessionLocal()
    try:
        retenciones = db.query(Retencion).filter(Retencion.deposit_id == deposit_id).all()
        
        retenciones_data = []
        for retencion in retenciones:
            retenciones_data.append({
                "id": retencion.id,
                "deposit_id": retencion.deposit_id,
                "nrocta": retencion.nrocta,
                "concepto": retencion.concepto,
                "nro_retencion": retencion.nro_retencion,
                "fecha": retencion.fecha,
                "importe": retencion.importe
            })
        
        return {
            "success": True,
            "total": len(retenciones_data),
            "retenciones": retenciones_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener retenciones: {str(e)}"
        )
    finally:
        db.close()

@router.put("/retenciones/{retencion_id}")
def actualizar_retencion(
    retencion_id: int,
    retencion_data: RetencionUpdate,
    current_user: User = Depends(get_any_user)
):
    """Actualizar una retención existente"""
    db = SessionLocal()
    try:
        retencion = db.query(Retencion).filter(Retencion.id == retencion_id).first()
        if not retencion:
            raise HTTPException(
                status_code=404,
                detail=f"Retención {retencion_id} no encontrada"
            )
        
        # Actualizar solo los campos proporcionados
        for field, value in retencion_data.dict(exclude_unset=True).items():
            setattr(retencion, field, value)
        
        db.commit()
        db.refresh(retencion)
        
        return {
            "success": True,
            "message": "Retención actualizada exitosamente",
            "retencion_id": retencion.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar retención: {str(e)}"
        )
    finally:
        db.close()

@router.delete("/retenciones/{retencion_identifier}")
def eliminar_retencion(
    retencion_identifier: str,
    current_user: User = Depends(get_any_user)
):
    """Eliminar una retención por ID o número de retención"""
    db = SessionLocal()
    try:
        retencion = None
        
        # Intentar buscar por ID primero (si es numérico)
        if retencion_identifier.isdigit():
            retencion_id = int(retencion_identifier)
            retencion = db.query(Retencion).filter(Retencion.id == retencion_id).first()
        
        # Si no se encontró por ID, buscar por número de retención
        if not retencion and retencion_identifier.isdigit():
            nro_retencion = int(retencion_identifier)
            retencion = db.query(Retencion).filter(Retencion.nro_retencion == nro_retencion).first()
        
        if not retencion:
            raise HTTPException(
                status_code=404,
                detail=f"Retención número {retencion_identifier} no encontrada"
            )
        
        # Guardar información de la retención antes de eliminarla para el log
        retencion_info = {
            "retencion_id": retencion.id,
            "deposit_id": retencion.deposit_id,
            "importe": retencion.importe,
            "nro_retencion": retencion.nro_retencion,
            "searched_by": retencion_identifier
        }
        
        db.delete(retencion)
        db.commit()
        
        return {
            "success": True,
            "message": "Retención eliminada exitosamente",
            "retencion_info": retencion_info
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar retención: {str(e)}"
        )
    finally:
        db.close()

# ENDPOINT COMBINADO PARA OBTENER CHEQUES Y RETENCIONES DE UN DEPÓSITO
@router.get("/deposit/{deposit_id}/completo")
def obtener_cheques_y_retenciones_por_deposito(
    deposit_id: str,
    current_user: User = Depends(get_any_user)
):
    """Obtener todos los cheques y retenciones de un depósito específico"""
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        if not deposit:
            raise HTTPException(
                status_code=404,
                detail=f"Depósito {deposit_id} no encontrado"
            )
        
        # Obtener cheques
        cheques = db.query(Cheque).filter(Cheque.deposit_id == deposit_id).all()
        cheques_data = []
        total_cheques = 0
        for cheque in cheques:
            cheque_info = {
                "id": cheque.id,
                "nrocta": cheque.nrocta,
                "concepto": cheque.concepto,
                "banco": cheque.banco,
                "sucursal": cheque.sucursal,
                "localidad": cheque.localidad,
                "nro_cheque": cheque.nro_cheque,
                "nro_cuenta": cheque.nro_cuenta,
                "titular": cheque.titular,
                "fecha": cheque.fecha,
                "importe": cheque.importe
            }
            cheques_data.append(cheque_info)
            total_cheques += cheque.importe if cheque.importe else 0
        
        # Obtener retenciones
        retenciones = db.query(Retencion).filter(Retencion.deposit_id == deposit_id).all()
        retenciones_data = []
        total_retenciones = 0
        for retencion in retenciones:
            retencion_info = {
                "id": retencion.id,
                "nrocta": retencion.nrocta,
                "concepto": retencion.concepto,
                "nro_retencion": retencion.nro_retencion,
                "fecha": retencion.fecha,
                "importe": retencion.importe
            }
            retenciones_data.append(retencion_info)
            total_retenciones += retencion.importe if retencion.importe else 0
        
        return {
            "success": True,
            "deposit_id": deposit_id,
            "deposit_info": {
                "user_name": deposit.user_name,
                "total_amount": deposit.total_amount,
                "deposit_esperado": deposit.deposit_esperado,
                "estado": deposit.estado.value
            },
            "cheques": {
                "total": len(cheques_data),
                "total_importe": total_cheques,
                "items": cheques_data
            },
            "retenciones": {
                "total": len(retenciones_data),
                "total_importe": total_retenciones,
                "items": retenciones_data
            },
            "resumen": {
                "total_efectivo": deposit.total_amount,
                "total_cheques": total_cheques,
                "total_retenciones": total_retenciones,
                "total_general": deposit.total_amount + total_cheques + total_retenciones
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener datos completos: {str(e)}"
        )
    finally:
        db.close()
