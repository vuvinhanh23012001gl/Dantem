import os
import time
import threading
from typing import Dict, Any
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/api/system",
    tags=["System Control"]
)

def _delayed_exit(delay_seconds: float = 0.8) -> None:
    """
    Chờ một khoảng thời gian ngắn để server trả về response cho client trước khi ngắt tiến trình.

    Args:
        delay_seconds (float): Thời gian chờ tính bằng giây. Mặc định là 0.8s.
    """
    time.sleep(delay_seconds)
    print("🛑 [Shutdown] Đang kết thúc tiến trình ứng dụng...")
    os._exit(0)

@router.post("/shutdown")
async def shutdown_system(request: Request) -> JSONResponse:
    """
    Dừng toàn bộ hệ thống, ngắt các luồng, đóng Camera, COM và giải phóng bộ nhớ.

    Args:
        request (Request): FastAPI request context chứa state của ứng dụng.

    Returns:
        JSONResponse: Trả về trạng thái thực hiện giải phóng tài nguyên.
    """
    try:
        fastapi_app = request.app

        # 1. Dừng Pipeline xử lý chính
        pipeline = getattr(fastapi_app.state, "pipeline", None)
        if pipeline is not None:
            print("🛑 [Shutdown] Dừng Pipeline chính...")
            try:
                pipeline.stop_task_pipeline()
            except Exception as e:
                print(f"[Shutdown] Lỗi khi dừng pipeline: {e}")

        # 2. Dừng Services và giải phóng phần cứng (Camera, COM, STM32)
        services = getattr(fastapi_app.state, "services", None)
        if services is not None:
            print("🛑 [Shutdown] Dừng ServiceContainer và giải phóng phần cứng...")
            try:
                services.stop()
            except Exception as e:
                print(f"[Shutdown] Lỗi khi dừng services: {e}")

        # 3. Lên lịch ngắt tiến trình uvicorn để giải phóng triệt để OS process
        exit_thread = threading.Thread(
            target=_delayed_exit,
            kwargs={"delay_seconds": 0.8},
            daemon=True,
            name="DelayedProcessExit"
        )
        exit_thread.start()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Đã dừng toàn bộ luồng và giải phóng tài nguyên hệ thống."
            }
        )

    except Exception as e:
        print(f"❌ [Shutdown] Lỗi trong quá trình tắt hệ thống: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Lỗi khi dừng hệ thống: {str(e)}"
            }
        )
