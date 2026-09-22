from typing import Optional
from pydantic import BaseModel

class TaxBase(BaseModel):
    outlet_id: int
    name: str
    rate_percent: float
    is_inclusive: bool = False
    is_active: bool = True

class TaxResponse(TaxBase):
    id: int

class GratuityBase(BaseModel):
    outlet_id: int
    name: str
    rate_percent: float
    is_active: bool = True

class GratuityResponse(GratuityBase):
    id: int

class BankAccountBase(BaseModel):
    outlet_id: int
    bank_name: str
    account_number: str
    account_holder: str
    is_active: bool = True

class BankAccountResponse(BankAccountBase):
    id: int

class QRISConfigBase(BaseModel):
    outlet_id: int
    merchant_name: str
    merchant_id: str
    nmid: str
    api_key: Optional[str] = None
    is_active: bool = True

class QRISConfigResponse(QRISConfigBase):
    id: int

class QRISGenerateRequest(BaseModel):
    outlet_id: int
    transaction_id: Optional[int] = None
    amount: float

class QRISResponse(BaseModel):
    id: int
    transaction_reference: str
    qr_string: str
    amount: float
    status: str
    expiry_time: Optional[str] = None
