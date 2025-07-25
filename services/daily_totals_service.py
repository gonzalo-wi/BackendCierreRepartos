from sqlalchemy.orm import Session
from database import get_db
from models.daily_totals import DailyTotal
from services.deposits_service import get_all_totals, get_all_deposits
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import random

def execute_with_retry(func, max_retries=2, base_delay=0.05):
    """
    Ejecuta una función con reintentos en caso de bloqueo de base de datos
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                # Esperar un tiempo más corto antes de reintentar
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.05)
                print(f"⚠️ Base de datos bloqueada, reintentando en {delay:.2f}s (intento {attempt + 1}/{max_retries})")
                time.sleep(delay)
                continue
            else:
                raise e
    
def save_daily_totals(date: str) -> Dict:
    """
    Guarda los totales del día especificado en la base de datos
    """
    def _save_operation():
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
    
    try:
        return execute_with_retry(_save_operation)
    except Exception as e:
        print(f"Error en save_daily_totals: {e}")
        return {"error": str(e), "date": date}

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
    Asegura que existan datos hasta la fecha especificada, consultando automáticamente solo si es necesario
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        from services.deposits_service import get_all_totals
        
        # Solo verificar la fecha específica solicitada, no un rango
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        today = datetime.now().date()
        
        # No consultar fechas futuras
        if end_date_obj.date() > today:
            return
        
        db = next(get_db())
        
        try:
            # Solo verificar si ya existe data para la fecha específica
            existing = db.query(DailyTotal).filter(
                DailyTotal.date == end_date,
                DailyTotal.plant == "total"
            ).first()
            
            if not existing:
                print(f"🔄 Consultando datos faltantes para {end_date}...")
                try:
                    # Esto disparará el guardado automático
                    get_all_totals(end_date)
                except Exception as e:
                    print(f"⚠️ Error al consultar {end_date}: {e}")
        finally:
            db.close()
        
    except Exception as e:
        print(f"⚠️ Error al verificar datos: {e}")

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
    def _save_operation():
        db = next(get_db())
        
        try:
            # Limpiar totales existentes para esta fecha
            db.query(DailyTotal).filter(DailyTotal.date == date).delete()
            
            results = {
                "date": date,
                "saved_totals": [],
                "method": "from_calculated_data"
            }
            
            # Usar los totales ya calculados en lugar de hacer nuevas consultas
            plantas_totals = {
                'jumillano': totals_data.get('jumillano_total', 0),
                'plata': totals_data.get('plata_total', 0),
                'nafa': totals_data.get('nafa_total', 0)
            }
            
            # Configuración de plantas y máquinas
            plantas_config = {
                'jumillano': ['L-EJU-001', 'L-EJU-002'],
                'plata': ['L-EJU-003'],
                'nafa': ['L-EJU-004']
            }
            
            # Guardar totales por planta (sin desglose por máquina para ser más rápido)
            total_deposits_global = 0
            for plant_name, machines in plantas_config.items():
                plant_total = plantas_totals.get(plant_name, 0)
                
                if plant_total > 0:
                    # Estimamos el número de depósitos basado en el promedio
                    estimated_deposits = max(1, int(plant_total / 1000))  # Estimación aproximada
                    
                    # Guardar total por planta
                    plant_daily_total = DailyTotal(
                        date=date,
                        plant=plant_name,
                        machine=None,  # Total por planta
                        total_amount=plant_total,
                        deposit_count=estimated_deposits
                    )
                    db.add(plant_daily_total)
                    
                    total_deposits_global += estimated_deposits
                    
                    results["saved_totals"].append({
                        "plant": plant_name,
                        "amount": plant_total,
                        "count": estimated_deposits
                    })
            
            # Guardar total general
            general_total = DailyTotal(
                date=date,
                plant="total",
                machine=None,
                total_amount=totals_data["grand_total"],
                deposit_count=total_deposits_global
            )
            db.add(general_total)
            
            db.commit()
            
            results["total_amount"] = totals_data["grand_total"]
            results["total_deposits"] = total_deposits_global
            
            return results
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    try:
        return execute_with_retry(_save_operation)
    except Exception as e:
        print(f"Error en save_daily_totals_from_data: {e}")
        return {"error": str(e), "date": date}
