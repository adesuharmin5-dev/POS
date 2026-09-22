from typing import Optional
from pydantic import BaseModel

class TableGroupBase(BaseModel):
    outlet_id: int
    name: str
    description: Optional[str] = None

class TableGroupResponse(TableGroupBase):
    id: int

class TableBase(BaseModel):
    group_id: Optional[int] = None
    outlet_id: int
    table_number: str
    capacity: int = 4
    pos_x: float = 0.0
    pos_y: float = 0.0
    status: str = "available" # available, occupied, reserved

class TableCreate(TableBase):
    pass

class TableUpdateLayout(BaseModel):
    pos_x: float
    pos_y: float

class TableStatusUpdate(BaseModel):
    status: str # available, occupied, reserved
    current_transaction_id: Optional[int] = None

class TableResponse(TableBase):
    id: int
    group_name: Optional[str] = None
    current_transaction_id: Optional[int] = None
