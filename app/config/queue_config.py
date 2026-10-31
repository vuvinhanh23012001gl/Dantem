from  dataclasses import dataclass

@dataclass(frozen=True)
class QueueConfig:

    SIZE_QUEUE_MANAGE_LOG = 500
    name_queue_manage  = "manage"
    
    SIZE_QUEUE_LOG_SEND_CLIENT = 500
    name_queue_log_client  = "log_client"


    SIZE_QUEUE_IMG_CAPTURE = 500
    name_queue_process_capture  = "process_capture"


    SIZE_QUEUE_DATA_SEND_CLIENT = 500
    ame_queue_data_client  = "data_send_client"

    SIZE_QUEUE_IMG_CALIBRATION = 201
    name_queue_img_calibration  = "queue_calibration"   

    SIZE_QUEUE_DATA_SEND_MCU = 500
    SIZE_QUEUE_DATA_LISTEN_MCU = 500




