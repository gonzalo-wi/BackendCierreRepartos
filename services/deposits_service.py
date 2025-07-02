import requests
import xmltodict
import base64
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://pimsapi.minibank.com.ar/")
USER = os.getenv("API_USER")
PASSWORD = os.getenv("API_PASSWORD")

# Verificar que las credenciales estén configuradas
if not USER or not PASSWORD:
    raise ValueError("Las variables de entorno API_USER y API_PASSWORD deben estar configuradas en el archivo .env")

def get_deposits(stIdentifier: str, date: str):
    # Intentar varios formatos de fecha
    formatted_date = None
    
    # Formato MM-DD-YYYY (como en tu request: 06-28-2025)
    try:
        date_obj = datetime.strptime(date, "%m-%d-%Y")
        formatted_date = date_obj.strftime("%m/%d/%Y")
    except ValueError:
        pass
        
    # Formato YYYY-MM-DD
    if not formatted_date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%m/%d/%Y")
        except ValueError:
            pass
            
    # Formato MM/DD/YYYY
    if not formatted_date:
        try:
            date_obj = datetime.strptime(date, "%m/%d/%Y")
            formatted_date = date
        except ValueError:
            formatted_date = date
    
    url = f"{BASE_URL}wcf/PIMSWS.svc/api/v3/deposits/byday?stIdentifier={stIdentifier}&date={formatted_date}"

    auth_token = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if not response.ok:
        raise Exception(f"Error en la API externa: {response.status_code}")

    # Parsear XML a dict
    parsed = xmltodict.parse(response.content)

    return parsed  # Ya es JSON serializable
def get_deposits_for_machines(identifiers: list[str], date: str):
    results = {}
    for stIdentifier in identifiers:
        try:
            results[stIdentifier] = get_deposits(stIdentifier, date)
        except Exception as e:
            results[stIdentifier] = {"error": str(e)}
    return results

def get_jumillano_deposits(date: str):
    return get_deposits_for_machines(["L-EJU-001", "L-EJU-002"], date)

def get_plata_deposits(date: str):
    return get_deposits_for_machines(["L-EJU-003"], date)

def get_nafa_deposits(date: str):
    return get_deposits_for_machines(["L-EJU-004"], date)

def get_all_deposits(date: str):
    identifiers = ["L-EJU-001", "L-EJU-002", "L-EJU-003", "L-EJU-004"]
    return get_deposits_for_machines(identifiers, date)


def calculate_deposits_total(deposits_data):
    """
    Calcula el total de depósitos de un conjunto de máquinas
    """
    total = 0
    for maquina in deposits_data:
        if "error" not in deposits_data[maquina]:
            # Navegar por la estructura correcta de la respuesta XML convertida
            array_deposits = deposits_data[maquina].get("ArrayOfWSDepositsByDayDTO", {})
            deposits = array_deposits.get("WSDepositsByDayDTO", [])
            
            if isinstance(deposits, dict):
                deposits = [deposits]
            
            for deposit in deposits:
                # El monto está en currencies.WSDepositCurrency.totalAmount
                currencies = deposit.get("currencies", {})
                ws_deposit_currency = currencies.get("WSDepositCurrency", {})
                amount_str = ws_deposit_currency.get("totalAmount", "0")
                
                try:
                    amount = float(amount_str)
                    total += amount
                except (ValueError, TypeError):
                    continue
                    
    return total

def get_jumillano_total(date: str):
    """
    Obtiene el total de depósitos de las máquinas de Jumillano
    """
    data = get_jumillano_deposits(date)
    return calculate_deposits_total(data)

def get_plata_total(date: str):
    """
    Obtiene el total de depósitos de la máquina de La Plata
    """
    data = get_plata_deposits(date)
    return calculate_deposits_total(data)

def get_nafa_total(date: str):
    """
    Obtiene el total de depósitos de la máquina de Nafa
    """
    data = get_nafa_deposits(date)
    return calculate_deposits_total(data)

def get_all_totals(date: str):
    """
    Obtiene los totales de todas las máquinas desglosados
    """
    jumillano_total = get_jumillano_total(date)
    plata_total = get_plata_total(date)
    nafa_total = get_nafa_total(date)
    
    return {
        "date": date,
        "jumillano_total": jumillano_total,
        "plata_total": plata_total,
        "nafa_total": nafa_total,
        "grand_total": jumillano_total + plata_total + nafa_total
    }