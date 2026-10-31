import json
from pathlib import Path
from app.config import PATH_CONFIG_POINTS
    
class PointRepository:
    def __init__(self):
        self.path_file = Path(
            PATH_CONFIG_POINTS
        )
        self.path_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.path_file.exists():

            self.save_points({})

    def load_points(
        self
    ) -> dict:
        if not self.path_file.exists():
            return {}
        with open(
            self.path_file,
            "r",
            encoding="utf-8-sig"
        ) as file:
            return json.load(file)

    def save_points(
        self,
        data: dict
    ) -> None:
        with open(
            self.path_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )