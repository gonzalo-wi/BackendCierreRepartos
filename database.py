from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import quote_plus

# Configuración de base de datos
DB_TYPE = os.getenv("DB_TYPE", "sqlserver")  # Default a sqlserver para producción

if DB_TYPE == "sqlserver":
    # Configuración para SQL Server en producción
    SERVER = "192.168.0.234"
    DATABASE = "PAC"
    USERNAME = "h2o"
    PASSWORD = "Jumi1234"
    PORT = 1433
    
    # Connection string para SQL Server con pymssql (no requiere ODBC drivers)
    connection_url = f"mssql+pymssql://{USERNAME}:{PASSWORD}@{SERVER}:{PORT}/{DATABASE}"
    SQLALCHEMY_DATABASE_URL = connection_url
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,  # Verificar conexión antes de usar
        pool_recycle=300,  # Reciclar conexiones cada 5 minutos
        connect_args={
            "timeout": 30,  # Timeout de conexión
            "autocommit": False
        }
    )
else:
    # Configuración para SQLite (desarrollo)
    SQLALCHEMY_DATABASE_URL = "sqlite:///./deposits.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()