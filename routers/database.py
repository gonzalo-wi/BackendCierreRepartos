"""
Router para operaciones CRUD de la base de datos
"""
import traceback
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from schemas.requests import StatusUpdateRequest, ExpectedAmountUpdateRequest
from sqlalchemy import func, text, Date, distinct
import os

def get_date_function(column):
    """
    Función auxiliar para extraer la fecha de un datetime, compatible con diferentes bases de datos
    """
    db_type = os.getenv("DB_TYPE", "sqlserver")
    if db_type == "sqlserver":
        # En SQL Server usamos CAST para extraer solo la fecha
        return func.cast(column, Date)
    else:
        # Para SQLite u otras bases de datos
        return func.date(column)

router = APIRouter(
    prefix="/db",
    tags=["database-operations"]
)


@router.get("/deposits/by-plant")
def get_deposits_from_db_by_plant(date: str = Query(...)):
    """
    Obtiene depósitos desde la base de datos organizados por planta
    Auto-sincroniza datos frescos de miniBank y valores esperados de la API externa
    """
    try:
        from database import SessionLocal
        from sqlalchemy import func
        from datetime import datetime as dt
        from models.deposit import Deposit
        from services.deposits_service import get_all_deposits, save_deposits_to_db
        from services.repartos_api_service import actualizar_depositos_esperados
        
        # Verificar si es hoy y auto-sincronizar datos frescos de miniBank
        today = datetime.now().strftime("%Y-%m-%d")
        auto_synced_minibank = False
        
        if date == today:
            try:
                print(f"🔄 Auto-sincronizando datos frescos de miniBank para hoy: {date}")
                # Obtener datos frescos de la API de miniBank y guardarlos
                fresh_data = get_all_deposits(date)
                save_deposits_to_db(fresh_data)
                auto_synced_minibank = True
                print("✅ Datos de miniBank sincronizados")
            except Exception as sync_error:
                print(f"⚠️ Error en auto-sincronización de miniBank: {sync_error}")
        
        # SIEMPRE sincronizar valores esperados desde la API externa (para cualquier fecha)
        try:
            print(f"🔄 Auto-sincronizando valores esperados desde API externa para {date}...")
            resultado_esperados = actualizar_depositos_esperados(date)
            print(f"💰 Valores esperados: {resultado_esperados.get('actualizados', 0)} depósitos actualizados")
            auto_synced_expected = True
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            auto_synced_expected = False
        
        db = SessionLocal()
        
        # Convertir string de fecha a objeto datetime para comparar
        query_date = dt.strptime(date, "%Y-%m-%d").date()
        
        # Consultar depósitos de la fecha especificada
        deposits = db.query(Deposit).filter(
            get_date_function(Deposit.date_time) == query_date
        ).all()
        
        # Organizar por planta
        plants = {
            "jumillano": {
                "name": "Jumillano",
                "machines": ["L-EJU-001", "L-EJU-002"],
                "deposits": [],
                "total": 0
            },
            "plata": {
                "name": "La Plata", 
                "machines": ["L-EJU-003"],
                "deposits": [],
                "total": 0
            },
            "nafa": {
                "name": "Nafa",
                "machines": ["L-EJU-004"],
                "deposits": [],
                "total": 0
            }
        }
        
        # Clasificar depósitos por planta
        for deposit in deposits:
            deposit_data = {
                "deposit_id": deposit.deposit_id,
                "identifier": deposit.identifier,
                "user_name": deposit.user_name,
                "total_amount": deposit.total_amount,
                "deposit_esperado": deposit.deposit_esperado,
                "composicion_esperado": deposit.composicion_esperado,  # Nuevo campo
                "diferencia": deposit.diferencia,
                "tiene_diferencia": deposit.tiene_diferencia,
                "estado": deposit.estado.value if deposit.estado else "PENDIENTE",
                "currency_code": deposit.currency_code,
                "deposit_type": deposit.deposit_type,
                "date_time": deposit.date_time.isoformat(),
                "pos_name": deposit.pos_name,
                "st_name": deposit.st_name,
                # Agregar cheques y retenciones directamente
                "cheques": [{
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
                    "importe": float(cheque.importe) if cheque.importe else 0.0
                } for cheque in deposit.cheques],
                "retenciones": [{
                    "id": retencion.id,
                    "nrocta": retencion.nrocta,
                    "concepto": retencion.concepto,
                    "nro_retencion": retencion.nro_retencion,
                    "fecha": retencion.fecha,
                    "importe": float(retencion.importe) if retencion.importe else 0.0
                } for retencion in deposit.retenciones],
                "total_cheques": len(deposit.cheques),
                "total_retenciones": len(deposit.retenciones)
            }
            
            if deposit.identifier in plants["jumillano"]["machines"]:
                plants["jumillano"]["deposits"].append(deposit_data)
                plants["jumillano"]["total"] += deposit.total_amount
            elif deposit.identifier in plants["plata"]["machines"]:
                plants["plata"]["deposits"].append(deposit_data)
                plants["plata"]["total"] += deposit.total_amount
            elif deposit.identifier in plants["nafa"]["machines"]:
                plants["nafa"]["deposits"].append(deposit_data)
                plants["nafa"]["total"] += deposit.total_amount
        
        # Agregar contadores
        for plant in plants.values():
            plant["count"] = len(plant["deposits"])
            # Ordenar por fecha/hora descendente
            plant["deposits"].sort(key=lambda x: x["date_time"], reverse=True)
        
        db.close()
        
        return {
            "status": "ok",
            "date": date,
            "source": "database",
            "auto_synced_minibank": auto_synced_minibank,
            "auto_synced_expected": auto_synced_expected,
            "is_today": date == today,
            "plants": plants,
            "summary": {
                "jumillano_total": plants["jumillano"]["total"],
                "jumillano_count": plants["jumillano"]["count"],
                "plata_total": plants["plata"]["total"],
                "plata_count": plants["plata"]["count"],
                "nafa_total": plants["nafa"]["total"],
                "nafa_count": plants["nafa"]["count"],
                "grand_total": plants["jumillano"]["total"] + plants["plata"]["total"] + plants["nafa"]["total"],
                "total_deposits": sum(plant["count"] for plant in plants.values())
            }
        }
        
    except Exception as e:
        print(f"❌ Error al consultar BD: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deposits/by-machine")
