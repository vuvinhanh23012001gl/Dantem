# from pathlib import Path
# import sys
# # import cv2
# sys.path.append(str(Path(__file__).resolve().parents[3]))
# from pathlib import Path
# from handler_model import ModelHandler
# import config_detect
# from app.storage.config import PATH_FILE_UNET_DETECT_WELD_LINE

import math
import cv2
class FaceHandlers: 
    # Lớp này tính toán cho 1 búc ảnh thôi 
    def __init__(self,img,polygons, regulation_master:list=None, shape = (960,1280), convert_mm = 0.1):
        self.img = img
        self.polygons = polygons
        self.regulation_master = regulation_master
        self.shape = shape 
        self.mm_per_pixel  = convert_mm

    def hex_to_bgr(self,hex_color):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (b, g, r)


    def draw_line(self, line):
        h, w = self.img.shape[:2]
        x1 = line["PointStarX"]
        y1 = line["PointStarY"]
        x2 = line["PointEndX"]
        y2 = line["PointEndY"]
        # ===== Scale theo self.shape =====
        if self.shape is not None:
            reg_h, reg_w = self.shape
            if (reg_h, reg_w) != (h, w):
                scale_x = w / reg_w
                scale_y = h / reg_h
                x1 = int(x1 * scale_x)
                y1 = int(y1 * scale_y)
                x2 = int(x2 * scale_x)
                y2 = int(y2 * scale_y)
        # ===== Màu =====
        line_color = self.hex_to_bgr(line.get("color", "#b8d828"))
        text_color = self.hex_to_bgr(line.get("point_color", "#ffffff"))

        # ===== Vẽ line + điểm =====
        cv2.line(self.img, (x1, y1), (x2, y2), line_color, 2)
        cv2.circle(self.img, (x1, y1), 6, line_color, -1)
        cv2.circle(self.img, (x2, y2), 6, line_color, -1)
        name = line.get("name", "")
        if not name:
            return self.img

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        (text_w, text_h), baseline = cv2.getTextSize(name, font, font_scale, thickness)

        # ===== Đặt chữ gần điểm bắt đầu =====
        offset = 10  # khoảng cách cách điểm tròn
        text_x = x1 + offset
        text_y = y1 - offset

        # Giữ trong khung ảnh
        text_x = max(0, min(text_x, w - text_w))
        text_y = max(text_h, min(text_y, h))

        cv2.putText(
            self.img,
            name,
            (text_x, text_y),
            font,
            font_scale,
            text_color,
            thickness,
            cv2.LINE_AA
        )


    def draw_polygon(self,
            color=(0, 255, 0),
            thickness=2,
            draw_points=True,
            point_color=(0, 0, 255),
            point_radius=4
        ):
            """
            Vẽ polygon lên ảnh
            Parameters:
                image (np.ndarray): Ảnh gốc (BGR)
                polygon (np.ndarray): Polygon từ approxPolyDP (N,1,2)
                color (tuple): Màu vẽ polygon (BGR)
                thickness (int): Độ dày đường
                draw_points (bool): Có vẽ điểm đỉnh hay không
                point_color (tuple): Màu điểm đỉnh
                point_radius (int): Bán kính điểm đỉnh
            Returns:
                np.ndarray: Ảnh đã vẽ
            """
            # Vẽ polygon (đường bao)
            cv2.polylines(
                self.img,
                [self.polygons],
                isClosed=True,
                color=color,
                thickness=thickness
            )
            # Vẽ từng đỉnh
            if draw_points:
                for p in self.polygons:
                    x, y = p[0]
                    cv2.circle(self.img, (int(x), int(y)), point_radius, point_color, -1)


    def judment_frame(self):
        frame_ok =  True
        arr_line = []
        if not self.regulation_master or self.polygons is None or len(self.polygons) == 0:
            print("Không có dữ liệu phán định")
            return False,arr_line,self.img
        self.draw_polygon()
        for line in self.regulation_master:
                self.draw_line(line)
                x1, y1 = line["PointStarX"],line["PointStarY"]
                x2, y2 = line["PointEndX"],line["PointEndY"]
                name = line["name"]
                point_color = self.hex_to_bgr(line.get("color", "#b8d828"))
                status , line_intersec  = self.line_intersect_polygon((x1,y1),(x2,y2))
                quantity_point  = len(line_intersec)
                if status:
                    # print("line_intersec",line_intersec)
                    level_current = 0
                    self.draw_intersections(line_intersec,point_color)
                    distance_reality = self.distance_px_to_mm(line_intersec[0],line_intersec[1])
                    level_1 = line["level1"]
                    level_2 = line["level2"]
                    level_3 = line["level3"]
                    level_4 = line["level4"]
                    if 0 <=  distance_reality < level_1:
                            frame_ok = False
                            print("NG mức level 1")
                            level_current = 1
                    elif  level_1 <=  distance_reality < level_2:
                            frame_ok = False
                            print("NG mức level 2")
                            level_current = 2
                    elif  level_2 <=  distance_reality < level_3:
                            frame_ok = False
                            print("NG mức level 3")
                            level_current = 3
                    elif  level_3 <=  distance_reality < level_4:
                            print("ok mức level 4 ")
                            level_current = 4
                    else:
                        frame_ok = False
                        level_current = 5
                        print("Vượt quá kích thước quy định")
                    arr_line.append({"name_line":name,"width":distance_reality,"level":level_current,"status":status})
                    print(f"Đường thẳng {name} có 2 điểm cắt polygon")
                    print("Khoảng cách pixel thực tế là:",distance_reality)
                elif (quantity_point == 1):
                    print(f"Đường thẳng {name} chỉ có 1 đường giao")
                    self.draw_intersections(line_intersec,point_color)
                    frame_ok = False
                elif (quantity_point == 0):
                    frame_ok = False
                    print(f"Đường thẳng {name} kông có đường giao")
                elif (quantity_point > 2):
                    frame_ok = False
                    self.draw_intersections(line_intersec,point_color)
                    print(f"Đường thẳng {name} có nhiều hơn 2 điểm cắt polygon")
        print("Frame OK :",frame_ok)
        return frame_ok,arr_line,self.img
    

    def draw_intersections(self, points,
                        color=(0, 0, 255),
                        radius=6,
                        thickness=-1,
                        draw_text=True):
        """
        points: list [(x,y), ...]
        """
        for idx, (x, y) in enumerate(points):
            # Vẽ hình tròn
            cv2.circle(self.img, (int(x), int(y)), radius, color, thickness)

            # Nếu muốn ghi tọa độ
            if draw_text:
                text = f"{x},{y}"
                cv2.putText(
                    self.img,
                    text,
                    (int(x)+8, int(y)-8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                    cv2.LINE_AA
                )


    def line_intersect_polygon(self, line_p1, line_p2):
        h, w = self.img.shape[:2]
        x1, y1 = line_p1
        x2, y2 = line_p2
        # ===== Scale giống draw_line =====
        if self.shape is not None:
            reg_h, reg_w = self.shape
            if (reg_h, reg_w) != (h, w):
                scale_x = w / reg_w
                scale_y = h / reg_h
                x1 = int(x1 * scale_x)
                y1 = int(y1 * scale_y)
                x2 = int(x2 * scale_x)
                y2 = int(y2 * scale_y)

        line_p1_scaled = (x1, y1)
        line_p2_scaled = (x2, y2)
        intersections = []
        # ⚠ polygon của bạn có dạng (N,1,2)
        polygon = self.polygons.reshape(-1, 2)
        n = len(polygon)
        for i in range(n):
            p3 = tuple(polygon[i])
            p4 = tuple(polygon[(i + 1) % n])
            hit, point = self._line_segment_intersection(
                line_p1_scaled, line_p2_scaled, p3, p4
            )
            if hit:
                intersections.append(point)
        len_data  = len(intersections)
        if  len_data == 2:
            return True,intersections
        return False,intersections

        
    def _line_segment_intersection(self, p1, p2, p3, p4):
        """
        Kiểm tra 2 đoạn thẳng p1-p2 và p3-p4 có cắt nhau không
        Nếu có trả về tọa độ pixel giao điểm
        """
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
        if denom == 0:
            return False, None  # song song
        # Công thức giao điểm
        px = ((x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)) / denom
        py = ((x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)) / denom

        # Kiểm tra có nằm trên cả 2 đoạn không
        if (min(x1, x2) <= px <= max(x1, x2) and
            min(y1, y2) <= py <= max(y1, y2) and
            min(x3, x4) <= px <= max(x3, x4) and
            min(y3, y4) <= py <= max(y3, y4)):

            return True, (int(px), int(py))
        return False, None
    
    def distance_px_to_mm(self,p1,p2) -> float:
            """
            p1, p2: (x, y) có thể là int hoặc float (subpixel)
            return: khoảng cách mm
            """
            if len(p1) != 2 or len(p2) != 2:
                raise ValueError("Points must be (x, y)")

            dx = float(p2[0]) - float(p1[0])
            dy = float(p2[1]) - float(p1[1])

            dist_px = math.hypot(dx, dy)
            print("So pixellll la",dist_px)
            return dist_px * self.mm_per_pixel
 


# from app.services.product import Choose_Product
# from app.services.product import Manager_Product
# choose_product_current = Choose_Product.get_choose_product_pick()
# status,data,erro = Manager_Product.get_data_regulation_by_product_id(choose_product_current)
# shape = (960,1280)
# Model =  ModelHandler(PATH_FILE_UNET_DETECT_WELD_LINE,config_detect.encoder,img_size= config_detect.img_size,threshold= config_detect.threshold)
# mask  = Model.predict(img) # Loc nhieu ảnh
# mask_clean= Model.clean_mask_opening(mask,config_detect.Kernel) # Loc nhieu xung quanh
# polygon  = Model.find_largest_external_polygon(mask_clean,config_detect.epsilon_ratio,config_detect.min_area)
# for key, value in data.items():
#     if key.isdigit():
#         print("Key:", key)
#         print("Value:", value)
# Frame = FrameHandlers(img,polygon,data["0"],shape)
# Frame = FrameHandlers(img,polygon,data["1"],shape)
# Frame.judment_frame()
# print("regulation",data["0"])   # Lấy phần từ 0
# print("polygon:",polygon)









 
FrameHandlers = FaceHandlers

