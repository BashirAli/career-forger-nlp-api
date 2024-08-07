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
    "date_sent": "Thu, 1 Apr 2021 12:00:00 +0000",
    "sender": "sender@example.com",
    "recipient": "recipient@example.com",
    "title": "Test Email",
    "content_type": "text/plain",
    "content": "Your technical skills are impressive, especially your proficiency in Python and algorithms. However, "
               "there is room for improvement in your knowledge of machine learning algorithms and data structures. "
               "In non-technical aspects, your communication skills are excellent, and you work well in teams. "
               "However, sometimes you struggle with time management and meeting deadlines, which can affect project "
               "timelines. You might want to focus on developing your project management skills and improving your "
               "ability to prioritise tasks effectively. Your involvement in extracurricular activities, such as the "
               "coding club and volunteering for community projects, is commendable. You showed remarkable leadership "
               "during the last project, but there were instances where you could have delegated tasks more "
               "efficiently. For career advice, I suggest you keep honing your public speaking skills and seek "
               "opportunities for mentorship to further enhance your leadership abilities."
}


class EmailInfo(BaseModel):
    date_sent: str = Field(..., description='date sent')
    sender: str = Field(..., description='email sender')
    recipient: str = Field(..., description='email reciever')
    title: str = Field(..., description='email title')
    content_type: Optional[str] = None
    content: str = Field(..., description='email content')
