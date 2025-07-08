import traceback
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
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
    get_all_totals,
    save_deposits_to_db
    
)

from services.pdf_service import generate_daily_closure_pdf, generate_detailed_repartos_pdf
from fastapi.responses import JSONResponse, Response
from database import Base, engine
from models.deposit import Deposit
from datetime import datetime


app = FastAPI()

Base.metadata.create_all(bind=engine)


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
    

@app.post("/api/deposits/jumillano/save")
def save_jumillano_deposits(date: str = Query(...)):
    try:
        print(f"🔄 Iniciando guardado de depósitos para fecha: {date}")
        data = get_jumillano_deposits(date)
        print("📊 Datos obtenidos, guardando en base de datos...")
        save_deposits_to_db(data)
        print("✅ Proceso completado exitosamente")
        return {"status": "ok", "message": "Depósitos guardados correctamente"}
    except Exception as e:
        print(f"❌ Error en save_jumillano_deposits: {str(e)}")
        traceback.print_exc()  # ⬅️ muestra el stacktrace
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deposits/all/save")
def save_all_deposits(date: str = Query(...)):
    try:
        print(f"🔄 Iniciando guardado de TODOS los depósitos para fecha: {date}")
        data = get_all_deposits(date)
        print("📊 Datos de todas las máquinas obtenidos, guardando en base de datos...")
        save_deposits_to_db(data)
        print("✅ Proceso completado exitosamente para todas las máquinas")
        return {"status": "ok", "message": "Todos los depósitos guardados correctamente"}
    except Exception as e:
        print(f"❌ Error en save_all_deposits: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deposits/plata/save")
def save_plata_deposits(date: str = Query(...)):
    try:
        print(f"🔄 Iniciando guardado de depósitos de La Plata para fecha: {date}")
        data = get_plata_deposits(date)
        print("📊 Datos de La Plata obtenidos, guardando en base de datos...")
        save_deposits_to_db(data)
        print("✅ Proceso completado exitosamente para La Plata")
        return {"status": "ok", "message": "Depósitos de La Plata guardados correctamente"}
    except Exception as e:
        print(f"❌ Error en save_plata_deposits: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deposits/nafa/save")
def save_nafa_deposits(date: str = Query(...)):
    try:
        print(f"🔄 Iniciando guardado de depósitos de Nafa para fecha: {date}")
        data = get_nafa_deposits(date)
        print("📊 Datos de Nafa obtenidos, guardando en base de datos...")
        save_deposits_to_db(data)
        print("✅ Proceso completado exitosamente para Nafa")
        return {"status": "ok", "message": "Depósitos de Nafa guardados correctamente"}
    except Exception as e:
        print(f"❌ Error en save_nafa_deposits: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    """
    Endpoint de verificación de salud del servidor
    """
    return {"status": "ok", "message": "Servidor funcionando correctamente", "timestamp": datetime.now().isoformat()}

@app.get("/api/test-db")
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

@app.get("/api/deposits/sync")
def sync_deposits_today():
    """
    Sincroniza automáticamente los depósitos de hoy y los retorna
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"🔄 Auto-sincronizando depósitos para hoy: {today}")
        
        # Obtener datos
        data = get_all_deposits(today)
        
        # Guardar automáticamente
        save_deposits_to_db(data)
        print("📊 Datos sincronizados automáticamente")
        
        # Retornar los totales también
        totals = get_all_totals(today)
        
        return {
            "status": "ok", 
            "message": "Depósitos sincronizados automáticamente",
            "date": today,
            "data": data,
            "totals": totals
        }
    except Exception as e:
        print(f"❌ Error en sincronización automática: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/totals/sync")
