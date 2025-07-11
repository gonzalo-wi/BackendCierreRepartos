
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
    deposit_id = Column(String, ForeignKey("deposits.deposit_id"), nullable=False)
    nrocta = Column(Integer)
    concepto = Column(String)
    banco = Column(String)
    sucursal = Column(String)
    localidad = Column(String)
    nro_cheque = Column(String)
    nro_cuenta = Column(Integer)
    titular = Column(String)
    fecha = Column(String)  # Podrías usar DateTime si prefieres
    importe = Column(Float)
    
    # Relación con Deposit
    deposit = relationship("Deposit", back_populates="cheques")

class Retencion(Base):
    __tablename__ = "retenciones"
    
    id = Column(Integer, primary_key=True, index=True)
    deposit_id = Column(String, ForeignKey("deposits.deposit_id"), nullable=False)
    nrocta = Column(Integer)
    concepto = Column(String)
    nro_retencion = Column(Integer)
    fecha = Column(String)  # Podrías usar DateTime si prefieres
    importe = Column(Float)
    
    # Relación con Deposit
    deposit = relationship("Deposit", back_populates="retenciones")
    