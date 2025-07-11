# __init__.py para models
# Importar todos los modelos para que SQLAlchemy pueda resolver las relaciones

from .deposit import Deposit, EstadoDeposito
from .cheque_retencion import Cheque, Retencion, TipoConcepto

# Exportar todos los modelos
__all__ = ['Deposit', 'EstadoDeposito', 'Cheque', 'Retencion', 'TipoConcepto']