def get_totals_with_sync(date: str = Query(None)):
    """
    Obtiene los totales y sincroniza automáticamente si es necesario
    """
    try:
        # Si no se proporciona fecha, usar hoy
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"🔄 Obteniendo totales con sincronización para: {date}")
        
        # Verificar si es hoy y sincronizar automáticamente
        today = datetime.now().strftime("%Y-%m-%d")
        if date == today:
            # Auto-sincronizar datos de hoy
            data = get_all_deposits(date)
            save_deposits_to_db(data)
            print("📊 Datos de hoy sincronizados automáticamente")
        
        # Obtener totales
        totals = get_all_totals(date)
        
        return {
            "status": "ok",
            "date": date,
            "auto_synced": date == today,
            **totals
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deposits/all/sync")
def get_all_deposits_with_sync(date: str = Query(None)):
    """
    Obtiene todos los depósitos y sincroniza automáticamente si es hoy
    """
    try:
        # Si no se proporciona fecha, usar hoy
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"🔄 Obteniendo depósitos con auto-sync para: {date}")
        
        # Obtener datos
        data = get_all_deposits(date)
        
        # Si es hoy, sincronizar automáticamente
        today = datetime.now().strftime("%Y-%m-%d")
        if date == today:
            save_deposits_to_db(data)
            print("📊 Datos de hoy sincronizados automáticamente en BD")
        
        return {
            "status": "ok",
            "date": date,
            "auto_synced": date == today,
            "data": data
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deposits/db/by-plant")
def get_deposits_from_db_by_plant(date: str = Query(...)):
    """
    Obtiene depósitos desde la base de datos organizados por planta
    Auto-sincroniza si es la fecha de hoy
    """
    try:
        from database import SessionLocal
        from sqlalchemy import and_, func
        from datetime import datetime as dt
        
        # Verificar si es hoy y auto-sincronizar
        today = datetime.now().strftime("%Y-%m-%d")
        auto_synced = False
        
        if date == today:
            try:
                print(f"🔄 Auto-sincronizando datos para hoy: {date}")
                # Obtener datos frescos de la API y guardarlos
                fresh_data = get_all_deposits(date)
                save_deposits_to_db(fresh_data)
                auto_synced = True
                print("✅ Datos auto-sincronizados correctamente")
            except Exception as sync_error:
                print(f"⚠️ Error en auto-sincronización: {sync_error}")
                # Continuar con los datos de la BD aunque falle la sincronización
        
        db = SessionLocal()
        
        # Convertir string de fecha a objeto datetime para comparar
        query_date = dt.strptime(date, "%Y-%m-%d").date()
        
        # Consultar depósitos de la fecha especificada
        deposits = db.query(Deposit).filter(
            func.date(Deposit.date_time) == query_date
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
                "currency_code": deposit.currency_code,
                "deposit_type": deposit.deposit_type,
                "date_time": deposit.date_time.isoformat(),
                "pos_name": deposit.pos_name,
                "st_name": deposit.st_name
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
            "auto_synced": auto_synced,
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

@app.get("/api/deposits/db/by-machine")
def get_deposits_from_db_by_machine(date: str = Query(...)):
    """
    Obtiene depósitos desde la base de datos organizados por máquina
    """
    try:
        from database import SessionLocal
        from sqlalchemy import and_, func
        from datetime import datetime as dt
        
        db = SessionLocal()
        
        # Convertir string de fecha a objeto datetime para comparar
        query_date = dt.strptime(date, "%Y-%m-%d").date()
        
        # Consultar depósitos de la fecha especificada
        deposits = db.query(Deposit).filter(
            func.date(Deposit.date_time) == query_date
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

@app.get("/api/deposits/db/dates")
def get_available_dates():
    """
    Obtiene todas las fechas disponibles en la base de datos
    """
    try:
        from database import SessionLocal
        from sqlalchemy import func, distinct
        
        db = SessionLocal()
        
        # Obtener fechas únicas
        dates = db.query(
            distinct(func.date(Deposit.date_time)).label('date')
        ).order_by(func.date(Deposit.date_time).desc()).all()
        
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

@app.get("/api/deposits/db/summary")
def get_db_summary():
    """
    Obtiene un resumen general de la base de datos
    """
    try:
        from database import SessionLocal
        from sqlalchemy import func, distinct
        
        db = SessionLocal()
        
        # Estadísticas generales
        total_deposits = db.query(func.count(Deposit.id)).scalar()
        total_amount = db.query(func.sum(Deposit.total_amount)).scalar() or 0
        unique_machines = db.query(func.count(distinct(Deposit.identifier))).scalar()
        date_range = db.query(
            func.min(func.date(Deposit.date_time)).label('min_date'),
            func.max(func.date(Deposit.date_time)).label('max_date')
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