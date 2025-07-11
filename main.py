import traceback
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
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
from services.repartos_api_service import actualizar_depositos_esperados

from services.pdf_service import generate_daily_closure_pdf, generate_detailed_repartos_pdf
from fastapi.responses import JSONResponse, Response
from database import Base, engine
# Importar todos los modelos para resolver relaciones SQLAlchemy
from models.deposit import Deposit, EstadoDeposito
from models.cheque_retencion import Cheque, Retencion
from routers.movimientos_financieros import router as movimientos_router


app = FastAPI()

# Incluir el router de movimientos financieros
app.include_router(movimientos_router, prefix="/api", tags=["movimientos-financieros"])

Base.metadata.create_all(bind=engine)

# Modelos Pydantic para requests
class StatusUpdateRequest(BaseModel):
    status: str

class ExpectedAmountUpdateRequest(BaseModel):
    deposit_esperado: int


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
        # Obtener datos de miniBank
        data = get_jumillano_deposits(date)
        
        # Auto-sincronizar valores esperados desde API externa
        try:
            print(f"🔄 Auto-sincronizando valores esperados para Jumillano {date}...")
            resultado_sync = actualizar_depositos_esperados(date)
            print(f"💰 Sincronización: {resultado_sync.get('actualizados', 0)} depósitos actualizados")
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            # Continuar aunque falle la sincronización
        
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/deposits/nafa")
def deposits_nafa(date: str = Query(...)):
    try:
        # Obtener datos de miniBank
        data = get_nafa_deposits(date)
        
        # Auto-sincronizar valores esperados desde API externa
        try:
            print(f"🔄 Auto-sincronizando valores esperados para Nafa {date}...")
            resultado_sync = actualizar_depositos_esperados(date)
            print(f"💰 Sincronización: {resultado_sync.get('actualizados', 0)} depósitos actualizados")
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            # Continuar aunque falle la sincronización
        
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/deposits/plata")
def deposits_plata(date: str = Query(...)):
    try:
        # Obtener datos de miniBank
        data = get_plata_deposits(date)
        
        # Auto-sincronizar valores esperados desde API externa
        try:
            print(f"🔄 Auto-sincronizando valores esperados para La Plata {date}...")
            resultado_sync = actualizar_depositos_esperados(date)
            print(f"💰 Sincronización: {resultado_sync.get('actualizados', 0)} depósitos actualizados")
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            # Continuar aunque falle la sincronización
        
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})    
    
@app.get("/api/deposits/all")
def deposits_all(date: str = Query(...)):
    try:
        # Obtener datos de miniBank
        data = get_all_deposits(date)
        
        # Auto-sincronizar valores esperados desde API externa
        try:
            print(f"🔄 Auto-sincronizando valores esperados para {date}...")
            resultado_sync = actualizar_depositos_esperados(date)
            print(f"💰 Sincronización: {resultado_sync.get('actualizados', 0)} depósitos actualizados")
        except Exception as sync_error:
            print(f"⚠️ Error en auto-sincronización de valores esperados: {sync_error}")
            # Continuar aunque falle la sincronización
        
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

@app.get("/api/test-extraction")
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
    Auto-sincroniza datos frescos de miniBank y valores esperados de la API externa
    """
    try:
        from database import SessionLocal
        from sqlalchemy import and_, func
        from datetime import datetime as dt
        
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
                "deposit_esperado": deposit.deposit_esperado,
                "diferencia": deposit.diferencia,
                "tiene_diferencia": deposit.tiene_diferencia,
                "estado": deposit.estado.value if deposit.estado else "PENDIENTE",
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
                "deposit_esperado": deposit.deposit_esperado,
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

@app.put("/api/deposits/{deposit_id}/status")
def update_deposit_status(deposit_id: str, request: StatusUpdateRequest):
    """
    Actualiza el estado de un depósito específico
    Frontend solo puede cambiar de PENDIENTE a LISTO
    """
    try:
        from database import SessionLocal
        
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

@app.put("/api/deposits/{deposit_id}/expected-amount")
def update_deposit_expected_amount(deposit_id: str, request: ExpectedAmountUpdateRequest):
    """
    Actualiza el monto esperado de un depósito y recalcula el estado automáticamente
    """
    try:
        from database import SessionLocal
        
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

@app.get("/api/deposits/states")
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

@app.put("/api/deposits/{deposit_id}/mark-sent")
def mark_deposit_as_sent(deposit_id: str):
    """
    Marca un depósito como ENVIADO (solo para uso interno del backend)
    """
    try:
        from database import SessionLocal
        
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

@app.post("/api/deposits/sync-expected-amounts")
def sync_expected_amounts(date: str = Query(...)):
    """
    Sincroniza los montos esperados desde la API externa de repartos
    """
    try:
        print(f"🔄 Iniciando sincronización de montos esperados para fecha: {date}")
        
        resultado = actualizar_depositos_esperados(date)
        
        if resultado["status"] == "error":
            raise HTTPException(status_code=500, detail=resultado["message"])
        
        print(f"✅ Sincronización completada: {resultado['actualizados']} depósitos actualizados")
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en sincronización de montos esperados: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deposits/test-external-api")
def test_external_api(date: str = Query(...)):
    """
    Endpoint de prueba para verificar la conexión con la API externa
    """
    try:
        from services.repartos_api_service import get_repartos_valores
        from datetime import datetime as dt
        
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