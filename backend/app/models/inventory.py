from typing import Optional, List
from pydantic import BaseModel

class IngredientCategoryBase(BaseModel):
    brand_id: int
    name: str
    description: Optional[str] = None

class IngredientCategoryResponse(IngredientCategoryBase):
    id: int

class IngredientBase(BaseModel):
    category_id: Optional[int] = None
    name: str
    unit: str
    cost_per_unit: float = 0.0
    min_stock_alert: float = 10.0
    is_active: bool = True

class IngredientCreate(IngredientBase):
    initial_stock_outlet_id: Optional[int] = None
    initial_stock: Optional[float] = 0.0

class IngredientResponse(IngredientBase):
    id: int
    category_name: Optional[str] = None
    current_stock: Optional[float] = 0.0

class RecipeItemInput(BaseModel):
    ingredient_id: int
    quantity_used: float
    unit: str

class RecipeCreate(BaseModel):
    item_id: int
    recipes: List[RecipeItemInput]

class RecipeResponse(BaseModel):
    id: int
    item_id: int
    ingredient_id: int
    ingredient_name: str
    quantity_used: float
    unit: str

class SupplierBase(BaseModel):
    brand_id: int
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True

class SupplierResponse(SupplierBase):
    id: int

class POItemInput(BaseModel):
    ingredient_id: int
    quantity: float
    unit_price: float

class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    outlet_id: int
    order_date: str
    expected_date: Optional[str] = None
    notes: Optional[str] = None
    items: List[POItemInput]

class PurchaseOrderResponse(BaseModel):
    id: int
    po_number: str
    supplier_id: int
    supplier_name: Optional[str] = None
    outlet_id: int
    order_date: str
    expected_date: Optional[str] = None
    status: str
    total_amount: float
    notes: Optional[str] = None
    items: List[dict] = []

class StockAdjustmentItemInput(BaseModel):
    ingredient_id: int
    actual_stock: float

class StockAdjustmentCreate(BaseModel):
    outlet_id: int
    reason: str
    adjusted_by: str
    items: List[StockAdjustmentItemInput]

class StockTransferItemInput(BaseModel):
    ingredient_id: int
    quantity: float

class StockTransferCreate(BaseModel):
    source_outlet_id: int
    target_outlet_id: int
    notes: Optional[str] = None
    items: List[StockTransferItemInput]
