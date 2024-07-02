import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator
import pendulum

from fastapi import FastAPI, Request, status, Response, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from configuration.env import settings
from gcp.pubsub import PubSubPublisher
from gcp.secret import SecretManager
from core.api import build_hello_world
from configuration.logger_config import logger_config
from service.logger import CustomLoggerAdapter, configure_logger
from service import dependencies
from helper.utils import decode_pubsub_message_data, extract_trace_and_request_type, format_pydantic_validation_error_message, create_pydantic_validation_error_message
from error.custom_exceptions import (
    ManualDLQError,
    InternalAPIException,
    PubsubPublishException,
    PubsubReprocessError,
    DatastoreGenericError,
    DatastoreNotFoundException,
    ModelValidationError,
    DatastoreMultiResultException,
    InternalAPIException
)
from pydantic_model.api_model import (
    Message,
    StatusLog,
    ErrorResponse,
    LogStatus,
    GCPTemplateResponse,
    GCPTemplateRequest
)

logger = CustomLoggerAdapter(configure_logger(), None)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    if settings.is_test_env:
        keys = ""
    else:
        sm_client = SecretManager()
        keys = sm_client.get_secret(settings.key_secret_id)
    yield


app = FastAPI(title=settings.api_name, lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"Status": "OK"}

### ### ### ### ### ### PubSub Subscriber ### ### ### ### ### ### ### ###
@app.post("/")
def pubsub_subscriber(request: Message, original_request: Request) -> JSONResponse:

    # set request contexts
    ctx_fields = extract_trace_and_request_type(original_request=original_request)
    original_request = request.model_dump()
    original_request["message"]["data"] = json.loads(
        decode_pubsub_message_data(original_request["message"]["data"], strict=False)
    )
    logger_config.set_request_contexts(
        ctx_fields=ctx_fields, original_request=original_request
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "Success",
            "pubsub_message_id": request.message.message_id,
            "pubsub_publish_timestamp": request.message.publish_time,
            "acknowledge_timestamp": str(pendulum.now("Europe/London")),
        },
    )

### ### ### ### ### ### Consumer API ### ### ### ### ### ### ### ###
@app.post("/v1/hello_world")
def gcp_template_response(
        request: GCPTemplateRequest,
        headers: dependencies.HeaderParams = Depends(dependencies.HeaderParams)
):

    response = build_hello_world(request.data)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content= {
            "status": "Success",
            "response": response,
        },
    )



@app.exception_handler(RequestValidationError)
async def api_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """In the event of an invalid request payload, we want to return a 2xx code to stop the api to retry
    on broken paylaods - so we're sending the data to pubsub"""
    validation_exception = format_pydantic_validation_error_message(exc.errors())
    http_response_dict = ErrorResponse(
        exception="Request Validation Error", detail=validation_exception
    ).model_dump(exclude_none=True)
    logger.info(
        msg="Request Validation Error Occurred", additional_info=http_response_dict
    )
    try:
        # Handling messages that needs to be sent to DLQ manually
        pubsub_publisher = PubSubPublisher(
            project_id=settings.gcp_project_id, topic=settings.dlq_topic
        )
        pubsub_publisher.publish(
            data=json.loads(
                decode_pubsub_message_data(
                    exc.body["message"].get("data"), strict=False
                )
            ),
            source_message_uuid=exc.body["message"].get("message_id"),
            source_publish_time=exc.body["message"].get("publish_time"),
        )
    except PubsubPublishException as pb:
        http_response_dict = ErrorResponse(
            exception="Pubsub Publish Error", detail=str(pb)
        ).model_dump(exclude_none=True)
        logger.info(
            msg=f"PubsubPublishException Error Occurred: {str(pb)}",
            additional_info=http_response_dict,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=http_response_dict,
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content=http_response_dict
    )


