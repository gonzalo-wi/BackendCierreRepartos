from fastapi import APIRouter, Request

@router.post('/movimientos')
async def crear_movimiento(request: Request):
    data = await request.json()
    tipo = data.get('tipo')
    if tipo == 'CHEQUE':
        cheques = data.get('cheques', [])
        for cheque_data in cheques:
            cheque = Cheque(**cheque_data)
            # Guardar cheque en la base de datos
    elif tipo == 'RETENCION':
        retenciones = data.get('retenciones', [])
        for retencion_data in retenciones:
            retencion = Retencion(**retencion_data)
            # Guardar retención en la base de datos
    return {"ok": True}