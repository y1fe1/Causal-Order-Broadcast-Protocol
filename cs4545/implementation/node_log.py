import logging
import csv

import asyncio

from enum import Enum
from pathlib import Path
from typing import Dict, Literal
from datetime import datetime

class LOG_LEVEL(Enum):
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    WARNING = logging.WARNING
    ERROR = logging.ERROR

class delivered_msg_info : 
    def __init__(self):
        self.start_time: float = None  # Initialize as None to indicate it's unset
        self.end_time: float = None
        self.latency: float = 0.0
        self.is_delivered: bool = False
        self.recieved_msg_cnt: int = 0

class OutputMetrics:
    total_node_count: int = 0
    total_byzantine_count: int = 0
    total_connectivity: int = 0

    delivered_info: Dict[int, delivered_msg_info]
    delivered_msg_cnt: int = 0
    message_recieved: int
    byte_sent: int = 0

    def __init__(self, curAlgorithm:"DistributedAlgorithm" = None): #use forward declaration to make compiler happy (avoid circular import)
        
        if curAlgorithm:
            self.total_node_count = curAlgorithm.N 
            self.total_byzantine_count = curAlgorithm.f
            self.total_connectivity = curAlgorithm.connectivity

        self.delivered_info = {}
    
    def msg_summary_toString(self):

        msg_summary_list = [
            f"Msg {msg_id}: Start Time={info.start_time}, End Time={info.end_time}, "
            f"Latency={info.latency}, Is Delivered={info.is_delivered}, "
            f"Received Msg Count={info.recieved_msg_cnt}"   
            for msg_id, info in self.delivered_info.items()
        ]

        return msg_summary_list


class message_logger:
    def __init__(self, node_id, log_file_path: Path, outputMetrics: OutputMetrics, msg_log_level = LOG_LEVEL.DEBUG):

        self.node_id = node_id
        self.log_metrics = outputMetrics
        self.log_file_path = log_file_path
        self.logger = logging.getLogger(f'NodeLog-{self.node_id}')
        self.logger.setLevel(msg_log_level.value)

        self.file_handler = logging.FileHandler(self.log_file_path)
        if isinstance(msg_log_level, LOG_LEVEL):
            level = msg_log_level.value
        else:
            level = LOG_LEVEL.INFO.value
        self.file_handler.setLevel(level)

        formatter = logging.Formatter('%(message)s')
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

    def update_log_path(self, log_file_path):
        # Close the current file handler to release the file
        self.file_handler.close()
        # Remove the old file handler from the logger
        self.logger.removeHandler(self.file_handler)

        # Set the new log file path
        self.log_file_path = log_file_path
        
        log_dir = self.log_file_path.parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True) 

        # Create a new file handler with the updated path
        self.file_handler = logging.FileHandler(self.log_file_path)
        self.file_handler.setLevel(self.logger.level)  # Retain the current log level

        # Reapply the formatter
        formatter = logging.Formatter('%(message)s')
        self.file_handler.setFormatter(formatter)

        # Add the new file handler to the logger
        self.logger.addHandler(self.file_handler)

    def log(self, level, msg):

        log_entry = f'{self.node_id} | {level} | {msg}'

        if level == LOG_LEVEL.INFO:
            self.logger.info(log_entry)
        elif level == LOG_LEVEL.DEBUG:
            self.logger.debug(log_entry)
        elif level == LOG_LEVEL.WARNING:
            self.logger.warning(log_entry)
        elif level == LOG_LEVEL.ERROR:
            self.logger.error(log_entry)
        else:
            raise ValueError(f"Unknown log level: {level}")
    
    def get_deliver_info_msg(self,msg_id) -> delivered_msg_info: 
        return self.log_metrics.delivered_info.setdefault(msg_id,delivered_msg_info())

    def set_metric_start_time(self, msg_id):
        if not self.get_deliver_info_msg(msg_id).start_time:
            self.get_deliver_info_msg(msg_id).start_time = datetime.now()

    def set_metric_end_time(self,msg_id):
        self.get_deliver_info_msg(msg_id).end_time = datetime.now()
        self.get_deliver_info_msg(msg_id).latency = self.get_deliver_info_msg(msg_id).start_time - self.get_deliver_info_msg(msg_id).end_time

    def set_metric_delivered_status(self,msg_id, status=True):
        self.log_metrics.delivered_msg_cnt += 1
        self.get_deliver_info_msg(msg_id).is_delivered = True

    def log_message_cnt(self, msg_id): 
        self.get_deliver_info_msg(msg_id).recieved_msg_cnt += 1
    
    def set_message_history(self,message_recieved, byte_sent):
        self.log_metrics.message_recieved = message_recieved
        self.log_metrics.byte_sent = byte_sent

    def metric_summary_toString(self):
        return (
            f"{self.node_id},{self.log_metrics.total_node_count},"
            f"{self.log_metrics.total_byzantine_count},{self.log_metrics.total_connectivity},"
            f"{self.log_metrics.delivered_msg_cnt},"
            f"{self.log_metrics.message_recieved},{self.log_metrics.byte_sent}"
        )

    def output_metrics_to_csv(self,metrics_summary) :
        
        csv_output_path = (self.log_file_path.parent
                           / f"{self.log_file_path.stem}.csv")
        
        metrics_list = [item.strip() for item in metrics_summary.split(",")]

        header = [
            "node_id",
            "node_count",
            "byzantine_count",
            "connectivity",
            "delivered_msg_cnt",
            "message_recieved",
            "msg_complexity"
        ]

        is_file_exist = csv_output_path.exists() and csv_output_path.stat().st_size > 0
        
        with open(csv_output_path, "a") as csv_output:

            writer = csv.writer(csv_output)

            if not is_file_exist:
                writer.writerow(header)
            
            writer.writerow(metrics_list)

        self.log(LOG_LEVEL.DEBUG, f"Node {self.node_id} outputs to CSV File {csv_output_path}")
    
    # Write the log output to files \ this should occure every time a deliver event is triggered?
    def flush(self):

        msg_summary_list = self.log_metrics.msg_summary_toString()

        for msg_summary in msg_summary_list:
            self.log(LOG_LEVEL.DEBUG, msg_summary)   

        metrics_summary = self.metric_summary_toString()

        self.log(LOG_LEVEL.INFO, metrics_summary)

        self.file_handler.flush()
        self.output_metrics_to_csv(metrics_summary)

