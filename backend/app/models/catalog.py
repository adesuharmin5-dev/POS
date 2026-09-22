from typing import Optional, List
from pydantic import BaseModel

class CategoryBase(BaseModel):
    brand_id: int
    name: str
    description: Optional[str] = None
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    id: int

class ModifierOptionBase(BaseModel):
    name: str
    additional_price: float = 0.0

class ModifierOptionInput(ModifierOptionBase):
    id: Optional[int] = None

class ModifierOptionCreate(ModifierOptionBase):
    pass

class ModifierOptionResponse(ModifierOptionBase):
    id: int
    modifier_id: int

class ModifierBase(BaseModel):
    brand_id: int = 1
    name: str
    min_selection: int = 0
    max_selection: int = 1
    is_active: bool = True

class ModifierCreate(ModifierBase):
    options: List[ModifierOptionInput] = []

class ModifierUpdate(BaseModel):
    name: Optional[str] = None
    min_selection: Optional[int] = None
    max_selection: Optional[int] = None
    is_active: Optional[bool] = None
    options: Optional[List[ModifierOptionInput]] = None

class ModifierResponse(ModifierBase):
    id: int
    options: List[ModifierOptionResponse] = []

class ItemBase(BaseModel):
    category_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    price: float
    cost_price: float = 0.0
    image_url: Optional[str] = None
    is_active: bool = True

class ItemCreate(ItemBase):
    modifier_ids: Optional[List[int]] = []

class ItemUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    modifier_ids: Optional[List[int]] = None

class PriceUpdate(BaseModel):
    price: float
    cost_price: Optional[float] = None

class ItemResponse(ItemBase):
    id: int
    category_name: Optional[str] = None
    modifiers: Optional[List[ModifierResponse]] = []

class BundleItemInput(BaseModel):
    item_id: int
    quantity: int = 1

class BundlePackageCreate(BaseModel):
    brand_id: int
    name: str
    price: float
    description: Optional[str] = None
    items: List[BundleItemInput] = []

class BundlePackageResponse(BaseModel):
    id: int
    brand_id: int
    name: str
    price: float
    description: Optional[str] = None
    is_active: bool = True
    items: List[dict] = []
