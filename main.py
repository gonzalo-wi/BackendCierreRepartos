"""
Backend de Cierre de Repartos
Sistema para gestionar depósitos y sincronización con miniBank y API externa
"""
from fastapi import FastAPI
from database import Base, engine

from models.deposit import Deposit, EstadoDeposito
from models.cheque_retencion import Cheque, Retencion
from models.daily_totals import DailyTotal


from routers.deposits import router as deposits_router
from routers.totals import router as totals_router
from routers.pdf_reports import router as pdf_router
from routers.sync import router as sync_router
from routers.database import router as database_router
from routers.testing import router as testing_router
from routers.movimientos_financieros import router as movimientos_router
from routers.charts import router as charts_router


app = FastAPI(
    title="Backend Cierre Repartos",
    description="Sistema para gestionar depósitos y sincronización con miniBank y API externa",
    version="1.0.0"
)


Base.metadata.create_all(bind=engine)


app.include_router(deposits_router, prefix="/api")
app.include_router(totals_router, prefix="/api")
app.include_router(pdf_router, prefix="/api")
app.include_router(sync_router, prefix="/api")
app.include_router(database_router, prefix="/api")
app.include_router(testing_router, prefix="/api")
app.include_router(movimientos_router, prefix="/api")
app.include_router(charts_router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "message": "Backend Cierre Repartos API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "deposits": "/api/deposits/*",
            "totals": "/api/totals/*", 
            "pdf": "/api/pdf/*",
            "sync": "/api/sync/*",
            "database": "/api/db/*",
            "testing": "/api/test/*",
            "movimientos": "/api/movimientos-financieros/*",
            "charts": "/api/charts/*"
        }
    }

