from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

class DailyTotal(Base):
    __tablename__ = "daily_totals"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)  # Formato YYYY-MM-DD
    plant = Column(String, nullable=False)  # 'jumillano', 'plata', 'nafa', 'total'
    machine = Column(String, nullable=True)  # L-EJU-001, L-EJU-002, etc. (null para totales por planta)
    total_amount = Column(Float, default=0.0)
    deposit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Evitar duplicados por fecha, planta y máquina
    __table_args__ = (
        UniqueConstraint('date', 'plant', 'machine', name='_date_plant_machine_uc'),
    )

    def __repr__(self):
        return f"<DailyTotal(date={self.date}, plant={self.plant}, machine={self.machine}, amount={self.total_amount})>"
