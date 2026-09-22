from typing import Optional, Dict, Any
from pydantic import BaseModel

class StoreSettingsUpdate(BaseModel):
    outlet_id: int = 1
    name: str
    brand_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo: Optional[str] = None
    description: Optional[str] = None

class StoreSettingsResponse(BaseModel):
    outlet_id: int
    brand_id: int
    name: str
    brand_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo: Optional[str] = None
    description: Optional[str] = None

class ReceiptSettingsUpdate(BaseModel):
    outlet_id: int = 1
    receipt_header: Optional[str] = None
    receipt_footer: Optional[str] = None
    show_logo: Optional[bool] = True
    show_wifi: Optional[bool] = True
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    tax_id: Optional[str] = None
    instagram: Optional[str] = None
    tax_enabled: Optional[bool] = True
    tax_rate: Optional[float] = 10.0
    tax_name: Optional[str] = "PB1 / Pajak Restoran"
    show_tax_on_receipt: Optional[bool] = True
    paper_width: Optional[str] = "58mm"

class ReceiptSettingsResponse(BaseModel):
    outlet_id: int
    receipt_header: str
    receipt_footer: str
    show_logo: bool
    show_wifi: bool
    wifi_ssid: str
    wifi_password: str
    tax_id: str
    instagram: str
    tax_enabled: bool = True
    tax_rate: float = 10.0
    tax_name: str = "PB1 / Pajak Restoran"
    show_tax_on_receipt: bool = True
    paper_width: str = "58mm"

class AccountProfileUpdate(BaseModel):
    employee_id: int
    name: str
    phone: Optional[str] = None
    current_pin: Optional[str] = None
    new_pin: Optional[str] = None
