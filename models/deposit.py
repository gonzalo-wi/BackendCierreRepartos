from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.types import TypeDecorator, String as SQLString
from sqlalchemy.orm import relationship
from database import Base
import enum

TOLERANCE_DIFFERENCE = 10000

class EstadoDeposito(enum.Enum):
    PENDIENTE = "PENDIENTE"
    LISTO     = "LISTO"
    ENVIADO   = "ENVIADO"

class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True, index=True)
    deposit_id       = Column(String(255), unique=True, index=True)
    identifier       = Column(String(255))
    user_name        = Column(String(255))
    total_amount     = Column(Integer)
    deposit_esperado = Column(Integer, nullable=True)  # Total suma (Efectivo + Retenciones + Cheques)
    efectivo_esperado = Column(Integer, nullable=True)  # Solo efectivo para cierre
    composicion_esperado = Column(String(50), nullable=True)  # Composición E/C/R
    currency_code    = Column(String(10))
    deposit_type     = Column(String(100))
    date_time        = Column(DateTime)
    pos_name         = Column(String(255))
    st_name          = Column(String(255))
    estado           = Column(Enum(EstadoDeposito), default=EstadoDeposito.LISTO)
    fecha_envio      = Column(DateTime, nullable=True)  # Fecha cuando se envió el reparto

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
        """Actualiza el estado: PENDIENTE si tiene cheques o retenciones, LISTO si no tiene ninguno"""
        tiene_cheques = hasattr(self, 'cheques') and self.cheques and len(self.cheques) > 0
        tiene_retenciones = hasattr(self, 'retenciones') and self.retenciones and len(self.retenciones) > 0
        if tiene_cheques or tiene_retenciones:
            self.estado = EstadoDeposito.PENDIENTE
        else:
            self.estado = EstadoDeposito.LISTO