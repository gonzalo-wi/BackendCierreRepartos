"""
Backend de Cierre de Repartos
Sistema para gestionar depósitos y sincronización con miniBank y API externa
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine

from models.deposit import Deposit, EstadoDeposito
from models.cheque_retencion import Cheque, Retencion
from models.daily_totals import DailyTotal
from models.user import User  # Importar modelo de usuario

from routers.deposits import router as deposits_router
from routers.totals import router as totals_router
from routers.pdf_reports import router as pdf_router
from routers.sync import router as sync_router
from routers.database import router as database_router
from routers.testing import router as testing_router
from routers.movimientos_financieros import router as movimientos_router
from routers.charts import router as charts_router
from routers.auth import router as auth_router  # Importar router de autenticación
from routers.reparto_cierre import router as reparto_cierre_router
from routers.debug import router as debug_router
from routers.fix_auth import router as fix_auth_router
from routers.admin_users import router as admin_users_router


app = FastAPI(
    title="Backend Cierre Repartos",
    description="Sistema para gestionar depósitos y sincronización con miniBank y API externa",
    version="1.0.0"
)

# Configurar CORS para permitir requests del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],  # Ajustar según tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

# Incluir routers
app.include_router(fix_auth_router, prefix="/api")  # Router de fix auth
app.include_router(debug_router, prefix="/api")  # Router de debug PRIMERO
app.include_router(auth_router, prefix="/api")  # Router de autenticación PRIMERO
app.include_router(admin_users_router, prefix="/api")  # Router de gestión de usuarios
app.include_router(deposits_router, prefix="/api")
app.include_router(totals_router, prefix="/api")
app.include_router(pdf_router, prefix="/api")
app.include_router(sync_router, prefix="/api")
app.include_router(database_router, prefix="/api")
app.include_router(testing_router, prefix="/api")
app.include_router(movimientos_router, prefix="/api")
app.include_router(charts_router, prefix="/api")
app.include_router(reparto_cierre_router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "message": "Backend Cierre Repartos API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/api/auth/*",
            "admin-users": "/api/admin/users/*",
            "deposits": "/api/deposits/*",
            "totals": "/api/totals/*", 
            "pdf": "/api/pdf/*",
            "sync": "/api/sync/*",
            "database": "/api/db/*",
            "testing": "/api/testing/*",
            "movimientos": "/api/movimientos/*",
            "charts": "/api/charts/*",
            "reparto-cierre": "/api/reparto-cierre/*"
        }
    }

