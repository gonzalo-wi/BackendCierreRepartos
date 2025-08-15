
import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from database import Base

class TipoConcepto(enum.Enum):
    RIB = "RIB"
    CHE = "CHE"

class Cheque(Base):
    __tablename__ = "cheques"
    
    id = Column(Integer, primary_key=True, index=True)
    deposit_id = Column(String(255), ForeignKey("deposits.deposit_id"), nullable=False)  # Usar deposit_id string como estaba
    nrocta = Column(BigInteger, default=1)  # Cambiado a BigInteger para soportar números grandes
    concepto = Column(String(50), default="CHE")
    banco = Column(String(255))
    sucursal = Column(String(50), default="001")
    localidad = Column(String(100), default="1234")
    nro_cheque = Column(String(100))  # Este será el "numero" del frontend
    nro_cuenta = Column(Integer, default=1234)
    titular = Column(String(255), default="")
    fecha = Column(String(50))  # Este será la "fecha_cobro" del frontend - aumentado para timestamps
    importe = Column(Float)
    
    # Relación con Deposit
    deposit = relationship("Deposit", back_populates="cheques")

class Retencion(Base):
    __tablename__ = "retenciones"
    
    id = Column(Integer, primary_key=True, index=True)
    deposit_id = Column(String(255), ForeignKey("deposits.deposit_id"), nullable=False)  # Usar deposit_id string como estaba
    nrocta = Column(BigInteger, default=1)  # Cambiado a BigInteger para soportar números grandes
    concepto = Column(String(50), default="RIB")
    nro_retencion = Column(String(100))  # Este será el "numero" del frontend
    fecha = Column(String(50))  # Fecha de la retención - aumentado para timestamps completos
    importe = Column(Float)
    tipo = Column(String(50))  # Campo adicional para el frontend (tipo de retención)
    
    # Relación con Deposit
    deposit = relationship("Deposit", back_populates="retenciones")
    