import socketio
import asyncio
from fastapi import Request
from app.container import ServiceContainer
from app.core.dependencies import get_services
from fastapi import APIRouter, Depends
from app.config import TypeSend,TypeDataSendClient

NAMESPACE_LOG = "/log"
NAMESPACE_DATA = "/data"



sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

_services_instance = None

@sio.event(namespace=NAMESPACE_LOG)
async def connect(sid, environ):
    print("Client connected to log", sid)

@sio.event(namespace=NAMESPACE_LOG)
async def disconnect(sid):
    print("Client disconnected from log", sid)

@sio.event(namespace=NAMESPACE_DATA)
async def connect(sid, environ):
    print("Client connected to data", sid)
    if _services_instance is not None:
        cam_status = bool(_services_instance.obj_camera.get_is_connect()) if getattr(_services_instance, "obj_camera", None) else False
        tcp_status = bool(getattr(_services_instance, "is_tcp_connected", False))
        await sio.emit("status_camera", {"status": cam_status}, to=sid, namespace=NAMESPACE_DATA)
        await sio.emit("status_tcp", {"status": tcp_status}, to=sid, namespace=NAMESPACE_DATA)

@sio.event(namespace=NAMESPACE_DATA)
async def disconnect(sid):
    print("Client disconnected from data", sid)


async def log_sender(app):
    """Task chạy nền để tiêu thụ dữ liệu từ queue và gửi qua Socket.io.

    Cơ chế tối ưu:
    1. Tiêu thụ kiệt (Drain all) hàng đợi dữ liệu và log trong mỗi lượt để tránh nghẽn.
    2. Chỉ emit status_camera và status_com khi có thay đổi trạng thái hoặc định kỳ (3s).
    3. Tránh CPU-spin bằng sleep ngắn (20ms) khi hàng đợi rỗng.
    """
    global _services_instance
    print("📢 Log Sender Task đã bắt đầu...")
    services: ServiceContainer = app.state.services
    _services_instance = services

    last_cam_status = None
    last_tcp_status = None
    last_status_broadcast_time = 0.0
    loop = asyncio.get_running_loop()

    while not services.runtime_state.is_stop_requested():
        try:
            now = loop.time()
            cam_status = bool(services.obj_camera.get_is_connect()) if getattr(services, "obj_camera", None) else False
            tcp_status = bool(getattr(services, "is_tcp_connected", False))

            # Chỉ phát tán trạng thái phần cứng khi có thay đổi hoặc sau mỗi 3 giây (heartbeat)
            if (
                cam_status != last_cam_status
                or tcp_status != last_tcp_status
                or (now - last_status_broadcast_time) >= 3.0
            ):
                try:
                    await sio.emit("status_camera", {"status": cam_status}, namespace=NAMESPACE_DATA)
                    await sio.emit("status_tcp", {"status": tcp_status}, namespace=NAMESPACE_DATA)
                    last_cam_status = cam_status
                    last_tcp_status = tcp_status
                    last_status_broadcast_time = now
                except Exception as emit_err:
                    print(f"⚠️ [SocketIO LogSender] Lỗi emit hardware status: {emit_err}")

            processed_count = 0

            # 1. Tiêu thụ toàn bộ log đang chờ trong queue_log_send_client
            while processed_count < 100:
                data_log = services.queue_log_send_client.get()
                if data_log is None:
                    break
                processed_count += 1
                if not isinstance(data_log, dict):
                    continue
                log_type = data_log.get("type", None)
                msg = data_log.get("message", "")
                try:
                    if log_type == TypeSend.type_log_capture:
                        await sio.emit(TypeSend.type_log_capture, {"msg": msg}, namespace=NAMESPACE_LOG)
                    elif log_type == TypeSend.log_calibration:
                        await sio.emit(TypeSend.log_calibration, {"msg": msg}, namespace=NAMESPACE_LOG)
                    elif log_type == TypeSend.log_home:
                        await sio.emit(TypeSend.log_home, {"msg": msg}, namespace=NAMESPACE_LOG)
                except Exception as emit_log_err:
                    print(f"⚠️ [SocketIO LogSender] Lỗi emit log {log_type}: {emit_log_err}")

            # 2. Tiêu thụ toàn bộ dữ liệu phán định trong queue_data_send_client
            while processed_count < 200:
                data_send_client = services.queue_data_send_client.get()
                if data_send_client is None:
                    break
                processed_count += 1
                if not isinstance(data_send_client, dict):
                    continue
                data_type = data_send_client.get("type", None)
                data_data = data_send_client.get("data", None)
                try:
                    if TypeDataSendClient.data_calibration_send_client == data_type:
                        await sio.emit(TypeDataSendClient.data_calibration_send_client, {"data": data_data}, namespace=NAMESPACE_DATA)
                    elif data_type in {
                        TypeSend.judgment_reset,
                        TypeSend.judgment_item_result,
                        TypeSend.judgment_product_result,
                    }:
                        await sio.emit(data_type, {"data": data_data}, namespace=NAMESPACE_DATA)
                except Exception as emit_data_err:
                    print(f"⚠️ [SocketIO LogSender] Lỗi emit data {data_type}: {emit_data_err}")

            # Nếu không có dữ liệu nào trong queue, nhường event loop 20ms
            if processed_count == 0:
                await asyncio.sleep(0.02)
            else:
                # Nếu vừa xả nhiều dữ liệu, nhường nhẹ 1ms cho các coroutine khác
                await asyncio.sleep(0.001)
        except Exception as loop_err:
            print(f"❌ [SocketIO LogSender] Lỗi trong vòng lặp sender: {loop_err}")
            await asyncio.sleep(0.1)





