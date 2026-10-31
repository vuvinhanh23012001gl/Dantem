import os
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from app.config.path_config import PATH_DOC_INSTRUCT_STAFF_EE

router = APIRouter(
    prefix="/api/instruct",
    tags=["Instruction - Staff EE"]
)

@router.get("/staff_ee", response_class=FileResponse)
@router.get("/staff_ee.pdf", response_class=FileResponse)
def get_instruct_staff_ee() -> FileResponse:
    """
    Trả về file PDF tài liệu hướng dẫn sử dụng phần mềm dành cho kỹ sư EE để xem trực tiếp trên tab mới.

    Returns:
        FileResponse: Stream file PDF với định dạng application/pdf để trình duyệt mở trực tiếp.

    Raises:
        HTTPException: Trả về lỗi 404 nếu file tài liệu không tồn tại trên hệ thống.
    """
    try:
        if not os.path.exists(PATH_DOC_INSTRUCT_STAFF_EE):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tài liệu hướng dẫn sử dụng EE không tồn tại trên hệ thống."
            )
        return FileResponse(
            path=PATH_DOC_INSTRUCT_STAFF_EE,
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tải tài liệu hướng dẫn EE: {str(e)}"
        )
