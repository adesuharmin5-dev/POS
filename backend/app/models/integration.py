from typing import Optional, List, Any
from pydantic import BaseModel

class MobileOrderCreate(BaseModel):
    outlet_id: int
    table_id: Optional[int] = None
    customer_name: str
    customer_phone: Optional[str] = None
    items: List[dict] # list of items ordered
    total_amount: float

class MobileOrderResponse(BaseModel):
    id: int
    outlet_id: int
    table_id: Optional[int] = None
    customer_name: str
    customer_phone: Optional[str] = None
    items_json: str
    total_amount: float
    status: str
    created_at: str

class GoFoodConfig(BaseModel):
    outlet_id: int
    store_id: str
    is_integrated: bool = True
    auto_accept_order: bool = True

class PartnerResponse(BaseModel):
    id: int
    brand_id: int
    partner_name: str
    partner_type: str
    status: str

class SyncPushRequest(BaseModel):
    outlet_id: int
    entity_name: str
    action: str
    entity_id: int
    payload: dict

class SyncPullResponse(BaseModel):
    total_synced: int
    latest_sync_timestamp: str
    items: List[dict]
