from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True, index=True)
    deposit_id = Column(String, unique=True, index=True)
    identifier = Column(String)
    user_name = Column(String)
    total_amount = Column(Integer)
    currency_code = Column(String)
    deposit_type = Column(String)
    date_time = Column(DateTime)
    pos_name = Column(String)
    st_name = Column(String)