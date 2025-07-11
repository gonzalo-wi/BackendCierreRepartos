from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging
from database import SessionLocal
from models.deposit import Deposit
from models.cheque_retencion import Cheque, Retencion, TipoConcepto
from sqlalchemy.orm import Session

# Modelos Pydantic para validación
class ChequeModel(BaseModel):
    nrocta: int
    concepto: str
    banco: str
    sucursal: str
    localidad: str
    nro_cheque: str
    nro_cuenta: int
    titular: str
    fecha: str
    importe: float

class RetencionModel(BaseModel):
    nrocta: int
    concepto: str
    nro_retencion: int
    fecha: str
    importe: float

class MovimientoFinancieroRequest(BaseModel):
    tipo_concepto: str  # "CHE" o "RIB"
    deposit_id: str  # ID del depósito al que se asocian los cheques/retenciones
    cheques: Optional[List[ChequeModel]] = []
    retenciones: Optional[List[RetencionModel]] = []

# Dependency para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

@router.post("/movimientos-financieros")
async def crear_movimiento_financiero(data: MovimientoFinancieroRequest, db: Session = Depends(get_db)):
    try:
        logging.info(f"📥 Recibiendo movimiento para depósito: {data.deposit_id}")
        
        # 1. Buscar el depósito
        deposit = encontrar_deposit(db, data.deposit_id)
        if not deposit:
            raise HTTPException(
                status_code=404, 
                detail=f"Depósito no encontrado: {data.deposit_id}"
            )
        
        # 2. Procesar según el tipo
        resultado = {}
        
        if data.tipo_concepto == "CHE" and data.cheques:
            resultado = procesar_cheques(db, deposit, data.cheques)
        elif data.tipo_concepto == "RIB" and data.retenciones:
            resultado = procesar_retenciones(db, deposit, data.retenciones)
        else:
            raise HTTPException(
                status_code=400,
                detail="Tipo de movimiento inválido o sin datos"
            )
        
        logging.info(f"✅ Movimiento creado exitosamente para {data.deposit_id}")
        return {
            "success": True, 
            "deposit": {
                "id": deposit.id,
                "deposit_id": deposit.deposit_id,
                "user_name": deposit.user_name
            },
            "movimiento": resultado
        }
        
    except Exception as e:
        logging.error(f"❌ Error procesando movimiento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def encontrar_deposit(db: Session, deposit_id: str) -> Deposit:
    """
    Buscar el depósito por deposit_id
    """
    deposit = db.query(Deposit).filter(
        Deposit.deposit_id == deposit_id
    ).first()
    
    return deposit

def procesar_cheques(db: Session, deposit: Deposit, cheques_data: List[ChequeModel]) -> dict:
    """
    Crear cheques en la base de datos asociados al depósito
    """
    cheques_creados = []
    
    for cheque_data in cheques_data:
        cheque = Cheque(
            deposit_id=deposit.deposit_id,
            nrocta=cheque_data.nrocta,
            concepto=cheque_data.concepto,
            banco=cheque_data.banco,
            sucursal=cheque_data.sucursal,
            localidad=cheque_data.localidad,
            nro_cheque=cheque_data.nro_cheque,
            nro_cuenta=cheque_data.nro_cuenta,
            titular=cheque_data.titular,
            fecha=cheque_data.fecha,
            importe=cheque_data.importe
        )
        
        db.add(cheque)
        db.commit()
        db.refresh(cheque)
        
        cheques_creados.append({
            "id": cheque.id,
            "nro_cheque": cheque.nro_cheque,
            "titular": cheque.titular,
            "importe": cheque.importe,
            "fecha": cheque.fecha
        })
    
    logging.info(f"💰 {len(cheques_creados)} cheques creados para depósito {deposit.deposit_id}")
    
    return {
        "tipo": "cheques",
        "cantidad": len(cheques_creados),
        "total_importe": sum(c["importe"] for c in cheques_creados),
        "cheques": cheques_creados
    }

def procesar_retenciones(db: Session, deposit: Deposit, retenciones_data: List[RetencionModel]) -> dict:
    """
    Crear retenciones en la base de datos asociadas al depósito
    """
    retenciones_creadas = []
    
    for retencion_data in retenciones_data:
        retencion = Retencion(
            deposit_id=deposit.deposit_id,
            nrocta=retencion_data.nrocta,
            concepto=retencion_data.concepto,
            nro_retencion=retencion_data.nro_retencion,
            fecha=retencion_data.fecha,
            importe=retencion_data.importe
        )
        
        db.add(retencion)
        db.commit()
        db.refresh(retencion)
        
        retenciones_creadas.append({
            "id": retencion.id,
            "nro_retencion": retencion.nro_retencion,
            "concepto": retencion.concepto,
            "importe": retencion.importe,
            "fecha": retencion.fecha
        })
    
    logging.info(f"🏦 {len(retenciones_creadas)} retenciones creadas para depósito {deposit.deposit_id}")
    
    return {
        "tipo": "retenciones", 
        "cantidad": len(retenciones_creadas),
        "total_importe": sum(r["importe"] for r in retenciones_creadas),
        "retenciones": retenciones_creadas
    }

@router.get("/deposits/{deposit_id}/movimientos")
async def obtener_movimientos_deposit(deposit_id: str, db: Session = Depends(get_db)):
    """
    Obtener todos los cheques y retenciones de un depósito
    """
    deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
    
    if not deposit:
        raise HTTPException(status_code=404, detail=f"Depósito {deposit_id} no encontrado")
    
    return {
        "deposit": {
            "id": deposit.id,
            "deposit_id": deposit.deposit_id,
            "user_name": deposit.user_name,
            "total_amount": deposit.total_amount
        },
        "cheques": [
            {
                "id": c.id,
                "nro_cheque": c.nro_cheque,
                "titular": c.titular,
                "banco": c.banco,
                "importe": c.importe,
                "fecha": c.fecha
            } for c in deposit.cheques
        ],
        "retenciones": [
            {
                "id": r.id,
                "nro_retencion": r.nro_retencion,
                "concepto": r.concepto,
                "importe": r.importe,
                "fecha": r.fecha
            } for r in deposit.retenciones
        ],
        "totales": {
            "cheques_count": len(deposit.cheques),
            "cheques_total": sum(c.importe for c in deposit.cheques),
            "retenciones_count": len(deposit.retenciones),
            "retenciones_total": sum(r.importe for r in deposit.retenciones)
        }
    }
