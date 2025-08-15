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
    deposit_esperado = Column(Integer, nullable=True)  # Nuevo campo
    composicion_esperado = Column(String(50), nullable=True)  # Composición E/C/R
    currency_code    = Column(String(10))
    deposit_type     = Column(String(100))
    date_time        = Column(DateTime)
    pos_name         = Column(String(255))
    st_name          = Column(String(255))
    estado           = Column(Enum(EstadoDeposito), default=EstadoDeposito.PENDIENTE)
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
        """Actualiza el estado basado en la diferencia"""
        if self.deposit_esperado is None or self.deposit_esperado == 0:
            self.estado = EstadoDeposito.PENDIENTE
        else:
            # Diferencia = monto_real - monto_esperado
            # Positivo = sobra dinero, Negativo = falta dinero
            diferencia = self.total_amount - self.deposit_esperado
            
            # Si falta dinero (diferencia negativa) y el faltante es >= 10000
            if diferencia < 0 and abs(diferencia) >= TOLERANCE_DIFFERENCE:
                self.estado = EstadoDeposito.PENDIENTE
            else:
                # En todos los demás casos está LISTO:
                # - Si sobra dinero (cualquier cantidad)
                # - Si falta dinero pero menos de 10000
                # - Si está exacto (diferencia = 0)
                self.estado = EstadoDeposito.LISTO