"""
Backend de Cierre de Repartos
Sistema para gestionar depósitos y sincronización con miniBank y API externa
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine

# Importar configuración de logging
from config.logging_config import setup_application_logging
from middleware.logging_middleware import setup_request_logging

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
from routers.production_control import router as production_control_router
from routers.cheques_retenciones import router as cheques_retenciones_router


app = FastAPI(
    title="Backend Cierre Repartos",
    description="Sistema para gestionar depósitos y sincronización con miniBank y API externa",
    version="1.0.0"
)

# ========== CONFIGURACIÓN DE LOGGING ==========
# Inicializar sistema de logging ANTES que todo lo demás
setup_application_logging()

# Configurar middleware de logging para requests HTTP
setup_request_logging(app)

# ========== CONFIGURACIÓN DE CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],  # Ajustar según tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== CONFIGURACIÓN DE BASE DE DATOS ==========
Base.metadata.create_all(bind=engine)

# ========== CONFIGURACIÓN DE ROUTERS ==========
app.include_router(fix_auth_router, prefix="/api")  # Router de fix auth
app.include_router(debug_router, prefix="/api")  # Router de debug PRIMERO
app.include_router(auth_router, prefix="/api")  # Router de autenticación PRIMERO
app.include_router(admin_users_router, prefix="/api")  # Router de gestión de usuarios
app.include_router(production_control_router, prefix="/api")  # Control de producción
app.include_router(deposits_router, prefix="/api")
app.include_router(totals_router, prefix="/api")
app.include_router(pdf_router, prefix="/api")
app.include_router(sync_router, prefix="/api")
app.include_router(database_router, prefix="/api")
app.include_router(testing_router, prefix="/api")
app.include_router(movimientos_router, prefix="/api")
app.include_router(charts_router, prefix="/api")
app.include_router(reparto_cierre_router, prefix="/api")
app.include_router(cheques_retenciones_router, prefix="/api")

# ========== ENDPOINT RAÍZ ==========
@app.get("/")
def read_root():
    # Importar aquí para evitar import circular
    from utils.logging_utils import log_user_action
    import logging
    
    # Log de acceso al endpoint raíz
    app_logger = logging.getLogger('app')
    app_logger.info("Acceso al endpoint raíz de la aplicación")
    
    return {
        "message": "Backend Cierre Repartos API",
        "version": "1.0.0",
        "status": "running",
        "logging": "enabled",
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

