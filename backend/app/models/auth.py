from typing import Optional, List
from pydantic import BaseModel

class BrandBase(BaseModel):
    name: str
    logo: Optional[str] = None
    description: Optional[str] = None

class BrandResponse(BrandBase):
    id: int
    created_at: str

class OutletBase(BaseModel):
    brand_id: int
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True

class OutletCreate(OutletBase):
    pass

class OutletResponse(OutletBase):
    id: int
    created_at: str

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[str] = None

class RoleResponse(RoleBase):
    id: int
    employee_count: Optional[int] = 0

class EmployeeCreate(BaseModel):
    outlet_id: int = 1
    user_id: Optional[int] = None
    name: str
    pin: str
    role_id: Optional[int] = None
    phone: Optional[str] = None
    is_active: bool = True

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    pin: Optional[str] = None
    role_id: Optional[int] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class EmployeeResponse(BaseModel):
    id: int
    outlet_id: int
    name: str
    pin: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool

class EmployeePinVerify(BaseModel):
    outlet_id: Optional[int] = 1
    pin: str
    employee_id: Optional[int] = None

class BillingPlanResponse(BaseModel):
    id: int
    brand_id: int
    plan_name: str
    status: str
    billing_cycle: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    price: float

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserAccountInfo(BaseModel):
    id: int
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    role_id: Optional[int] = None
    brand_id: Optional[int] = None

class UserLoginResponse(BaseModel):
    success: bool
    token: str
    user: UserAccountInfo
    message: str

