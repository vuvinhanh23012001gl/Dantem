from .api_config_camera import router as camera_router
from .api_config_software import router as software_router
from .api_product import router as product_router
from .home import router as home_router
from .api_captureproduct import router as captureproduct_router
from .socketio_log import sio,log_sender
from .api_draw_regulations import router as draw_regulations_router
from .api_tool_law_regulations import router as tool_law_regulations_router
from .api_instruct_worker import router as instruct_worker_router
from .api_instruct_staff_ee import router as instruct_staff_ee_router
from .api_instruct_fix_erro import router as instruct_fix_erro_router
from .api_shutdown import router as shutdown_router
from .api_anti_blur import router as anti_blur_router
from .api_robot_config import router as robot_config_router
from .api_barcode import router as barcode_router
__all__ = [
    "home_router",
    "camera_router",
    "software_router",
    "anti_blur_router",
    "robot_config_router",
    "product_router",
    "captureproduct_router",
    "socket_log",
    "draw_regulations_router",
    "tool_law_regulations_router",
    "instruct_worker_router",
    "instruct_staff_ee_router",
    "instruct_fix_erro_router",
    "shutdown_router",
    "barcode_router",
]
