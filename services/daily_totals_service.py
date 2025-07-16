from sqlalchemy.orm import Session
from database import get_db
from models.daily_totals import DailyTotal
from services.deposits_service import get_all_totals, get_all_deposits
from datetime import datetime, timedelta
from typing import List, Dict, Optional

def save_daily_totals(date: str) -> Dict:
    """
    Guarda los totales del día especificado en la base de datos
    """
    db = next(get_db())
    
    try:
        # Obtener los totales del día
        totals_data = get_all_totals(date)
        
        # Limpiar totales existentes para esta fecha
        db.query(DailyTotal).filter(DailyTotal.date == date).delete()
        
        results = {
            "date": date,
            "saved_totals": [],
            "errors": []
        }
        
        # Procesar datos por planta
        plantas_config = {
            'jumillano': ['L-EJU-001', 'L-EJU-002'],
            'plata': ['L-EJU-003'],
            'nafa': ['L-EJU-004']
        }
        
        total_general = 0.0
        total_deposits = 0
        
        for plant_name, machines in plantas_config.items():
            plant_total = 0.0
            plant_deposits = 0
            
            # Guardar totales por máquina
            for machine in machines:
                if machine in totals_data and "error" not in totals_data[machine]:
                    machine_data = totals_data[machine]
                    amount = float(machine_data.get("total", 0))
                    count = int(machine_data.get("count", 0))
                    
                    # Guardar total por máquina
                    daily_total = DailyTotal(
                        date=date,
                        plant=plant_name,
                        machine=machine,
                        total_amount=amount,
                        deposit_count=count
                    )
                    db.add(daily_total)
                    
                    plant_total += amount
                    plant_deposits += count
                    
                    results["saved_totals"].append({
                        "plant": plant_name,
                        "machine": machine,
                        "amount": amount,
                        "count": count
                    })
                else:
                    results["errors"].append(f"No data for machine {machine}")
            
            # Guardar total por planta
            if plant_total > 0:
                plant_daily_total = DailyTotal(
                    date=date,
                    plant=plant_name,
                    machine=None,  # Total por planta
                    total_amount=plant_total,
                    deposit_count=plant_deposits
                )
                db.add(plant_daily_total)
                
                total_general += plant_total
                total_deposits += plant_deposits
        
        # Guardar total general
        general_total = DailyTotal(
            date=date,
            plant="total",
            machine=None,
            total_amount=total_general,
            deposit_count=total_deposits
        )
        db.add(general_total)
        
        db.commit()
        
        results["total_amount"] = total_general
        results["total_deposits"] = total_deposits
        
        return results
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_daily_totals_by_period(start_date: str, end_date: str, plant: Optional[str] = None) -> List[Dict]:
    """
    Obtiene los totales diarios para un período específico, consultando automáticamente datos faltantes
    """
    # Asegurar que los datos recientes existan
    ensure_recent_data_exists(end_date)
    
    db = next(get_db())
    
    try:
        query = db.query(DailyTotal).filter(
            DailyTotal.date >= start_date,
            DailyTotal.date <= end_date,
            DailyTotal.machine.is_(None)  # Solo totales por planta/general
        )
        
        if plant:
            query = query.filter(DailyTotal.plant == plant)
            
        totals = query.order_by(DailyTotal.date, DailyTotal.plant).all()
        
        result = []
        for total in totals:
            result.append({
                "date": total.date,
                "plant": total.plant,
                "total_amount": total.total_amount,
                "deposit_count": total.deposit_count,
                "created_at": total.created_at.isoformat() if total.created_at else None
            })
            
        return result
        
    finally:
        db.close()

