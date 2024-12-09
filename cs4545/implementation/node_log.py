import logging
import csv

import asyncio

from enum import Enum
from pathlib import Path
from typing import Dict, Literal
from cs4545.system.da_types import DistributedAlgorithm

class LOG_LEVL(Enum):
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

    def __init__(self, curAlgorithm:DistributedAlgorithm):
        
        self.total_node_count = curAlgorithm.N 
        self.total_byzantine_count = curAlgorithm.f
        self.total_connectivity = curAlgorithm.connectivity

        self.message_count = 0
        

class message_logger:
    def __init__(self, node_id, msg_log_level = LOG_LEVL.DEBUG, log_file_path: Path, outputMetrics: OutputMetrics):

        self.node_id = node_id
        self.outputMetrics = outputMetrics
        self.log_file = log_file_path
        self.logger = logging.getLogger(f'NodeLog-{self.node_id}')
        self.logger.setLevel(msg_log_level.value)

        self.file_handler = logging.FileHandler(self.log_file)
        self.file_handler.setLevel(msg_log_level.value)

        formatter = logging.Formatter('%(message)s')
        self.file_handler.setFormatter(formatter)

        self.logger.addHandler(self.file_handler)
        self.log_metrics = outputMetrics

    def log(self, level, msg):

        log_entry = f'{self.node_id} | {level} | {msg}'

        if level == LOG_LEVL.INFO:
            self.logger.info(log_entry)
        elif level == LOG_LEVL.DEBUG:
            self.logger.debug(log_entry)
        elif level == LOG_LEVL.WARNING:
            self.logger.warning(log_entry)
        elif level == LOG_LEVL.ERROR:
            self.logger.error(log_entry)
        else:
            raise ValueError(f"Unknown log level: {level}")
        
    async def output_metrics_to_csv(self,metrics_summary) :
        
        csv_output_path = (self.algorithm_output_file.parent
                           / f"{self.algorithm_output_file.stem}-{self.node_id}.csv")
        
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

        is_file_exist = csv_output_path.exist() and csv_output_path.stat().st_size > 0
        
        async with open(f'csv_output_file', "a") as csv_output:

            writer = csv.writer(await csv_output)

            if not is_file_exist:
                await writer.writerow(header)
            
            await writer.writerow(metrics_list)
            
    # Write the log output to files \ this should occure every time a deliver event is triggered?
    async def flush(self):

        metrics_summary = f"{self.node_id},\
                 {self.log_metrics.node_count},\
                 {self.log_metrics.byzantine_count},\
                 {self.log_metrics.connectivity},\
                 {self.log_metrics.delivered_msg_cnt},\
                 {self.log_metrics.latency:.3f},\
                 {self.log_metrics.message_count - self.log_metrics.last_message_count}"
    
        self.log(LOG_LEVL.INFO, metrics_summary)

        await self.file_handler.flush()
        await self.output_metrics_to_csv(metrics_summary)

