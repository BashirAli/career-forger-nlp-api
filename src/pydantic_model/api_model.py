from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field

from configuration.env import settings


class ErrorEnum(str, Enum):
    MESSAGE_VALIDATION = "MESSAGE_VALIDATION"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    GOOGLE_API_ERROR = "GOOGLE_APR_ERROR"
    INPUT_FILE_NAME = "INPUT_FILE_NAME_ERROR"
    EMAIL_NLP = "EMAIL_NLP_ANALYSIS_ERROR"
    PUSH_TO_PUBSUB = "PUSH_TO_PUBSUB"
    SENDING_TO_DLQ = "SENDING_TO_DLQ"


class ErrorResponse(BaseModel):
    exception: str = Field(..., description="exception")
    detail: str = Field(..., description="error message")


class LogStatus(str, Enum):
    """Allowed Status messages for Log Status"""
    SUCCESS = "Success"
    FAILURE = "Failure"
    RETRY = "Retry"


class StatusLog(BaseModel):
    """Log Message for API Status"""
    project_id: str = settings.gcp_project_id
    message_id: Optional[str] = None
    status: LogStatus
    source_bucket_name: Optional[str] = None
    error_stage: str = None
    error_desc: str = None
    response_status_code: str
    log_timestamp: str


class PubSubMessage(BaseModel):
    data: Union[bytes, Dict[str, Any]] = Field(...)
    attributes: Dict[str, Any] = Field(...)
    message_id: str = Field(...)
    publish_time: str = Field(...)


class Message(BaseModel):
    message: PubSubMessage


x = {
        'date_sent': 'Thu, 1 Apr 2021 12:00:00 +0000',
        'sender': 'sender@example.com',
        'recipient': 'recipient@example.com',
        'title': 'Test Email',
        'content_type': 'text/plain',
        'content': 'This is the body of the email.'
    }
class EmailInfo(BaseModel):
    date_sent: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    title: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = None
