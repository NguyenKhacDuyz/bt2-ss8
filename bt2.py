from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

app = FastAPI(title="Logistics API")

# --- 1. ĐỊNH NGHĨA CÁC MODEL (PYDANTIC) ---

class CarrierStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class CarrierBase(BaseModel):
    code: str
    name: str = Field(..., min_length=3, description="Tên không được rỗng và ít nhất 3 ký tự")
    max_weight_capacity: int = Field(..., gt=0, description="Sức chứa phải lớn hơn 0")
    status: CarrierStatus

class CarrierCreate(CarrierBase):
    pass

class CarrierUpdate(CarrierBase):
    pass

class CarrierResponse(CarrierBase):
    id: int

# --- DATABASE TẠM THỜI (IN-MEMORY) ---
carriers_db: List[dict] = [
    {"id": 1, "code": "GHN", "name": "Giao Hang Nhanh", "max_weight_capacity": 5000, "status": "ACTIVE"},
    {"id": 2, "code": "GHTK", "name": "Giao Hang Tiet Kiem", "max_weight_capacity": 4000, "status": "ACTIVE"},
    {"id": 3, "code": "VTP", "name": "Viettel Post", "max_weight_capacity": 10000, "status": "SUSPENDED"}
]
carrier_id_counter = 4

# --- 2. CÁC API ENDPOINT CHO CARRIERS ---

@app.post("/carriers", response_model=CarrierResponse, status_code=201)
def create_carrier(carrier: CarrierCreate):
    global carrier_id_counter
    # Kiểm tra code unique
    for c in carriers_db:
        if c["code"] == carrier.code:
            raise HTTPException(status_code=400, detail="Carrier code already exists")
    
    new_carrier = carrier.dict()
    new_carrier["id"] = carrier_id_counter
    carriers_db.append(new_carrier)
    carrier_id_counter += 1
    return new_carrier

@app.get("/carriers", response_model=List[CarrierResponse])
def get_carriers(
    keyword: Optional[str] = Query(None, description="Tìm theo tên hoặc code"),
    status: Optional[CarrierStatus] = Query(None, description="Lọc theo trạng thái"),
    min_weight: Optional[int] = Query(None, description="Lọc theo sức chứa tối thiểu")
):
    result = carriers_db
    
    if keyword:
        keyword_lower = keyword.lower()
        result = [c for c in result if keyword_lower in c["name"].lower() or keyword_lower in c["code"].lower()]
        
    if status:
        result = [c for c in result if c["status"] == status.value]
        
    if min_weight is not None:
        result = [c for c in result if c["max_weight_capacity"] >= min_weight]
        
    return result

@app.get("/carriers/{carrier_id}", response_model=CarrierResponse)
def get_carrier_detail(carrier_id: int):
    for c in carriers_db:
        if c["id"] == carrier_id:
            return c
    raise HTTPException(status_code=404, detail="Carrier not found")

@app.put("/carriers/{carrier_id}", response_model=CarrierResponse)
def update_carrier(carrier_id: int, carrier_update: CarrierUpdate):
    for idx, c in enumerate(carriers_db):
        if c["id"] == carrier_id:
            # Kiểm tra code unique nếu có đổi code
            if c["code"] != carrier_update.code:
                if any(ext_c["code"] == carrier_update.code for ext_c in carriers_db):
                    raise HTTPException(status_code=400, detail="Carrier code already exists")
            
            updated_data = carrier_update.dict()
            updated_data["id"] = carrier_id
            carriers_db[idx] = updated_data
            return updated_data
            
    raise HTTPException(status_code=404, detail="Carrier not found")

@app.delete("/carriers/{carrier_id}")
def delete_carrier(carrier_id: int):
    for idx, c in enumerate(carriers_db):
        if c["id"] == carrier_id:
            carriers_db.pop(idx)
            return {"message": "Carrier deleted successfully"}
    raise HTTPException(status_code=404, detail="Carrier not found")

# --- (Bạn có thể tự triển khai thêm phần Shipments tương tự) ---
