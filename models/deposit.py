from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.types import TypeDecorator, String as SQLString
from sqlalchemy.orm import relationship
from database import Base
import enum

TOLERANCE_DIFFERENCE = 0.05

class EstadoDeposito(enum.Enum):
    PENDIENTE = "PENDIENTE"
    LISTO     = "LISTO"
    ENVIADO   = "ENVIADO"

class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True, index=True)
    deposit_id       = Column(String, unique=True, index=True)
    identifier       = Column(String)
    user_name        = Column(String)
    total_amount     = Column(Integer)
    deposit_esperado = Column(Integer, nullable=True)  # Nuevo campo
    composicion_esperado = Column(String, nullable=True)  # Composición E/C/R
    currency_code    = Column(String)
    deposit_type     = Column(String)
    date_time        = Column(DateTime)
    pos_name         = Column(String)
    st_name          = Column(String)
    estado           = Column(Enum(EstadoDeposito), default=EstadoDeposito.PENDIENTE)

    # Relaciones con cheques y retenciones
    cheques = relationship("Cheque", back_populates="deposit", cascade="all, delete-orphan")
    retenciones = relationship("Retencion", back_populates="deposit", cascade="all, delete-orphan")

    @property
    def tiene_diferencia(self):
        """Verifica si hay diferencia entre monto esperado y real"""
        if self.deposit_esperado is None:
            return False
        return self.total_amount != self.deposit_esperado
    
    @property
    def diferencia(self):
        """Calcula la diferencia entre monto real y esperado"""
        if self.deposit_esperado is None:
            return 0
        return self.total_amount - self.deposit_esperado
    
    
    def actualizar_estado(self):
        """Actualiza el estado basado en la diferencia"""
        if self.deposit_esperado is None or self.deposit_esperado == 0:
            self.estado = EstadoDeposito.PENDIENTE
        else:
            diferencia = abs(self.total_amount - self.deposit_esperado)
            porcentaje = diferencia / self.deposit_esperado
        if porcentaje <= TOLERANCE_DIFFERENCE:
            self.estado = EstadoDeposito.LISTO
        else:
            self.estado = EstadoDeposito.PENDIENTE