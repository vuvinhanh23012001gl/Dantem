class ValidateCaptureProduct:
    @staticmethod
    def validate_erase_item_img(id, face_id, point_id):
        try:
            id = int(id)
            face_id = int(face_id)
            point_id = int(point_id)
            return id >= 0 and face_id >= 0 and point_id >= 0
        except (ValueError, TypeError):
            return False
        
    @staticmethod
    def validate_erase_face(id, face_id):
        try:
            id = int(id)
            face_id = int(face_id)
            return id >= 0 and face_id >= 0 
        except (ValueError, TypeError):
            return False

    validate_erase_frame = validate_erase_face
