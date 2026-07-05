# ==========================================
# Bài thực hành 2: IT Asset Management AP
# ==========================================

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

app = FastAPI(title="IT Asset Management API")

# --- 1. ĐỊNH NGHĨA MODEL ---

class AssetStatus(str, Enum):
    READY = "READY"
    ALLOCATED = "ALLOCATED"
    REPAIRING = "REPAIRING"
    SCRAPPED = "SCRAPPED"

class AssetBase(BaseModel):
    serial_number: str
    model: str = Field(..., min_length=2, max_length=255, description="Model thiết bị từ 2-255 ký tự")
    stock_available: int = Field(..., ge=0, description="Số lượng tồn kho phải >= 0")
    status: AssetStatus

class AssetCreate(AssetBase):
    pass

class AssetUpdate(AssetBase):
    pass

class AssetResponse(AssetBase):
    id: int

# --- DATABASE TẠM THỜI (IN-MEMORY) ---
assets_db: List[dict] = [
    {"id": 1, "serial_number": "SN-DELL-01", "model": "Dell Latitude 5420", "stock_available": 10, "status": "READY"},
    {"id": 2, "serial_number": "SN-MAC-02", "model": "MacBook Pro M1", "stock_available": 2, "status": "ALLOCATED"},
]
asset_id_counter = 3

# --- 2. CÁC API ENDPOINT CHO ASSETS ---

@app.post("/assets", response_model=AssetResponse, status_code=201)
def create_asset(asset: AssetCreate):
    global asset_id_counter
    # Kiểm tra serial_number unique
    if any(a["serial_number"] == asset.serial_number for a in assets_db):
        raise HTTPException(status_code=400, detail="Serial number already exists")
    
    new_asset = asset.dict()
    new_asset["id"] = asset_id_counter
    assets_db.append(new_asset)
    asset_id_counter += 1
    return new_asset

@app.get("/assets", response_model=List[AssetResponse])
def get_assets(
    keyword: Optional[str] = Query(None, description="Tìm theo serial_number hoặc model"),
    status: Optional[AssetStatus] = Query(None, description="Lọc theo trạng thái"),
    min_stock: Optional[int] = Query(None, description="Lọc theo số lượng tồn kho tối thiểu")
):
    result = assets_db
    
    if keyword:
        kw = keyword.lower()
        result = [a for a in result if kw in a["serial_number"].lower() or kw in a["model"].lower()]
        
    if status:
        result = [a for a in result if a["status"] == status.value]
        
    if min_stock is not None:
        result = [a for a in result if a["stock_available"] >= min_stock]
        
    return result

@app.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset_detail(asset_id: int):
    for a in assets_db:
        if a["id"] == asset_id:
            return a
    raise HTTPException(status_code=404, detail="Asset not found")

@app.put("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: int, asset_update: AssetUpdate):
    for idx, a in enumerate(assets_db):
        if a["id"] == asset_id:
            # Kiểm tra serial_number unique nếu có thay đổi
            if a["serial_number"] != asset_update.serial_number:
                if any(ext_a["serial_number"] == asset_update.serial_number for ext_a in assets_db):
                    raise HTTPException(status_code=400, detail="Serial number already exists")
            
            updated_data = asset_update.dict()
            updated_data["id"] = asset_id
            assets_db[idx] = updated_data
            return updated_data
            
    raise HTTPException(status_code=404, detail="Asset not found")

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int):
    for idx, a in enumerate(assets_db):
        if a["id"] == asset_id:
            assets_db.pop(idx)
            return {"message": "Asset deleted successfully"}
    raise HTTPException(status_code=404, detail="Asset not found")

# --- TODO: Triển khai phần Allocations (Cấp phát) ở đây ---
