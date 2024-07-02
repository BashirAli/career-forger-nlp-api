import json
import logging
import logging.config

from os import path
from typing import Any
from pythonjsonlogger import jsonlogger
from fastapi import Request

from configuration.env import settings
from configuration.logger_config import logger_config


def configure_logger():
    current_dir = path.dirname(path.abspath(__file__))
    parent_dir = path.dirname(current_dir)
    logging_ini_path = path.join(parent_dir, "resources", "logging.ini")
    logging.config.fileConfig(logging_ini_path, disable_existing_loggers=False)
    current_log_factory = logging.getLogRecordFactory()

    def log_record_factory(*args, **kwargs):
        record = current_log_factory(*args, **kwargs)
        record.serviceName = settings.api_name
        # record.version = settings.api_major_version
        return record

    logging.setLogRecordFactory(log_record_factory)

    return logging.getLogger(settings.api_name)


class StackdriverJsonFormatter(jsonlogger.JsonFormatter, object):
    """Class that adds log fields required for stackdriver to display messages correctly"""

    def process_log_record(self, log_record):
        log_record["severity"] = log_record["levelname"]
        del log_record["levelname"]
        return super(StackdriverJsonFormatter, self).process_log_record(log_record)


class CustomLoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger: logging.Logger, extras):
        super().__init__(logger, extras)
        self.ctx = logger_config.context

    def process(self, msg: Any, kwargs: dict):
        """
        Add a prefix to each log message and any additional information
        """
        entry = dict(
            product=settings.api_name,
            message=msg,
            context=self.ctx.get(),
            **kwargs.get("additional_info", {})
        )
        return json.dumps(entry), {}