def ensure_recent_data_exists(end_date: str = None) -> None:
    """
    Asegura que existan datos hasta la fecha especificada, consultando automáticamente si faltan
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        from services.deposits_service import get_all_totals
        
        # Verificar qué fechas faltan en los últimos 7 días, pero no fechas futuras
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        today = datetime.now().date()
        
        # No consultar fechas futuras
        if end_date_obj.date() > today:
            end_date_obj = datetime.combine(today, datetime.min.time())
            end_date = end_date_obj.strftime("%Y-%m-%d")
        
        start_date_obj = end_date_obj - timedelta(days=7)
        
        db = next(get_db())
        
        for i in range(8):  # Últimos 7 días + hoy
            check_date = start_date_obj + timedelta(days=i)
            check_date_str = check_date.strftime("%Y-%m-%d")
            
            # Solo verificar fechas que no sean futuras
            if check_date.date() > today:
                continue
            
            # Verificar si ya existe data para esta fecha
            existing = db.query(DailyTotal).filter(
                DailyTotal.date == check_date_str,
                DailyTotal.plant == "total"
            ).first()
            
            if not existing and check_date <= end_date_obj:
                print(f"🔄 Consultando automáticamente datos faltantes para {check_date_str}...")
                try:
                    # Esto disparará el guardado automático
                    get_all_totals(check_date_str)
                except Exception as e:
                    print(f"⚠️ Error al consultar {check_date_str}: {e}")
        
        db.close()
        
    except Exception as e:
        print(f"⚠️ Error al verificar datos recientes: {e}")

def get_monthly_chart_data(year: int, month: int, plant: Optional[str] = None) -> Dict:
    """
    Obtiene datos para gráficos mensuales, asegurando que los datos recientes estén disponibles
    """
    # Asegurar que los datos recientes existan
    ensure_recent_data_exists()
    
    # Calcular primer y último día del mes
    start_date = f"{year}-{month:02d}-01"
    
    # Último día del mes
    if month == 12:
        next_month = f"{year + 1}-01-01"
    else:
        next_month = f"{year}-{month + 1:02d}-01"
    
    next_month_date = datetime.strptime(next_month, "%Y-%m-%d")
    last_day = (next_month_date - timedelta(days=1)).strftime("%Y-%m-%d")
    
    totals = get_daily_totals_by_period(start_date, last_day, plant)
    
    # Organizar datos por fecha
    chart_data = {
        "labels": [],  # Fechas
        "datasets": []
    }
    
    if plant and plant != "total":
        # Datos para una planta específica
        amounts = []
        counts = []
        
        for total in totals:
            if total["plant"] == plant:
                chart_data["labels"].append(total["date"])
                amounts.append(total["total_amount"])
                counts.append(total["deposit_count"])
        
        chart_data["datasets"] = [
            {
                "label": f"Ventas {plant.title()}",
                "data": amounts,
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 2
            }
        ]
    else:
        # Datos comparativos por planta
        plantas_data = {}
        dates = set()
        
        for total in totals:
            if total["plant"] != "total":
                plant_name = total["plant"]
                date = total["date"]
                
                if plant_name not in plantas_data:
                    plantas_data[plant_name] = {}
                
                plantas_data[plant_name][date] = total["total_amount"]
                dates.add(date)
        
        chart_data["labels"] = sorted(list(dates))
        
        colors = {
            "jumillano": {"bg": "rgba(255, 99, 132, 0.2)", "border": "rgba(255, 99, 132, 1)"},
            "plata": {"bg": "rgba(54, 162, 235, 0.2)", "border": "rgba(54, 162, 235, 1)"},
            "nafa": {"bg": "rgba(255, 205, 86, 0.2)", "border": "rgba(255, 205, 86, 1)"}
        }
        
        for plant_name, plant_totals in plantas_data.items():
            amounts = []
            for date in chart_data["labels"]:
                amounts.append(plant_totals.get(date, 0))
            
            chart_data["datasets"].append({
                "label": plant_name.title(),
                "data": amounts,
                "backgroundColor": colors.get(plant_name, {}).get("bg", "rgba(128, 128, 128, 0.2)"),
                "borderColor": colors.get(plant_name, {}).get("border", "rgba(128, 128, 128, 1)"),
                "borderWidth": 2
            })
    
    return chart_data

def auto_save_today_totals() -> Dict:
    """
    Guarda automáticamente los totales del día actual
    """
    today = datetime.now().strftime("%Y-%m-%d")
    return save_daily_totals(today)

def save_daily_totals_from_data(date: str, totals_data: Dict) -> Dict:
    """
    Guarda los totales del día a partir de datos ya calculados (más eficiente)
    """
    db = next(get_db())
    
    try:
        # Limpiar totales existentes para esta fecha
        db.query(DailyTotal).filter(DailyTotal.date == date).delete()
        
        results = {
            "date": date,
            "saved_totals": [],
            "method": "from_calculated_data"
        }
        
        # Obtener datos detallados por máquina para contar depósitos
        detailed_data = get_all_deposits(date)
        
        # Configuración de plantas y máquinas
        plantas_config = {
            'jumillano': ['L-EJU-001', 'L-EJU-002'],
            'plata': ['L-EJU-003'],
            'nafa': ['L-EJU-004']
        }
        
        # Guardar totales por máquina y planta
        for plant_name, machines in plantas_config.items():
            plant_total = 0.0
            plant_deposits = 0
            
            # Guardar totales por máquina
            for machine in machines:
                if machine in detailed_data and "error" not in detailed_data[machine]:
                    machine_data = detailed_data[machine]
                    array_deposits = machine_data.get("ArrayOfWSDepositsByDayDTO", {})
                    deposits = array_deposits.get("WSDepositsByDayDTO", [])
                    
                    if isinstance(deposits, dict):
                        deposits = [deposits]
                    
                    # Calcular total y contar depósitos para esta máquina
                    machine_total = 0.0
                    machine_count = len(deposits) if deposits else 0
                    
                    for deposit in deposits:
                        currencies = deposit.get("currencies", {})
                        ws_deposit_currencies = currencies.get("WSDepositCurrency", [])
                        
                        if isinstance(ws_deposit_currencies, dict):
                            ws_deposit_currencies = [ws_deposit_currencies]
                        
                        for currency in ws_deposit_currencies:
                            try:
                                amount = float(currency.get("totalAmount", "0"))
                                machine_total += amount
                            except (ValueError, TypeError):
                                continue
                    
                    # Guardar total por máquina
                    daily_total = DailyTotal(
                        date=date,
                        plant=plant_name,
                        machine=machine,
                        total_amount=machine_total,
                        deposit_count=machine_count
                    )
                    db.add(daily_total)
                    
                    plant_total += machine_total
                    plant_deposits += machine_count
                    
                    results["saved_totals"].append({
                        "plant": plant_name,
                        "machine": machine,
                        "amount": machine_total,
                        "count": machine_count
                    })
            
            # Guardar total por planta
            if plant_total > 0:
                plant_daily_total = DailyTotal(
                    date=date,
                    plant=plant_name,
                    machine=None,  # Total por planta
                    total_amount=plant_total,
                    deposit_count=plant_deposits
                )
                db.add(plant_daily_total)
        
        # Guardar total general
        general_total = DailyTotal(
            date=date,
            plant="total",
            machine=None,
            total_amount=totals_data["grand_total"],
            deposit_count=sum(t["count"] for t in results["saved_totals"])
        )
        db.add(general_total)
        
        db.commit()
        
        results["total_amount"] = totals_data["grand_total"]
        results["total_deposits"] = sum(t["count"] for t in results["saved_totals"])
        
        return results
        
    except Exception as e:
        db.rollback()
        print(f"Error en save_daily_totals_from_data: {e}")
        return {"error": str(e), "date": date}
    finally:
        db.close()
