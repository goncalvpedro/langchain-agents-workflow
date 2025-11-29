"""
Structured JSON Logging Configuration for Observability
Outputs logs compatible with Grafana Loki
"""

import logging
import sys
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds service metadata
    and ensures consistent field naming for Loki parsing
    """
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['service'] = 'genesis_pipeline'
        log_record['logger'] = record.name
        
        # Add custom fields if they exist
        if hasattr(record, 'agent'):
            log_record['agent'] = record.agent
        if hasattr(record, 'execution_time'):
            log_record['execution_time'] = record.execution_time
        if hasattr(record, 'tokens_used'):
            log_record['tokens_used'] = record.tokens_used
        if hasattr(record, 'status'):
            log_record['status'] = record.status


def setup_logger(name: str = "genesis") -> logging.Logger:
    """
    Configure and return a structured JSON logger
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(service)s %(logger)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
logger = setup_logger()


def log_agent_execution(
    agent_name: str,
    execution_time: float,
    tokens_used: int,
    status: str,
    message: str = ""
):
    """
    Utility function to log agent execution with consistent structure
    
    Args:
        agent_name: Name of the agent
        execution_time: Time taken in seconds
        tokens_used: Number of tokens consumed
        status: 'success', 'error', or 'running'
        message: Optional additional message
    """
    logger.info(
        message or f"Agent {agent_name} execution completed",
        extra={
            'agent': agent_name,
            'execution_time': execution_time,
            'tokens_used': tokens_used,
            'status': status
        }
    )