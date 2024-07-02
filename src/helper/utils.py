import base64
import binascii
import time
import io
import json
from typing import Sequence
from functools import wraps

from fastapi import Request
from pydantic_core import ValidationError

from configuration.env import settings
from configuration.logger_config import logger_config
from error.custom_exceptions import ManualDLQError, MessageDecodeError, MessageValidationError

from gcp.gcs import GoogleCloudStorage
from pydantic_model.api_model import ErrorEnum
from service.logger import CustomLoggerAdapter, configure_logger

logger = CustomLoggerAdapter(configure_logger(), None)

def format_pydantic_validation_error_message(pydantic_exception: Sequence) -> str:
    exceptions_list = []
    for exception in pydantic_exception:
        parameter = exception["loc"][-1]
        message = exception["msg"]
        exceptions_list.append({"parameter": parameter, "reason": message})
    return f"The following request parameters failed validation: {str(exceptions_list)}"

def create_pydantic_validation_error_message(pydantic_exception: str) -> str: 
    exceptions_list = []
    pydantic_exception = pydantic_exception.split("\n")
    pydantic_exception.pop(0)
    # exceptions come in pairs, if the length is an odd number then there is unneeded metadata that can be discarded
    if len(pydantic_exception) % 2 != 0:
        pydantic_exception.pop()

    for i in range(0, len(pydantic_exception), 2):
        exceptions_list.append(
            (pydantic_exception[i], pydantic_exception[i + 1].strip())
        )

    return (
        f"The following request parameters failed validation: {exceptions_list}"
    )

def decode_pubsub_message_data(data, strict=True) -> str:
    try:
        return base64.b64decode(data).decode("utf-8").strip()
    except TypeError as te:
        if isinstance(data, dict):
            logger.info(f"PubSub message data was not encoded.")
            return json.dumps(data)
        elif not strict:
            return json.dumps(data)
        else:
            raise MessageDecodeError(
                f"Unknown DataType for PubSub message data - unable to decode. {te}"
            )
    except binascii.Error as be:
        raise MessageDecodeError(f"Pubsub Message Data Base64 error: {be}")
    except UnicodeDecodeError as ude:
        raise MessageDecodeError(f"Pubsub Message Data Decoding error: {ude}")


def read_validate_message_data(request, pydantic_model):
    try:
        message_data = pydantic_model(
            **json.loads(decode_pubsub_message_data(request.message.data))
        )
        logger.info(f"Data Decoded {message_data.model_dump()}")
        return message_data
    except json.decoder.JSONDecodeError as jse:
        logger.error(msg=dict(exception=str(jse.msg)))
        raise ManualDLQError(
            original_request=logger_config.context.get().get("original_request"),
            error_desc=str(jse.msg),
            error_stage=ErrorEnum.MESSAGE_VALIDATION,
        )
    except MessageValidationError as mve:
        logger.error(msg=dict(exception=str(mve)))
        raise ManualDLQError(
            original_request=logger_config.context.get().get("original_request"),
            error_desc=str(mve),
            error_stage=ErrorEnum.MESSAGE_VALIDATION,
        )
    except ValidationError as ve:
        logger.error(logger_config.context.get().get("original_request"))
        validation_exception = create_pydantic_validation_error_message(str(ve))
        logger.error(msg=dict(exception=str(validation_exception)))
        raise ManualDLQError(
            original_request=logger_config.context.get().get("original_request"),
            error_desc=validation_exception,
            error_stage=ErrorEnum.MESSAGE_VALIDATION,
        )

def extract_trace_and_request_type(original_request: Request) -> dict:
    ctx_required_fields = {}
    # X-Cloud-Trace-Context is for GCP tracing to work
    trace_header = original_request.headers.get("X-Cloud-Trace-Context")
    if trace_header and settings.gcp_project_id:
        trace = trace_header.split("/")
        ctx_required_fields[
            "logging.googleapis.com/trace"
        ] = f"projects/{settings.gcp_project_id}/traces/{trace[0]}"

    ctx_required_fields["requestType"] = original_request.scope["path"]
    return ctx_required_fields


