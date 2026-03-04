from pydantic import BaseModel
from typing import Optional

class Medicine(BaseModel):
    product_id: str
    name: str
    pzn: str
    price: float
    units_per_pack: int
    package_size_raw: str
    description: Optional[str] = None
    stock_level: int = 100
    prescription_required: bool = False
    reorder_threshold: int = 20
