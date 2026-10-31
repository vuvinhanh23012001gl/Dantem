import unittest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Any

from app.stages.stage_2_transform import StageTransform
from app.container import EnumMode


@dataclass
class DummyPreparedProduct:
    product_id: str
    frames: list[dict[str, Any]]
    scale_mm_per_pixel: float
    session_id: str
    number_step: int


class TestStage2ReturnToFirstPoint(unittest.TestCase):
    """Kiểm tra logic di chuyển IAI về vị trí item đầu tiên (step 1) sau khi hoàn tất phán định."""

    def setUp(self) -> None:
        self.mock_services = MagicMock()
        self.mock_services.obj_iai_config.move_retry_count = 1
        self.mock_services.obj_iai_config.move_timeout = 1.0
        self.mock_services.obj_iai_control.get_status.return_value.name = "AUTO"
        self.mock_services.runtime_state.is_stop_requested.return_value = False
        self.mock_services.obj_camera.capture_once.return_value = (True, MagicMock())
        self.mock_services.obj_judment.run_summary.return_value = {
            "status": "OK",
            "overall": True,
            "inspectors": {},
        }
        self.mock_services.obj_product_count_service.record_result.return_value = {
            "total": 1,
            "ok": 1,
            "ng": 0,
        }

    def test_return_to_first_point_after_judgment(self) -> None:
        # Chuẩn bị dữ liệu 2 frame, mỗi frame có point với tọa độ khác nhau
        prepared = DummyPreparedProduct(
            product_id="1",
            frames=[
                {
                    "frame_id": "0",
                    "points": [
                        {
                            "point_id": "0",
                            "x": 1234,
                            "y": 5678,
                            "z": 9012,
                            "judgment": {"ForeignObjectInspector": {}},
                            "source": {},
                        },
                        {
                            "point_id": "1",
                            "x": 2000,
                            "y": 3000,
                            "z": 4000,
                            "judgment": {"ForeignObjectInspector": {}},
                            "source": {},
                        },
                    ],
                },
                {
                    "frame_id": "1",
                    "points": [
                        {
                            "point_id": "0",
                            "x": 8888,
                            "y": 7777,
                            "z": 6666,
                            "judgment": {"ForeignObjectInspector": {}},
                            "source": {},
                        },
                    ],
                },
            ],
            scale_mm_per_pixel=0.05,
            session_id="session_test",
            number_step=3,
        )
        self.mock_services.prepared_product = prepared

        # Mock lệnh di chuyển luôn thành công
        self.mock_services.obj_iai_control.move_to_point.return_value = True

        stage = StageTransform(self.mock_services)

        # Mock các hàm I/O nội bộ để test nhanh
        with patch.object(stage, "_save_image", return_value="url/test.jpg"), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_session_item_dir", return_value=MagicMock()):
            
            stage.run()

        # Kiểm tra các lệnh gọi di chuyển IAI
        calls = self.mock_services.obj_iai_control.move_to_point.call_args_list
        self.assertEqual(len(calls), 4, "Phải có 3 lần di chuyển cho 3 point và 1 lần di chuyển về point đầu tiên")

        # Call cuối cùng phải có tọa độ của point đầu tiên (step 1: x=1234, y=5678, z=9012)
        last_call_args, last_call_kwargs = calls[-1]
        self.assertEqual(last_call_args[0], 1234, "Tọa độ X cuối cùng phải là X của item đầu tiên")
        self.assertEqual(last_call_args[1], 5678, "Tọa độ Y cuối cùng phải là Y của item đầu tiên")
        self.assertEqual(last_call_args[2], 9012, "Tọa độ Z cuối cùng phải là Z của item đầu tiên")

        # Kiểm tra chuyển mode sang MODE_EXPORT
        self.mock_services.set_mode.assert_called_with(EnumMode.MODE_EXPORT)


if __name__ == "__main__":
    unittest.main()
