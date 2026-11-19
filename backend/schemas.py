from pydantic import BaseModel, Field
from typing import List, Optional

class CategoryBase(BaseModel):
    name: str
    icon: Optional[str] = "restaurant"
    sort_order: Optional[int] = 0

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    class Config:
        from_attributes = True

class DishBase(BaseModel):
    name: str
    price: float
    available: bool = True
    unit: str = "portion"
    description: Optional[str] = ""
    categories: Optional[List[str]] = []
    image_url: Optional[str] = ""
    sort_order: Optional[int] = 0

class DishCreate(DishBase):
    pass

class Dish(DishBase):
    id: int
    class Config:
        from_attributes = True

class BillItem(BaseModel):
    name: str
    quantity: float
    unit_price: float
    subtotal: float
    piece_count: Optional[int] = None

class AIItem(BaseModel):
    name: str
    quantity: float = Field(gt=0)
    confidence: float = Field(ge=0.0, le=1.0)
    piece_count: Optional[int] = None

class AIResponse(BaseModel):
    is_valid_plate: bool
    rejection_reason: Optional[str] = ""
    items: List[AIItem] = []

class BillResponse(BaseModel):
    items: List[BillItem]
    total: float
    session_id: str
    bill_number: Optional[str] = ""

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    retake_required: bool = False

class VerifyRequest(BaseModel):
    session_id: str
    pin: str
    corrections: List[dict]
    cf_turnstile_response: str = Field(default="", alias="cf-turnstile-response")

    class Config:
        populate_by_name = True
