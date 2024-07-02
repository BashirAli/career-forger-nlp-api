from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field

from configuration.env import settings


class ErrorEnum(str, Enum):
    MESSAGE_VALIDATION = "MESSAGE_VALIDATION"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    GOOGLE_API_ERROR = "GOOGLE_APR_ERROR"
    ENCRYPTION = "ENCRYPTION_ERROR"
    INPUT_FILE_NAME = "INPUT_FILE_NAME_ERROR"
    UPLOAD_TO_GCS = "UPLOAD_TO_GCS"
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
    destination_bucket_name: Optional[str] = None
    error_stage: str = None
    error_desc: str = None
    response_status_code: str
    log_timestamp: str
    log_type: str = "ENCRYPTOR_LOG"


class GcsToPubsubEvent(BaseModel):
    kind: Optional[str] = Field(None, description="kind of object received")
    id: Optional[str] = Field(None, description="full path and id of file received")
    selfLink: Optional[str] = Field(None, description="link to the file received")
    name: str = Field(..., description="file path")
    bucket: str = Field(..., description="name of the storage bucket")
    generation: Optional[str] = None
    metageneration: Optional[str] = None
    contentType: Optional[str] = Field(None, description="kind of file receive")
    timeCreated: Optional[str] = Field(None, description="time the object was created")
    updated: Optional[str] = Field(None, description="time the object was updated")
    storageClass: Optional[str] = Field(None, description="storage class")
    timeStorageClassUpdated: Optional[str] = Field(
        None, description="time that storage class was updated"
    )
    size: Optional[str] = None
    md5Hash: Optional[str] = None
    mediaLink: Optional[str] = None
    crc32c: Optional[str] = None
    etag: Optional[str] = None


class PubSubMessage(BaseModel):
    data: Union[bytes, Dict[str, Any]] = Field(...)
    attributes: Dict[str, Any] = Field(...)
    message_id: str = Field(...)
    publish_time: str = Field(...)


class Message(BaseModel):
    message: PubSubMessage



class GCPTemplateResponse(BaseModel):
    response_message: Optional[str] = Field(None,
                                 description='Response message built',
                                 example=''
    )


class RequestBody(BaseModel):
    message_id: Optional[str] = Field(
        None,
        description='',
        example='',
    )
    message: Optional[str] = Field(
        None,
        description='',
        example='',
    )

class GCPTemplateRequest(BaseModel):
    data: Optional[RequestBody] = None