@app.exception_handler(ManualDLQError)
async def dead_letter_queue_exception_handler(
    request: Request, exc: ManualDLQError
):
    """Publishing to DLQ Manually in the event the api fails to do stuff with the request payload -
    instead of retrying/failing over and over"""
    try:
        pubsub_message = exc.original_request["message"]
        pubsub_publisher = PubSubPublisher(
            project_id=settings.gcp_project_id, topic=settings.dlq_topic
        )
        pubsub_publisher.publish(
            data=json.loads(
                decode_pubsub_message_data(pubsub_message["data"], strict=False)
            ),
            source_message_uuid=pubsub_message["message_id"],
            source_publish_time=pubsub_message["publish_time"],
        )
    except PubsubPublishException as pb:
        http_response_dict = ErrorResponse(
            exception="Pubsub Publish Error", detail=str(pb)
        ).model_dump(exclude_none=True)
        logger.info(
            msg=f"PubsubPublishException Error Occurred: {str(pb)}",
            additional_info=http_response_dict,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=http_response_dict,
        )

    logger.info(
        msg=f"Unable to process the file - File sent to DLQ.",
        extra_fields=StatusLog(
            message_id=pubsub_message["message_id"],
            status=LogStatus.FAILURE,
            source_bucket_name=pubsub_message["attributes"].get("bucketId", None),
            destination_bucket_name=None,
            error_stage=exc.error_stage,
            error_desc=exc.error_desc,
            response_status_code="202",
            log_timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        ).model_dump(),
    )
    http_response_dict = ErrorResponse(
        exception="ManualDLQError", detail=str(exc.error_desc)
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content=http_response_dict
    )


@app.exception_handler(PubsubReprocessError)
async def reprocess_message_exception_handler(
    request: Request, exc: PubsubReprocessError
):
    """Function to handle reprocess error"""
    logger.error(
        msg=f"Unable to process the message due to internal server error - Message "
        f" will be retried"
    )

    logger.info(
        msg=f"Unable to process the message - Message will be retried",
        extra_fields=StatusLog(
            message_id=exc.original_request["message"]["message_id"],
            status=LogStatus.RETRY,
            source_bucket_name=exc.original_request["message"]["attributes"].get(
                "bucketId", None
            ),
            destination_bucket_name=None,
            error_stage=exc.error_stage,
            error_desc=exc.error_desc,
            response_status_code="500",
            log_timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        ).model_dump(),
    )

    http_response_dict = ErrorResponse(
        exception="PubsubReprocessError", detail=str(exc.error_desc)
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=http_response_dict
    )

@app.exception_handler(ModelValidationError)
async def validation_exception_handler(request: Request, exc: ModelValidationError):
    logger.error(msg="ModelValidation Error Occurred")
    validation_exception = create_pydantic_validation_error_message(str(exc))
    http_response = ErrorResponse(exception="Request Validation Error Occurred", detail=validation_exception)
    http_response_dict = http_response.dict(exclude_none=True)
    logger.info(msg=http_response_dict)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=http_response_dict
    )


@app.exception_handler(DatastoreGenericError)
async def validation_exception_handler(request: Request, exc: DatastoreGenericError):
    logger.error(msg="DatastoreGeneric Error Occurred")
    http_response = ErrorResponse(exception="Datastore Error", detail=str(exc))
    http_response_dict = http_response.dict(exclude_none=True)
    logger.info(msg=http_response_dict)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=http_response_dict
    )


@app.exception_handler(DatastoreNotFoundException)
async def validation_exception_handler(request: Request, exc: DatastoreNotFoundException):
    logger.error(msg="DatastoreNotFound Error Occurred")
    http_response = ErrorResponse(errorCode="1001", exception="NotFound Error", detail=str(exc))
    http_response_dict = http_response.dict(exclude_none=True)
    logger.info(msg=http_response_dict)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=http_response_dict
    )


@app.exception_handler(DatastoreMultiResultException)
async def validation_exception_handler(request: Request, exc: DatastoreMultiResultException):
    logger.error(msg="DatastoreMultiResult Exception Occurred")
    http_response = ErrorResponse(errorCode="2001", exception="Multi Search Results Error", detail=str(exc))
    http_response_dict = http_response.dict(exclude_none=True)
    logger.info(msg=http_response_dict)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=http_response_dict
    )


@app.exception_handler(InternalAPIException)
async def validation_exception_handler(request: Request, exc: InternalAPIException):
    # Log the actual error but return a generic response to the consumer
    logger.error(msg=f"InternalAPI Exception Occurred: {str(exc)}")
    http_response = ErrorResponse(exception="Internal Error Occurred", detail="Internal Error Occurred")
    http_response_dict = http_response.dict(exclude_none=True)
    logger.info(msg=http_response_dict)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=http_response_dict
    )