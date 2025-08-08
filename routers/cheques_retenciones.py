from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from database import SessionLocal
from models.deposit import Deposit
from models.cheque_retencion import Cheque, Retencion
from models.user import User
from auth.dependencies import get_any_user
from datetime import datetime

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
def crear_cheque(
    cheque_data: ChequeCreate,
    current_user: User = Depends(get_any_user)
):
    """Crear un nuevo cheque asociado a un depósito"""
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == cheque_data.deposit_id).first()
        if not deposit:
            raise HTTPException(
                status_code=404,
                detail=f"Depósito {cheque_data.deposit_id} no encontrado"
            )
        
        # Crear el cheque
        cheque = Cheque(**cheque_data.dict())
        db.add(cheque)
        db.commit()
        db.refresh(cheque)
        
        return {
            "success": True,
            "message": "Cheque creado exitosamente",
            "cheque_id": cheque.id,
            "deposit_id": cheque.deposit_id,
            "importe": cheque.importe
        }
        
    except Exception as e:
        db.rollback()
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

@router.delete("/cheques/{cheque_id}")
def eliminar_cheque(
    cheque_id: int,
    current_user: User = Depends(get_any_user)
):
    """Eliminar un cheque"""
    db = SessionLocal()
    try:
        cheque = db.query(Cheque).filter(Cheque.id == cheque_id).first()
        if not cheque:
            raise HTTPException(
                status_code=404,
                detail=f"Cheque {cheque_id} no encontrado"
            )
        
        db.delete(cheque)
        db.commit()
        
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
def crear_retencion(
    retencion_data: RetencionCreate,
    current_user: User = Depends(get_any_user)
):
    """Crear una nueva retención asociada a un depósito"""
    db = SessionLocal()
    try:
        # Verificar que el depósito existe
        deposit = db.query(Deposit).filter(Deposit.deposit_id == retencion_data.deposit_id).first()
        if not deposit:
            raise HTTPException(
                status_code=404,
                detail=f"Depósito {retencion_data.deposit_id} no encontrado"
            )
        
        # Crear la retención
        retencion = Retencion(**retencion_data.dict())
        db.add(retencion)
        db.commit()
        db.refresh(retencion)
        
        return {
            "success": True,
            "message": "Retención creada exitosamente",
            "retencion_id": retencion.id,
            "deposit_id": retencion.deposit_id,
            "importe": retencion.importe
        }
        
    except Exception as e:
        db.rollback()
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

@router.delete("/retenciones/{retencion_id}")
def eliminar_retencion(
    retencion_id: int,
    current_user: User = Depends(get_any_user)
):
    """Eliminar una retención"""
    db = SessionLocal()
    try:
        retencion = db.query(Retencion).filter(Retencion.id == retencion_id).first()
        if not retencion:
            raise HTTPException(
                status_code=404,
                detail=f"Retención {retencion_id} no encontrada"
            )
        
        db.delete(retencion)
        db.commit()
        
        return {
            "success": True,
            "message": "Retención eliminada exitosamente"
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
