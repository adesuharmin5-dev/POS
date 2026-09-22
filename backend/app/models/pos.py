from typing import Optional, List
from pydantic import BaseModel

class SalesTypeBase(BaseModel):
    outlet_id: int
    name: str
    is_active: bool = True

class SalesTypeResponse(SalesTypeBase):
    id: int

class ShiftOpenRequest(BaseModel):
    outlet_id: int
    employee_id: int
    initial_cash: float

class ShiftCloseRequest(BaseModel):
    actual_cash: float
    notes: Optional[str] = None

class ShiftResponse(BaseModel):
    id: int
    outlet_id: int
    employee_id: int
    employee_name: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    initial_cash: float
    expected_cash: float
    actual_cash: Optional[float] = None
    difference: Optional[float] = None
    notes: Optional[str] = None
    status: str

class CartItemModifierInput(BaseModel):
    modifier_option_id: int
    additional_price: float = 0.0

class CartItemInput(BaseModel):
    item_id: int
    quantity: int = 1
    unit_price: float
    notes: Optional[str] = None
    modifiers: Optional[List[CartItemModifierInput]] = []

class CheckoutRequest(BaseModel):
    outlet_id: int
    shift_id: Optional[int] = None
    cashier_id: Optional[int] = None
    customer_id: Optional[int] = None
    table_id: Optional[int] = None
    sales_type_id: Optional[int] = None
    discount_id: Optional[int] = None
    promo_code: Optional[str] = None
    payment_method: str = "Cash" # Cash, QRIS, Bank Transfer, GoFood
    cash_received: Optional[float] = 0.0
    items: List[CartItemInput]
    notes: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    transaction_number: str
    outlet_id: int
    cashier_name: Optional[str] = None
    table_number: Optional[str] = None
    subtotal: float
    discount_amount: float
    tax_amount: float
    gratuity_amount: float
    total_amount: float
    payment_method: str
    payment_status: str
    change_amount: Optional[float] = 0.0
    created_at: str
    invoice_number: Optional[str] = None
    items: List[dict] = []
