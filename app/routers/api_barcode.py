from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.core.dependencies import get_services
from app.services.barcode_account_service import BarcodeAccountService

router = APIRouter(
    prefix="/barcode",
    tags=["Barcode"]
)


class CreateBarcodeAccountRequest(BaseModel):
    operator: str = Field(..., description="Tên người thao tác")
    factory: str = Field(..., description="Tên nhà máy")
    line: str = Field(..., description="Tên chuyền")
    role: str = Field(..., description="Loại tài khoản: Manager hoặc User")
    barcode: str = Field(..., description="Mã barcode")


class UpdateAdminRequest(BaseModel):
    username: str = Field(..., description="Tên tài khoản admin")
    password: Optional[str] = Field(None, description="Mật khẩu admin")


@router.get("/accounts")
def get_barcode_accounts(services=Depends(get_services)):
    """
    Lấy danh sách tất cả các tài khoản barcode:
    - Nhóm Quản lý (Manager) hiển thị trước, User hiển thị sau.
    - Admin không cần show trong danh sách này.
    """
    svc = getattr(services, "barcode_account_service", None)
    if not svc:
        # Fallback khởi tạo trực tiếp nếu container chưa gắn
        svc = BarcodeAccountService()

    accounts = svc.get_barcode_accounts()
    return {
        "status": True,
        "total": len(accounts),
        "data": accounts
    }


@router.post("/account")
def create_barcode_account(payload: CreateBarcodeAccountRequest, services=Depends(get_services)):
    """
    Tạo tài khoản barcode mới:
    - Kiểm tra barcode hợp lệ (chỉ chữ và số, không dấu tiếng Việt, không khoảng trắng).
    - Lưu thông tin vào file app/storage/barcode_accounts.json.
    - Trả về dữ liệu tài khoản vừa tạo.
    """
    svc = getattr(services, "barcode_account_service", None)
    if not svc:
        svc = BarcodeAccountService()

    success, message, new_acc = svc.create_account(
        operator=payload.operator,
        factory=payload.factory,
        line=payload.line,
        role=payload.role,
        barcode=payload.barcode
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "status": True,
        "message": message,
        "data": new_acc
    }


@router.delete("/account/{barcode}")
def delete_barcode_account(barcode: str, services=Depends(get_services)):
    """Xóa một tài khoản barcode khỏi file lưu trữ."""
    svc = getattr(services, "barcode_account_service", None)
    if not svc:
        svc = BarcodeAccountService()

    success, message = svc.delete_account(barcode)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )

    return {
        "status": True,
        "message": message
    }


@router.get("/admin")
def get_admin_info(services=Depends(get_services)):
    """Lấy thông tin tài khoản admin (tài khoản và mật khẩu)."""
    svc = getattr(services, "barcode_account_service", None)
    if not svc:
        svc = BarcodeAccountService()

    admin_data = svc.get_admin()
    return {
        "status": True,
        "data": admin_data
    }


@router.post("/admin")
def update_admin_info(payload: UpdateAdminRequest, services=Depends(get_services)):
    """Cập nhật thông tin tài khoản admin."""
    svc = getattr(services, "barcode_account_service", None)
    if not svc:
        svc = BarcodeAccountService()

    success, message = svc.update_admin(username=payload.username, password=payload.password)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "status": True,
        "message": message,
        "data": svc.get_admin()
    }


@router.post("/validate")
def validate_barcode(payload: Dict[str, Any]):
    """API kiểm tra tính hợp lệ của mã barcode (chữ, số, không tiếng Việt, không dấu cách)."""
    code = payload.get("barcode", "")
    is_valid, msg = BarcodeAccountService.validate_barcode(code)
    return {
        "status": True,
        "valid": is_valid,
        "message": msg if not is_valid else "Mã barcode hợp lệ"
    }