def get_deposits_from_db_by_machine(date: str = Query(...)):
    """
    Obtiene depósitos desde la base de datos organizados por máquina
    """
    try:
        from database import SessionLocal
        from sqlalchemy import func
        from datetime import datetime as dt
        from models.deposit import Deposit
        
        db = SessionLocal()
        
        # Convertir string de fecha a objeto datetime para comparar
        query_date = dt.strptime(date, "%Y-%m-%d").date()
        
        # Consultar depósitos de la fecha especificada
        deposits = db.query(Deposit).filter(
            get_date_function(Deposit.date_time) == query_date
        ).all()
        
        # Organizar por máquina
        machines = {}
        
        for deposit in deposits:
            machine_id = deposit.identifier
            
            if machine_id not in machines:
                machines[machine_id] = {
                    "identifier": machine_id,
                    "st_name": deposit.st_name,
                    "pos_name": deposit.pos_name,
                    "deposits": [],
                    "total": 0,
                    "count": 0
                }
            
            deposit_data = {
                "deposit_id": deposit.deposit_id,
                "user_name": deposit.user_name,
                "total_amount": deposit.total_amount,
                "deposit_esperado": deposit.deposit_esperado,
                "composicion_esperado": deposit.composicion_esperado,  # Nuevo campo
                "diferencia": deposit.diferencia,
                "tiene_diferencia": deposit.tiene_diferencia,
                "estado": deposit.estado.value if deposit.estado else "PENDIENTE",
                "currency_code": deposit.currency_code,
                "deposit_type": deposit.deposit_type,
                "date_time": deposit.date_time.isoformat(),
            }
            
            machines[machine_id]["deposits"].append(deposit_data)
            machines[machine_id]["total"] += deposit.total_amount
            machines[machine_id]["count"] += 1
        
        # Ordenar depósitos por fecha/hora dentro de cada máquina
        for machine in machines.values():
            machine["deposits"].sort(key=lambda x: x["date_time"], reverse=True)
        
        db.close()
        
        return {
            "status": "ok",
            "date": date,
            "source": "database",
            "machines": machines,
            "summary": {
                "total_machines": len(machines),
                "grand_total": sum(machine["total"] for machine in machines.values()),
                "total_deposits": sum(machine["count"] for machine in machines.values())
            }
        }
        
    except Exception as e:
        print(f"❌ Error al consultar BD: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deposits/dates")
def get_available_dates():
    """
    Obtiene todas las fechas disponibles en la base de datos
    """
    try:
        from database import SessionLocal
        from sqlalchemy import func, distinct
        from models.deposit import Deposit
        
        db = SessionLocal()
        
        # Obtener fechas únicas
        dates = db.query(
            distinct(get_date_function(Deposit.date_time)).label('date')
        ).order_by(get_date_function(Deposit.date_time).desc()).all()
        
        # Convertir a lista de strings
        available_dates = []
        for date_row in dates:
            if hasattr(date_row.date, 'strftime'):
                available_dates.append(date_row.date.strftime("%Y-%m-%d"))
            else:
                available_dates.append(str(date_row.date))
        
        db.close()
        
        return {
            "status": "ok",
            "dates": available_dates,
            "count": len(available_dates)
        }
        
    except Exception as e:
        print(f"❌ Error al obtener fechas: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deposits/summary")
