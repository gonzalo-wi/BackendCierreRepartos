
import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class TipoConcepto(enum.Enum):
    RIB = "RIB"
    CHE = "CHE"

class Cheque(Base):
    __tablename__ = "cheques"
    
    id = Column(Integer, primary_key=True, index=True)
    deposit_id = Column(String, ForeignKey("deposits.deposit_id"), nullable=False)  # Usar deposit_id string como estaba
    nrocta = Column(Integer, default=1)
    concepto = Column(String, default="CHE")
    banco = Column(String)
    sucursal = Column(String, default="001")
    localidad = Column(String, default="1234")
    nro_cheque = Column(String)  # Este será el "numero" del frontend
    nro_cuenta = Column(Integer, default=1234)
    titular = Column(String, default="")
    fecha = Column(String)  # Este será la "fecha_cobro" del frontend
    importe = Column(Float)
    
    # Relación con Deposit
    deposit = relationship("Deposit", back_populates="cheques")

class Retencion(Base):
    __tablename__ = "retenciones"
    
    id = Column(Integer, primary_key=True, index=True)
    deposit_id = Column(String, ForeignKey("deposits.deposit_id"), nullable=False)  # Usar deposit_id string como estaba
    nrocta = Column(Integer, default=1)
    concepto = Column(String, default="RIB")
    nro_retencion = Column(String)  # Este será el "numero" del frontend
    fecha = Column(String)  # Fecha de la retención
    importe = Column(Float)
    tipo = Column(String)  # Campo adicional para el frontend (tipo de retención)
    
    # Relación con Deposit
    deposit = relationship("Deposit", back_populates="retenciones")
    