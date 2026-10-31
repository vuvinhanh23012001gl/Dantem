from app.container import ServiceContainer, EnumMode
from app.stages.stage_2_transform import StageTransform
import json
from datetime import datetime, timezone
from app.config.path_config import PATH_FOLDER_OUTPUT

class StageExport:
    def __init__(self, service: ServiceContainer):
        self.service = service

    def run(self):
        """Tổng hợp kết quả sản phẩm, lưu file và chờ chu kỳ Reset tiếp theo.

        Input: kết quả point từ ``service.runtime_state``.
        Output: đường dẫn file JSON tổng hợp.
        Errors: ``RuntimeError`` nếu không có kết quả để export.
        """
        results = self.service.runtime_state.get_product_result()
        if not isinstance(results, list) or not results:
            raise RuntimeError("Không có kết quả sản phẩm để export")
        PATH_FOLDER_OUTPUT.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = PATH_FOLDER_OUTPUT / f"judgment_result_{timestamp}.json"
        clean_points = [
            StageTransform._strip_internal_images(result) if isinstance(result, dict) else result
            for result in results
        ]
        payload = {
            "product_id": results[0].get("product_id"),
            "overall": all(result.get("overall") is True for result in results),
            "status": "OK" if all(result.get("overall") is True for result in results) else "NG",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "points": clean_points,
        }
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        self.service.send_judgment_log(f"✅ Đã lưu kết quả: {output_path.name}")

        if getattr(self.service, "queue_manage_log", None):
            try:
                session_id = results[0].get("session_id", f"session_{timestamp}") if results else f"session_{timestamp}"
                product_name = results[0].get("product_name")
                if not product_name and getattr(self.service, "obj_manager_log", None):
                    product_name = self.service.obj_manager_log.get_current_product_name()
                if not product_name:
                    product_name = f"product_{payload.get('product_id', 1)}"

                # Tính tỷ lệ phán định % từ ProductCountService
                pass_rate_str = "0.00%"
                if getattr(self.service, "obj_product_count_service", None):
                    counts = self.service.obj_product_count_service.get_counts()
                    ok_count = counts.get("ok", 0)
                    total_count = counts.get("total", 0)
                    if total_count > 0:
                        pass_rate_str = f"{(ok_count / total_count) * 100:.2f}%"

                # Tổng hợp message log phán định của phiên
                ng_msgs = []
                for pt in results:
                    if pt.get("overall") is False:
                        m = pt.get("message") or f"Mặt {pt.get('face_id', pt.get('frame_id', ''))} Item {pt.get('point_id', pt.get('item_id', ''))} NG"
                        ng_msgs.append(m)
                session_summary_msg = " | ".join(ng_msgs) if ng_msgs else "Sản phẩm đạt chuẩn toàn bộ hạng mục"

                # Đẩy bản ghi tổng kết session vào file CSV tổng summary_daily.csv (Ảnh 1)
                cfg_sw = getattr(self.service, "obj_config_software", None)
                if cfg_sw is None or getattr(cfg_sw, "open_csv", True):
                    self.service.queue_manage_log.put({
                        "type": "csv_summary",
                        "msg": {
                            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Product": product_name,
                            "Session": session_id,
                            "OK/NG": payload.get("status"),
                            "Tỷ lệ phán định": pass_rate_str,
                            "Message": session_summary_msg,
                        },
                    })
            except Exception as e:
                print(f"[EXPORT] Lỗi đẩy log session: {e}")

        self.service.set_mode(EnumMode.MODE_IDLE)
        return str(output_path)
        
