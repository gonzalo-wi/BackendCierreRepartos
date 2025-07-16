"""
Modelos Pydantic compartidos para requests
"""
from pydantic import BaseModel


class StatusUpdateRequest(BaseModel):
    status: str


class ExpectedAmountUpdateRequest(BaseModel):
    deposit_esperado: int
