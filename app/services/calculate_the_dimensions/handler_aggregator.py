import threading

class ProductAggregator:
    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        self.expected_length = None
        self.received_indexes = set()
        self.arr_status = []

    def add_frame(self, index, status_frame, length):
        """
        Trả về:
            None -> chưa đủ frame
            True/False -> đã đủ frame, trả về kết quả sản phẩm
        """
        with self._lock:

            # set tổng số frame nếu chưa có
            if self.expected_length is None and length is not None:
                self.expected_length = length

            # lưu frame
            if index not in self.received_indexes:
                self.received_indexes.add(index)
                self.arr_status.append(status_frame)

            # kiểm tra đủ frame chưa
            if self.expected_length is not None and \
               len(self.received_indexes) == self.expected_length:

                final_status = all(self.arr_status)

                # reset cho sản phẩm tiếp theo
                self.reset()

                return final_status

            return None