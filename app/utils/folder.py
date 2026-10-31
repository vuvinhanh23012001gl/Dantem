
import os
import json
import inspect
import psutil
from pathlib import Path
import shutil

class Folder():
    @staticmethod
    def write_json_in_file(file_path: str, data: dict, indent: int = 4):
        """
        Ghi dữ liệu dạng JSON vào file.
        - file_path: đường dẫn tới file json
        - data: dict hoặc list cần lưu
        - indent: số khoảng trắng khi format cho dễ đọc
        """
        try:
            # Đảm bảo thư mục tồn tại
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
                print(f"✅ Đã ghi JSON vào: {file_path}")
        except Exception as e:
            print(f"❌ Lỗi khi ghi file JSON: {e}")

    @staticmethod
    def get_parent_and_append(new_name: str):
        """
        Lấy đường dẫn thư mục cha và nối thêm tên mới dùng thư viện os.
        """
        # 1. Lấy đường dẫn tuyệt đối của file hiện tại
        current_file_path = os.path.abspath(__file__)
        # 2. Lấy thư mục cha của file đó
        parent_dir = os.path.dirname(current_file_path)
        # 3. Nối thêm tên mới vào đường dẫn cha
        # os.path.join sẽ tự động thêm dấu / hoặc \ phù hợp với Windows/Linux
        new_path = os.path.join(parent_dir, new_name)
        return new_path
    
    @staticmethod
    def get_caller_parent_and_append(new_name: str):
        """
        Lấy đường dẫn thư mục cha của file GỌI hàm này và nối thêm tên mới.
        """
        # 1. Lấy thông tin file của người gọi (stack level 1)
        caller_frame = inspect.stack()[1]
        caller_file_path = os.path.abspath(caller_frame.filename)
        # 2. Lấy thư mục cha của file người gọi
        parent_dir = os.path.dirname(caller_file_path)
        # 3. Nối thêm tên mới
        new_path = os.path.join(parent_dir, new_name)
        return new_path
    
    @staticmethod
    def read_json_from_file(file_path: str):
        """
        Đọc dữ liệu từ file JSON.
        - Luôn trả về dict để tránh lỗi NoneType.
        """
        try:
            if not os.path.exists(file_path):
                print(f"⚠️ File không tồn tại: {file_path}")
                return {}
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"📖 Đã đọc xong dữ liệu từ: {file_path}")
                return data if isinstance(data, dict) else {}

        except json.JSONDecodeError:
            print(f"❌ Lỗi: File {file_path} không đúng định dạng JSON.")
            return {}

        except Exception as e:
            print(f"❌ Lỗi khi đọc file JSON: {e}")
            return {}
    @staticmethod
    def get_or_create_json(name_file: str, name_folder: str) -> str:
        """
        Kiểm tra nếu file JSON đã tồn tại thì trả về đường dẫn.
        Nếu chưa có: tạo folder, tạo file và ghi {} rỗng.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir  = os.path.join(current_dir, name_folder)
        os.makedirs(target_dir, exist_ok=True)  # đảm bảo folder tồn tại

        file_path = os.path.join(target_dir, name_file)

        if not os.path.exists(file_path):
            print(f"📂 Chưa có file, tạo mới: {file_path}")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=4)
                print("✅ Đã tạo file JSON rỗng {}")
            except Exception as e:
                print("❌ Lỗi khi tạo file JSON:", e)
        else:
            print(f"✅ File đã tồn tại: {file_path}")
        return file_path
    
    @staticmethod
    def get_or_create_json_by_path(file_path: str) -> str:
        """
        Kiểm tra nếu file JSON đã tồn tại thì trả về đường dẫn.
        Nếu chưa có: tạo folder cha, tạo file và ghi {} rỗng.
        """
        # Lấy thư mục cha từ đường dẫn đầy đủ
        target_dir = os.path.dirname(os.path.abspath(file_path))
        # Đảm bảo thư mục tồn tại
        os.makedirs(target_dir, exist_ok=True)

        if not os.path.exists(file_path):
            print(f"📂 Chưa có file, tạo mới: {file_path}")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=4)
                print("✅ Đã tạo file JSON rỗng {}")
            except Exception as e:
                print("❌ Lỗi khi tạo file JSON:", e)
        else:
            print(f"✅ File đã tồn tại: {file_path}")
        return file_path
    
    @staticmethod
    def get_or_create_json_by_path_return_data(file_path: str) -> dict:
        """
        Nếu file JSON tồn tại → đọc và trả về data.
        Nếu chưa tồn tại → tạo folder + file JSON rỗng {} và trả về {}.
        """

        # Lấy thư mục cha
        target_dir = os.path.dirname(os.path.abspath(file_path))

        # Tạo thư mục nếu chưa có
        os.makedirs(target_dir, exist_ok=True)

        # Nếu file chưa tồn tại → tạo file rỗng
        if not os.path.exists(file_path):
            print(f"📂 Chưa có file, tạo mới: {file_path}")

            data = {}

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                print("✅ Đã tạo file JSON rỗng {}")

            except Exception as e:
                print("❌ Lỗi khi tạo file JSON:", e)

            return data

        # Nếu file đã tồn tại → đọc data
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"✅ Đã đọc file JSON: {file_path}")
            return data

        except Exception as e:
            print("❌ Lỗi khi đọc file JSON:", e)
            return {}
        
    @staticmethod
    def get_or_create_folder(folder_name: str, base_dir: str = None) -> str:
        """
        Tạo folder nếu chưa tồn tại và trả về đường dẫn tuyệt đối.

        :param folder_name: Tên folder cần tạo
        :param base_dir: Thư mục gốc (mặc định là thư mục file hiện tại)
        :return: Đường dẫn tuyệt đối của folder
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        folder_path = os.path.join(base_dir, folder_name)

        os.makedirs(folder_path, exist_ok=True)

        return folder_path
    
    @staticmethod
    def create_folder_from_path(path: str | Path) -> Path:
        """
        Tạo toàn bộ thư mục từ đường dẫn nếu chưa tồn tại
        :param path: đường dẫn đầy đủ
        :return: Path đã được tạo
        """
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def list_drives(with_trailing_sep=True):
        drives = set()
        for p in psutil.disk_partitions(all=False):
            drive, _ = os.path.splitdrive(p.device)
            if not drive:
                drive = p.device.rstrip("\\/")
            if os.name == "nt":
                drive = drive.upper().rstrip("\\/")
                drive = f"{drive}\\" if with_trailing_sep else drive
            drives.add(drive)
        return sorted(drives)
    
    @staticmethod
    def ensure_file(folder: str, filename: str) -> str:
        """
        Đảm bảo thư mục và file tồn tại; tự động tạo nếu chưa có và trả về đường dẫn file.
        """
        if not folder or not filename:
            print(f"Đường dẫn thư mục hoặc tên file {filename} không hợp lệ")
            return False 

        folder_path = Path(folder)
        folder_path.mkdir(parents=True, exist_ok=True)

        file_path = folder_path / filename
        file_path.touch(exist_ok=True)

        return str(file_path.resolve())

    @staticmethod
    def get_parts_from_bottom(path_input: str, levels: int = 1) -> str:
        """
        Lấy n phần tính từ dưới lên.
        levels=1: lấy tên file
        levels=2: lấy folder_cha/tên_file
        """
        path_obj = Path(path_input)
        # Lấy các bộ phận của đường dẫn và đổi sang chuẩn web /
        parts = path_obj.parts 
    
        # Lấy n phần tử cuối cùng
        last_parts = parts[-levels:]
        return "/".join(last_parts)

    @staticmethod
    def get_list_files(folder_path: str, extension: str = None) -> list:
        """
        Lấy danh sách tên các file trong một thư mục.
        :param folder_path: Đường dẫn tới thư mục.
        :param extension: Lọc theo định dạng (ví dụ: '.jpg', '.png'). Để None nếu lấy hết.
        """
        path = Path(folder_path)
        
        # Kiểm tra nếu thư mục không tồn tại
        if not path.exists() or not path.is_dir():
            print(f"[Cảnh báo] Thư mục không tồn tại: {folder_path}")
            return []

        if extension:
            # Lọc theo đuôi file (ví dụ: *.jpg)
            return [f.name for f in path.glob(f"*{extension}")]
        else:
            # Lấy tất cả các file
            return [f.name for f in path.iterdir() if f.is_file()]

    @staticmethod
    def delete_folder(folder_path):
        path = Path(folder_path)
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
                print(f"Đã xóa toàn bộ thư mục: {folder_path}")
                return True
            except Exception as e:
                print(f"Lỗi khi xóa: {e}")
                return False
        else:
            print("Thư mục không tồn tại.")
            return False
        
    @staticmethod
    def delete_file(
        path_file: str | Path
    ) -> bool:

        try:

            path_file = Path(path_file)

            if path_file.exists() and path_file.is_file():

                path_file.unlink()

                return True

            return False

        except Exception as e:

            print(
                f"Lỗi xóa file: {e}"
            )

            return False
    @staticmethod
    def check_file(file_path: str | Path):
        p = Path(file_path)
        if not p.exists():
            return False, "FILE_NOT_EXIST"
        if not p.is_file():
            return False, "PATH_IS_NOT_FILE"
        return True, None

    @staticmethod
    def create_folder(path: str) -> str:
        """
        Tạo folder nếu chưa tồn tại và trả về đường dẫn tuyệt đối.
        """
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return str(p.resolve())
    
    @staticmethod
    def create_file_path(file_path: str):
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        if not os.path.exists(file_path):
            open(file_path, 'w').close()