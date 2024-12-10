import logging
import csv

import asyncio

from enum import Enum
from pathlib import Path
from typing import Dict, Literal

class LOG_LEVEL(Enum):
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    WARNING = logging.WARNING
    ERROR = logging.ERROR

class OutputMetrics:

    total_node_count: int = 0
    total_byzantine_count: int = 0
    total_connectivity: int = 0

    message_count: int = 0
    last_message_count: int = 0
    delivered_msg_cnt: int = 0

    start_time: Dict[int, float] = {}
    end_time: Dict[int, float] = {}

    latency: float = 0.0

    def __init__(self, curAlgorithm:"DistributedAlgorithm" = None): #use forward declaration to make compiler happy (avoid circular import)
        
        if curAlgorithm:
            self.total_node_count = curAlgorithm.N 
            self.total_byzantine_count = curAlgorithm.f
            self.total_connectivity = curAlgorithm.connectivity

        self.message_count = 0
        

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
            "latency",
            "msg_difference"
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

        metrics_summary = f"{self.node_id},{self.log_metrics.total_node_count},{self.log_metrics.total_byzantine_count},{self.log_metrics.total_connectivity},{self.log_metrics.delivered_msg_cnt},{self.log_metrics.latency:.3f},{self.log_metrics.message_count - self.log_metrics.last_message_count}"
    
        self.log(LOG_LEVEL.INFO, metrics_summary)

        self.file_handler.flush()
        self.output_metrics_to_csv(metrics_summary)