def get_db_summary():
    """
    Obtiene un resumen general de la base de datos
    """
    try:
        from database import SessionLocal
        from sqlalchemy import func, distinct
        from models.deposit import Deposit
        
        db = SessionLocal()
        
        # Estadísticas generales
        total_deposits = db.query(func.count(Deposit.id)).scalar()
        total_amount = db.query(func.sum(Deposit.total_amount)).scalar() or 0
        unique_machines = db.query(func.count(distinct(Deposit.identifier))).scalar()
        date_range = db.query(
            func.min(get_date_function(Deposit.date_time)).label('min_date'),
            func.max(get_date_function(Deposit.date_time)).label('max_date')
        ).first()
        
        # Totales por máquina
        machine_totals = db.query(
            Deposit.identifier,
            Deposit.st_name,
            func.count(Deposit.id).label('deposit_count'),
            func.sum(Deposit.total_amount).label('total_amount')
        ).group_by(Deposit.identifier, Deposit.st_name).all()
        
        machines_summary = []
        for machine in machine_totals:
            machines_summary.append({
                "identifier": machine.identifier,
                "st_name": machine.st_name,
                "deposit_count": machine.deposit_count,
                "total_amount": machine.total_amount
            })
        
        db.close()
        
        return {
            "status": "ok",
            "summary": {
                "total_deposits": total_deposits,
                "total_amount": float(total_amount),
                "unique_machines": unique_machines,
                "date_range": {
                    "from": date_range.min_date.strftime("%Y-%m-%d") if date_range.min_date else None,
                    "to": date_range.max_date.strftime("%Y-%m-%d") if date_range.max_date else None
                }
            },
            "machines": machines_summary
        }
        
    except Exception as e:
        print(f"❌ Error al obtener resumen: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/deposits/{deposit_id}/status")
def update_deposit_status(deposit_id: str, request: StatusUpdateRequest):
    """
    Actualiza el estado de un depósito específico
    Frontend solo puede cambiar de PENDIENTE a LISTO
    """
    try:
        from database import SessionLocal
        from models.deposit import Deposit, EstadoDeposito
        
        status_str = request.status
        
        # Validar que el estado es válido para frontend
        if status_str not in ["PENDIENTE", "LISTO"]:
            raise HTTPException(
                status_code=400, 
                detail="Frontend solo puede cambiar estados entre PENDIENTE y LISTO"
            )
        
        try:
            nuevo_estado = EstadoDeposito(status_str)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Estado inválido"
            )
        
        db = SessionLocal()
        
        # Buscar el depósito
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        
        if not deposit:
            db.close()
            raise HTTPException(status_code=404, detail=f"Depósito {deposit_id} no encontrado")
        
        # Validar transiciones permitidas para frontend
        current_status = deposit.estado.value if deposit.estado else "PENDIENTE"
        
        if current_status == "ENVIADO":
            db.close()
            raise HTTPException(
                status_code=400, 
                detail="No se puede modificar un depósito ya ENVIADO"
            )
        
        # Solo permitir: PENDIENTE ↔ LISTO
        if not ((current_status == "PENDIENTE" and nuevo_estado.value == "LISTO") or 
                (current_status == "LISTO" and nuevo_estado.value == "PENDIENTE")):
            db.close()
            raise HTTPException(
                status_code=400, 
                detail=f"Transición no permitida: {current_status} → {nuevo_estado.value}"
            )
        
        # Actualizar el estado
        old_status = deposit.estado.value if deposit.estado else "PENDIENTE"
        deposit.estado = nuevo_estado
        
        db.commit()
        db.refresh(deposit)
        
        # Preparar respuesta
        result = {
            "status": "ok",
            "message": f"Estado actualizado de {old_status} a {nuevo_estado.value}",
            "deposit": {
                "deposit_id": deposit.deposit_id,
                "user_name": deposit.user_name,
                "total_amount": deposit.total_amount,
                "deposit_esperado": deposit.deposit_esperado,
                "diferencia": deposit.diferencia,
                "tiene_diferencia": deposit.tiene_diferencia,
                "estado": deposit.estado.value,
                "date_time": deposit.date_time.isoformat(),
                "pos_name": deposit.pos_name,
                "st_name": deposit.st_name
            }
        }
        
        db.close()
        
        print(f"✅ Estado del depósito {deposit_id} actualizado: {old_status} → {nuevo_estado.value}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al actualizar estado del depósito {deposit_id}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/deposits/{deposit_id}/expected-amount")
