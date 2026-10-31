import cv2
import numpy as np


def crop_image(
    image: np.ndarray,
    x: int,
    y: int,
    width: int,
    height: int
) -> np.ndarray:
    """Crop ảnh theo tọa độ góc trên bên trái.
    Args:
        image: Ảnh đầu vào.
        x: Tọa độ X.
        y: Tọa độ Y.
        width: Chiều rộng vùng crop.
        height: Chiều cao vùng crop.
    Returns:
        np.ndarray: Ảnh sau khi crop.
    """
    h, w = image.shape[:2]

    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))

    x2 = min(x + width, w)
    y2 = min(y + height, h)

    return image[y:y2, x:x2]
def center_to_box(
    x: int,
    y: int,
    width: int,
    height: int
) -> tuple[int, int, int, int]:
    """Chuyển tọa độ tâm thành hai góc.
    Args:
        x: Tọa độ tâm X.
        y: Tọa độ tâm Y.
        width: Chiều rộng.
        height: Chiều cao.
    Returns:
        tuple[int, int, int, int]: (x1, y1, x2, y2)
    """
    x1 = x - width // 2
    y1 = y - height // 2

    x2 = x + width // 2
    y2 = y + height // 2

    return x1, y1, x2, y2

def main():
    image = cv2.imread(r"c:\Users\anhuv\Desktop\train\yolo_object_hinh_vuong_iner_hinh_vuong\img_train\0_copy (29).jpg")

    if image is None:
        print("Không tìm thấy ảnh image.jpg")
        return

    x = int(input("Nhập x: "))
    y = int(input("Nhập y: "))
    width = int(input("Nhập width: "))
    height = int(input("Nhập height: "))
    x1, y1, x2, y2 = center_to_box(x,y,width=width,height=height)
    print("(p1,p2)",x1,y1,x2,y2)
    crop = crop_image(
        image=image,
        x=x,
        y=y,
        width=width,
        height=height
    )

    cv2.imwrite("crop.jpg", crop)

    cv2.imshow("Original", image)
    cv2.imshow("Crop", crop)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

# kq: 300 400 1100 1200