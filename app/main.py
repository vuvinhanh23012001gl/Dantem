import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
from app.config.path_config import (
    BASE_PATH_STORAGE,
    PATH_FOLDER_OUTPUT,
    PATH_FOLDER_STATIC,
    URL_PATH_OUTPUT,
    URL_PATH_STATIC,
    URL_PATH_STORAGE,
)
from app.container import create_container
from app.pipeline import Pipeline

from app.routers import (
    camera_router,
    software_router,
    product_router,
    home_router,
    captureproduct_router,
    sio,draw_regulations_router,tool_law_regulations_router,
    log_sender,
    instruct_worker_router,instruct_staff_ee_router,instruct_fix_erro_router,
    shutdown_router,
    anti_blur_router,
    barcode_router,
    robot_config_router,
)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    print("🚀 Đang khởi tạo tài nguyên...")
    loop = asyncio.get_running_loop()
    previous_exception_handler = loop.get_exception_handler()

    def handle_connection_reset(loop, context):
        error = context.get("exception")
        if isinstance(error, ConnectionResetError) and getattr(error, "winerror", None) == 10054:
            return
        if previous_exception_handler is not None:
            previous_exception_handler(loop, context)
        else:
            loop.default_exception_handler(context)

    loop.set_exception_handler(handle_connection_reset)
    fastapi_app.state.services = create_container()
    fastapi_app.state.pipeline = Pipeline(fastapi_app.state.services)
    asyncio.create_task(log_sender(fastapi_app))
    yield 
    print("🛑 Đang dọn dẹp tài nguyên...")
    if getattr(fastapi_app.state, "pipeline", None):
        fastapi_app.state.pipeline.stop_task_pipeline()
    if getattr(fastapi_app.state, "services", None):
        fastapi_app.state.services.stop()
    loop.set_exception_handler(previous_exception_handler)


def create_app():
    # 🔹 FastAPI gốc
    global fastapi_app
    fastapi_app = FastAPI(title="Width Line Detection",lifespan=lifespan)

    # 🔹 Static
    fastapi_app.mount(URL_PATH_STATIC, StaticFiles(directory=str(PATH_FOLDER_STATIC)), name="static")
    fastapi_app.mount(URL_PATH_STORAGE, StaticFiles(directory=str(BASE_PATH_STORAGE)), name="storage")
    fastapi_app.mount(URL_PATH_OUTPUT, StaticFiles(directory=str(PATH_FOLDER_OUTPUT)), name="output")
    
    # 🔹 Router
    fastapi_app.include_router(home_router)
    fastapi_app.include_router(camera_router)
    fastapi_app.include_router(software_router)
    fastapi_app.include_router(product_router)
    fastapi_app.include_router(captureproduct_router)
    fastapi_app.include_router(draw_regulations_router)
    fastapi_app.include_router(tool_law_regulations_router)
    fastapi_app.include_router(instruct_worker_router)
    fastapi_app.include_router(instruct_staff_ee_router)
    fastapi_app.include_router(instruct_fix_erro_router)
    fastapi_app.include_router(shutdown_router)
    fastapi_app.include_router(anti_blur_router)
    fastapi_app.include_router(barcode_router)
    fastapi_app.include_router(robot_config_router)
   
    return socketio.ASGIApp(sio, fastapi_app)


# 🔥 Uvicorn PHẢI chạy biến này
app = create_app()