def update_deposit_expected_amount(deposit_id: str, request: ExpectedAmountUpdateRequest):
    """
    Actualiza el monto esperado de un depósito y recalcula el estado automáticamente
    """
    try:
        from database import SessionLocal
        from models.deposit import Deposit
        
        monto_esperado = request.deposit_esperado
        
        # Validar que sea un número positivo
        if monto_esperado < 0:
            raise HTTPException(status_code=400, detail="El monto esperado debe ser un número positivo")
        
        db = SessionLocal()
        
        # Buscar el depósito
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        
        if not deposit:
            db.close()
            raise HTTPException(status_code=404, detail=f"Depósito {deposit_id} no encontrado")
        
        # Actualizar el monto esperado
        old_expected = deposit.deposit_esperado
        deposit.deposit_esperado = monto_esperado
        
        # Actualizar estado automáticamente
        old_status = deposit.estado.value if deposit.estado else "PENDIENTE"
        deposit.actualizar_estado()
        
        db.commit()
        db.refresh(deposit)
        
        # Preparar respuesta
        result = {
            "status": "ok",
            "message": f"Monto esperado actualizado de {old_expected} a {deposit.deposit_esperado}",
            "status_change": old_status != deposit.estado.value,
            "deposit": {
                "deposit_id": deposit.deposit_id,
                "user_name": deposit.user_name,
                "total_amount": deposit.total_amount,
                "deposit_esperado": deposit.deposit_esperado,
                "diferencia": deposit.diferencia,
                "tiene_diferencia": deposit.tiene_diferencia,
                "estado": deposit.estado.value,
                "date_time": deposit.date_time.isoformat(),
                "pos_name": deposit.pos_name,
                "st_name": deposit.st_name
            }
        }
        
        db.close()
        
        print(f"✅ Monto esperado del depósito {deposit_id} actualizado: {old_expected} → {deposit.deposit_esperado}")
        print(f"✅ Estado actualizado: {old_status} → {deposit.estado.value}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al actualizar monto esperado del depósito {deposit_id}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deposits/states")
def get_available_states():
    """
    Obtiene los estados disponibles para el frontend
    Solo PENDIENTE y LISTO (ENVIADO es para uso interno)
    """
    return {
        "status": "ok",
        "states": [
            {"value": "PENDIENTE", "label": "PENDIENTE"},
            {"value": "LISTO", "label": "LISTO"}
        ]
    }


@router.put("/deposits/{deposit_id}/mark-sent")
def mark_deposit_as_sent(deposit_id: str):
    """
    Marca un depósito como ENVIADO (solo para uso interno del backend)
    """
    try:
        from database import SessionLocal
        from models.deposit import Deposit, EstadoDeposito
        
        db = SessionLocal()
        
        # Buscar el depósito
        deposit = db.query(Deposit).filter(Deposit.deposit_id == deposit_id).first()
        
        if not deposit:
            db.close()
            raise HTTPException(status_code=404, detail=f"Depósito {deposit_id} no encontrado")
        
        current_status = deposit.estado.value if deposit.estado else "PENDIENTE"
        
        # Solo se puede enviar si está LISTO
        if current_status != "LISTO":
            db.close()
            raise HTTPException(
                status_code=400, 
                detail=f"Solo se pueden enviar depósitos en estado LISTO. Estado actual: {current_status}"
            )
        
        # Cambiar a ENVIADO
        old_status = deposit.estado.value
        deposit.estado = EstadoDeposito.ENVIADO
        
        db.commit()
        db.refresh(deposit)
        
        # Preparar respuesta
        result = {
            "status": "ok",
            "message": f"Depósito marcado como enviado: {old_status} → ENVIADO",
            "deposit": {
                "deposit_id": deposit.deposit_id,
                "user_name": deposit.user_name,
                "total_amount": deposit.total_amount,
                "deposit_esperado": deposit.deposit_esperado,
                "diferencia": deposit.diferencia,
                "tiene_diferencia": deposit.tiene_diferencia,
                "estado": deposit.estado.value,
                "date_time": deposit.date_time.isoformat(),
                "pos_name": deposit.pos_name,
                "st_name": deposit.st_name
            }
        }
        
        db.close()
        
        print(f"✅ Depósito {deposit_id} marcado como ENVIADO: {old_status} → ENVIADO")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al marcar depósito como enviado {deposit_id}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
