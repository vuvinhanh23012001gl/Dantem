
# from pathlib import Path
# import sys
# sys.path.append(str(Path(__file__).resolve().parents[3]))

from datetime import datetime
from app.utils import Folder
from app.config import PATH_INFORMATION_SOFTWARE 

class Infor_Software:
    def __init__(self,):
        self.path_infor_software = Folder.get_or_create_json_by_path(PATH_INFORMATION_SOFTWARE)
        self.data_head_infor_software = Folder.read_json_from_file(self.path_infor_software) 
        self.name = self.data_head_infor_software.get("name","Weld Ink Line Measurement")
        self.version = self.data_head_infor_software.get("version","1.0.0")
        self.author = self.data_head_infor_software.get("author","Vũ VinH Ánh")
        self.company = self.data_head_infor_software.get("company","Công ty TNHH Công nghiệp Brother Việt Nam")
        self.description = self.data_head_infor_software.get("description","Phần mềm nhận diện kích thước độ đường hàn mực")
        self.build_date = self.data_head_infor_software.get("build_date",datetime.now().strftime("%d-%m-%Y"))
        self.license = self.data_head_infor_software.get("license","Internal Use")
    
    # ===== GET =====
    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

    def get_author(self):
        return self.author

    def get_company(self):
        return self.company

    def get_description(self):
        return self.description

    def get_build_date(self):
        return self.build_date

    def get_license(self):
        return self.license

    # ===== SET =====
    def set_name(self, value: str):
        self.name = value
        self.save_upadte_data_infor_software()
    def set_version(self, value: str):
        self.version = value
        self.save_upadte_data_infor_software()
    def set_author(self, value: str):
        self.author = value
        self.save_upadte_data_infor_software()
    def set_company(self, value: str):
        self.company = value
        self.save_upadte_data_infor_software()
    def set_description(self, value: str):
        self.description = value
        self.save_upadte_data_infor_software()

    def set_build_date(self, value: str):
        self.build_date = value
        self.save_upadte_data_infor_software()

    def set_license(self, value: str):
        self.license = value
        self.save_upadte_data_infor_software()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "company": self.company,
            "description": self.description,
            "build_date": self.build_date,
            "license": self.license,
        }

    def __str__(self):
        return (
            f"{self.name} v{self.version}\n"
            f"Author: {self.author}\n"
            f"Company: {self.company}\n"
            f"Build date: {self.build_date}\n"
            f"License: {self.license}\n"
            f"Description: {self.description}"
        )
    
    def save_upadte_data_infor_software(self):
        Folder.write_json_in_file(self.path_infor_software,self.to_dict())

        
# I1  = Infor_Software()
# I1.save_upadte_data_infor_software()