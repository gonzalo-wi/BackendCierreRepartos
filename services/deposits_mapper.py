def map_deposit_to_reparto(deposit: dict) -> dict:
    return {
        "fechaReparto": deposit.get("dateTime"),
        "depositoEsperado": None,
        "depositoReal": float(deposit.get("currencies", {}).get("WSDepositCurrency", {}).get("totalAmount", 0)),
        "idReparto": deposit.get("depositId") or deposit.get("userName"),
        "movimientoFinanciero": None
    }