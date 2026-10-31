import re
import numpy as np
import cv2
import time

class Logic():
    @staticmethod
    def is_valid_id(id_value) -> bool:
        if id_value is None:
            return False
        id_str = str(id_value).strip()
        # Chỉ cho phép chữ số
        return bool(re.fullmatch(r"[0-9]+", id_str))
    
    @staticmethod
    async def convert_uploadfile_to_numpy(file) -> np.ndarray:
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            print("Lỗi chuyển đổi UploadFile sang numpy ndarray")
            return None
        # cv2.imshow("anh show",img)
        return img
    
        
    @staticmethod
    def validate_full_regulation(data: dict) -> tuple[bool, str]:

        if not isinstance(data, dict):
            return False, "Data phải là dict"

        if "width" not in data or "heigh" not in data:
            return False, "Thiếu width hoặc heigh"

        if not isinstance(data["width"], int) or data["width"] <= 0:
            return False, "width phải là int > 0"

        if not isinstance(data["heigh"], int) or data["heigh"] <= 0:
            return False, "heigh phải là int > 0"

        width = data["width"]
        heigh = data["heigh"]

        color_pattern = re.compile(r"^#[0-9a-fA-F]{6}$")

        for key, value in data.items():

            if key in ("width", "heigh"):
                continue

            if not key.isdigit():
                return False, f"Key '{key}' không hợp lệ"

            if not isinstance(value, list):
                return False, f"Key '{key}' Không phải list"

            for idx, item in enumerate(value):

                if not isinstance(item, dict):
                    return False, f"{key}[{idx}] phải là dict"

                # ===== Bắt buộc phải có tọa độ =====
                for field in ["PointStarX","PointStarY","PointEndX","PointEndY"]:
                    if field not in item:
                        return False, f"{key}[{idx}] thiếu '{field}'"

                    if not isinstance(item[field], (int, float)):
                        return False, f"{key}[{idx}]['{field}'] phải là số"

                x1 = item["PointStarX"]
                y1 = item["PointStarY"]
                x2 = item["PointEndX"]
                y2 = item["PointEndY"]

                # ===== Boundary =====
                if not (0 <= x1 <= width and 0 <= x2 <= width):
                    return False, f"{key}[{idx}] X vượt boundary"

                if not (0 <= y1 <= heigh and 0 <= y2 <= heigh):
                    return False, f"{key}[{idx}] Y vượt boundary"

                # ===== Line length check =====
                if x1 == x2 and y1 == y2:
                    return False, f"{key}[{idx}] Line có độ dài = 0"

                # ===== Validate color =====
                color = item.get("color")
                if color is not None:
                    if not isinstance(color, str) or not color_pattern.match(color):
                        return False, f"{key}[{idx}] color không hợp lệ"

                # ===== Validate Level =====
                levels = []
                for i in range(1, 5):
                    level_key = f"level{i}"
                    value_level = item.get(level_key)

                    if value_level is None:
                        break

                    if not isinstance(value_level, (int, float)):
                        return False, f"{key}[{idx}]['{level_key}'] phải là số"

                    if value_level < 0:
                        return False, f"{key}[{idx}]['{level_key}'] không được âm"

                    levels.append(value_level)

                # phải có ít nhất 1 level
                if len(levels) == 0:
                    return False, f"{key}[{idx}] phải có ít nhất level1"

                # check tăng dần
                for i in range(1, len(levels)):
                    if levels[i] <= levels[i-1]:
                        return False, f"{key}[{idx}] Level phải tăng dần"

        return True, "Dữ liệu hợp lệ"

    @staticmethod
    def validate_calibration_data(data: dict):
        if not data or not isinstance(data, dict):
            return {"status": False, "message": "Dữ liệu calibration rỗng hoặc không đúng định dạng"}

        # ===== name =====
        name = data.get("name")
        if not isinstance(name, str) or name.strip() == "":
            return {"status": False, "message": "Tên calibration không được để trống"}

        # ===== numberCapture =====
        number_capture = data.get("numberCapture")
        if isinstance(number_capture, bool) or number_capture is None:
            return {"status": False, "message": "Số lần chụp phải là số nguyên > 0"}
        try:
            val_int = int(number_capture)
            if float(number_capture) != val_int or val_int <= 0:
                return {"status": False, "message": "Số lần chụp phải là số nguyên > 0"}
            if val_int > 100:
                return {"status": False, "message": "Số lần chụp không được vượt quá 100"}
        except (ValueError, TypeError):
            return {"status": False, "message": "Số lần chụp phải là số nguyên > 0"}

        # ===== reality =====
        reality = data.get("reality")
        if isinstance(reality, bool) or reality is None:
            return {"status": False, "message": "Chiều dài thực tế phải > 0"}
        try:
            val_reality = float(reality)
            if val_reality <= 0:
                return {"status": False, "message": "Chiều dài thực tế phải > 0"}
        except (ValueError, TypeError):
            return {"status": False, "message": "Chiều dài thực tế phải > 0"}

        # ===== tọa độ =====
        for key_coord in ["PointStarX", "PointStarY", "PointEndX", "PointEndY"]:
            v = data.get(key_coord)
            if isinstance(v, bool) or v is None:
                return {"status": False, "message": f"Tọa độ {key_coord} không hợp lệ"}
            try:
                float(v)
            except (ValueError, TypeError):
                return {"status": False, "message": f"Tọa độ {key_coord} không hợp lệ"}

        # ===== kiểm tra trùng điểm =====
        try:
            x1, y1 = float(data.get("PointStarX")), float(data.get("PointStarY"))
            x2, y2 = float(data.get("PointEndX")), float(data.get("PointEndY"))
            if x1 == x2 and y1 == y2:
                return {"status": False, "message": "Hai điểm calibration không được trùng nhau"}
        except (ValueError, TypeError):
            return {"status": False, "message": "Tọa độ không hợp lệ"}

        return {"status": True}
    
    @staticmethod
    def is_all_int_strings(lst):
        """Hàm này dùng để kiểm tra xem tất cả phần tử trong danh sách có phải là số nguyên hợp lệ hay không."""
        try:
            return all(isinstance(int(item), int) for item in lst)
        except (ValueError, TypeError):
            return False
        
    @staticmethod 
    def data_format(arr_check):
            """Kiểm tra dữ liệu có đúng định dạng không và chuyển đổi về định dạng chuẩn.
            Ví dụ: 'cmd:1,2,3' -> 'cmd:001,002,003,ok'"""
            
            if not arr_check:
                print("❌ Dữ liệu bị lỗi hoặc trống, không có dữ liệu để so sánh.")
                return False
            if arr_check.startswith("cmd:"):
                raw_data = arr_check[4:].split(",")
                raw_data = [x.strip() for x in raw_data if x.strip() != ""]

                if not raw_data:
                    print("❌ Không có dữ liệu tọa độ sau 'cmd:'")
                    return False

                arr_covert_text = ["cmd:"]
                for i in raw_data:
                    try:
                        padded = f"{int(i):03}"
                    except ValueError:
                        print(f"⚠️ Không thể chuyển '{i}' thành số nguyên.")
                        return False
                    arr_covert_text.append(padded)

                arr_covert_text.append("ok")
                s = ",".join(arr_covert_text[1:])
                s = "cmd:"+s
                return s
            else:
                print("❌ Không phải dữ liệu tọa độ (không bắt đầu bằng 'cmd:')")
                return False
            
    @staticmethod
    def wait_for_specific_data(obj_manager_serial, expected_message, timeout= 4):
        """Hàm này chờ tín hiệu cụ thể từ obj_manager_serial.Chờ thời gian timeout giây.Sau thời gian chờ k được gửi về False.Nếu nhận đúng tín hiệu trả về True"""
        if obj_manager_serial is None:
            return True
        print(f"⏳ Đang chờ tín hiệu:{expected_message} trong {timeout} giây...")
        if hasattr(obj_manager_serial, "clear_rx_queue"):
            obj_manager_serial.clear_rx_queue()
        if hasattr(obj_manager_serial, "clear_tx_queue"):
            obj_manager_serial.clear_tx_queue()
        start_time = time.time()
        expected = Logic.data_format(expected_message)
        while time.time() - start_time < timeout:
            data = obj_manager_serial.get_data_from_queue()
            if data:
                print(f"📥 PC Nhận được: {data}")
                print("📥 Sau chuyển đổi :", expected)
                if data.strip() == expected:
                    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    print(now_str,"✅ Nhận đúng tín hiệu mong đợi.")
                    return True
                else:
                    print("⚠️ Tín hiệu nhận sai nội dung.")
            time.sleep(0.001)  # 🔑 tránh CPU 100% + làm chương trình mượt hơn
        print(f"❌ Timeout: Không nhận được tín hiệu trong {timeout} giây.")
        return False
    
