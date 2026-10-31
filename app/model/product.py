class Product:

    def __init__(
        self,
        id: int,
        name: str,
        description: str = "",
        limit_x_max: int = 0,
        limit_y_max: int = 0,
        limit_z_max: int = 0,
        home_x: float = 0,
        home_y: float = 0,
        home_z: float = 0
    ):

        self._id = id
        self._name = name
        self._description = description

        # IAI limits
        self.limit_x_max = limit_x_max
        self.limit_y_max = limit_y_max
        self.limit_z_max = limit_z_max
        
        self.home_x = home_x
        self.home_y = home_y
        self.home_z = home_z

        # metadata
        self.created_at = ""
        self.updated_at = ""

    # =========================
    # ID
    # =========================

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    # =========================
    # NAME
    # =========================

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    # =========================
    # DESCRIPTION
    # =========================

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    # =========================
    # TO DICT
    # =========================

    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "limit_x_max": self.limit_x_max,
            "limit_y_max": self.limit_y_max,
            "limit_z_max": self.limit_z_max,
            "home_x": self.home_x,
            "home_y": self.home_y,
            "home_z": self.home_z,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    # =========================
    # REPR
    # =========================

    def __repr__(self):

        return (
            f"Product("
            f"id={self.id}, "
            f"name='{self.name}'"
            f")"
        )