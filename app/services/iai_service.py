
from app.config import IAIConfig
class IAIService:

    def __init__(self, config: IAIConfig):

        self.config = config

    # ==========================================================
    # CHECK LIMIT
    # ==========================================================
    def is_valid_x(self, x: float) -> bool:

        return (
            self.config.limit_x_min <= x <=
            self.config.limit_x_max
        )

    def is_valid_y(self, y: float) -> bool:

        return (
            self.config.limit_y_min <= y <=
            self.config.limit_y_max
        )

    def is_valid_z(self, z: float) -> bool:

        return (
            self.config.limit_z_min <= z <=
            self.config.limit_z_max
        )

    # ==========================================================
    # CHECK POSITION
    # ==========================================================
    def is_valid_position(
        self,
        x: float,
        y: float,
        z: float
    ) -> bool:

        return (
            self.is_valid_x(x) and
            self.is_valid_y(y) and
            self.is_valid_z(z)
        )

    # ==========================================================
    # GET HOME POSITION
    # ==========================================================
    def get_home_position(self) -> tuple:

        return (
            self.config.home_x,
            self.config.home_y,
            self.config.home_z
        )

    # ==========================================================
    # SET HOME POSITION
    # ==========================================================
    def set_home_position(
        self,
        x: float,
        y: float,
        z: float
    ):

        self.config.home_x = x
        self.config.home_y = y
        self.config.home_z = z

        self.config.save()

    # ==========================================================
    # UPDATE LIMIT X
    # ==========================================================
    def set_limit_x(
        self,
        min_x: float,
        max_x: float
    ):

        self.config.limit_x_min = min_x
        self.config.limit_x_max = max_x

        self.config.save()

    # ==========================================================
    # UPDATE LIMIT Y
    # ==========================================================
    def set_limit_y(
        self,
        min_y: float,
        max_y: float
    ):

        self.config.limit_y_min = min_y
        self.config.limit_y_max = max_y

        self.config.save()

    # ==========================================================
    # UPDATE LIMIT Z
    # ==========================================================
    def set_limit_z(
        self,
        min_z: float,
        max_z: float
    ):

        self.config.limit_z_min = min_z
        self.config.limit_z_max = max_z

        self.config.save()
        
    def get_dict(self) -> dict:
        return self.config.get_dict()