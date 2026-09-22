from typing import Optional
from pydantic import BaseModel

class CustomerBase(BaseModel):
    brand_id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    loyalty_points: int = 0
    total_spent: float = 0.0
    created_at: str

class DiscountBase(BaseModel):
    brand_id: int
    name: str
    discount_type: str # percentage, fixed
    value: float
    min_order_amount: float = 0.0
    is_active: bool = True

class DiscountResponse(DiscountBase):
    id: int

class PromoBase(BaseModel):
    brand_id: int
    name: str
    promo_code: str
    discount_type: str # percentage, fixed
    discount_value: float
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    quota: int = 100
    used_count: int = 0
    is_active: bool = True

class PromoResponse(PromoBase):
    id: int

class CampaignBase(BaseModel):
    brand_id: int
    name: str
    target_audience: Optional[str] = None
    message: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "active"

class CampaignResponse(CampaignBase):
    id: int