# gui data cho calibarion  #  {"type":TypeDataSendClient.data_calibration_send_client,"data":data} # services.queue_data_send_client.put({"type":TypeDataSendClient.data_calibration_send_client,"data":"test"})
 # gui log cho calibarion        {"type":TypeDataSendClient.data_calibration_send_client,"data":data}     services.queue_log_send_client.put({"type":TypeSend.log_calibration,"msg":"vu vinh anh"})






          
    #         if log_type == TypeSend.log_home:
    #             msg = data_log.get("message","")
    #             await sio.emit(TypeSend.log_home, {"msg": msg}, namespace= NAMESPACE_LOG)

    #     data_send_client = services.queue_data_send_client.get()
    #     if data_send_client is not None:
#         if  data_send_client.get("type",None) == TypeSend.datatype_Calibration:
#              await sio.emit(TypeSend.datatype_Calibration, {"data": data_send_client}, namespace= NAMESPACE_DATA)  # Cai nay la anh
#         if data_send_client.get(TypeSend.datatype_Home,None):
#             # print("đã vào đây rồi nha cú bes")
#             # print(data_send_client)
#             await sio.emit(TypeSend.datatype_Home, {"msg":data_send_client}, namespace = NAMESPACE_DATA)

# await asyncio.sleep(0.01)
# obj_queue.put(name_queue_log_client,{"type":log_calibration,"message":result.message()})
# obj_queue.put(name_queue_log_client,{"type":log_Home,"message":"log gui client"})
# # await sio.emit(log_home, {"msg": "Chỗ này để hiển thi log."}, namespace= NAMESPACE_LOG)
#  await sio.emit(log_home, {"msg": "Chỗ này để hiển thi log."}, namespace= NAMESPACE_LOG)
# test_send = {"type":type_capture,"message":"Test log CaptureProduct"}
# obj_queue.put(name_queue_log_client, test_send)
# # # await sio.emit(data_output_judment, {"msg": "xin chao em"}, namespace= NAMESPACE_DATA)
# # data_client = obj_queue.get(name_queue_data_client)
# # if data_client is not None:
