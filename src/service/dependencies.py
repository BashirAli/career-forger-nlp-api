from fastapi import Header, Request
import datetime
import logging
import contextvars
from service.logger import CustomLoggerAdapter

logger = CustomLoggerAdapter(logging.getLogger(__name__), None)


class HeaderParams:
    """Class holding the custom header details"""

    def __init__(
            self,
            request_id: str = Header(..., min_length=1, max_length=20),
            request_timestamp: datetime.datetime = Header(...)
    ):
        self.request_id = request_id
        self.request_timestamp = request_timestamp
