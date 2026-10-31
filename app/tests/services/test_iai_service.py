from app.config import IAIConfig
from app.services   import IAIService
from app.config import PATH_FILE_DATA_CONFIG_IAI

def main():

    # ==========================================================
    # INIT
    # ==========================================================
    config = IAIConfig(
       PATH_FILE_DATA_CONFIG_IAI
    )

    iai_service = IAIService(
        config
    )

    # ==========================================================
    # SHOW CURRENT CONFIG
    # ==========================================================
    print("\n===== CURRENT CONFIG =====")

    print("LIMIT X :",
          config.limit_x_min,
          "->",
          config.limit_x_max)

    print("LIMIT Y :",
          config.limit_y_min,
          "->",
          config.limit_y_max)

    print("LIMIT Z :",
          config.limit_z_min,
          "->",
          config.limit_z_max)

    print("HOME :",
          iai_service.get_home_position())

    # ==========================================================
    # TEST POSITION
    # ==========================================================
    print("\n===== TEST POSITION =====")

    x = 100
    y = 200
    z = 300

    result = iai_service.is_valid_position(
        x,
        y,
        z
    )

    print(
        f"Position ({x}, {y}, {z}) = {result}"
    )

    # ==========================================================
    # UPDATE HOME
    # ==========================================================
    print("\n===== UPDATE HOME =====")

    iai_service.set_home_position(
        10,
        20,
        30
    )

    print(
        "New Home =",
        iai_service.get_home_position()
    )

    # ==========================================================
    # UPDATE LIMIT
    # ==========================================================
    print("\n===== UPDATE LIMIT X =====")

    iai_service.set_limit_x(
        0,
        500
    )

    print(
        "LIMIT X =",
        config.limit_x_min,
        "->",
        config.limit_x_max
    )

    print("\n===== DONE =====")


if __name__ == "__main__":
    main()