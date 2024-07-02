from __future__ import annotations

from configuration.logger_config import logger_config
from service.logger import CustomLoggerAdapter
from configuration.env import settings
import logging
import hashlib
import json

logger = CustomLoggerAdapter(logging.getLogger(__name__), None)


def build_hello_world(payload_request_details):
    message_id = payload_request_details.message_id
    if not message_id:
        message_id = "default"
    message = payload_request_details.message

    logger.info(
        ctx=logger_config.context,
        msg=f"Using secret manager api key dummy code")

    # dummy_api_key = secret_manager_api_key
    # key_hashed = hashlib.md5(dummy_api_key.encode('utf-8')).hexdigest()

    dummy_api_key = "12345"

    message_id_hashed = hashlib.md5(message_id.encode('utf-8')).hexdigest() + "_" + message_id

    data = {"message": message, "hashed_message_id": message_id_hashed, "secret_manager_key": dummy_api_key}

    response = {"result": data}

    return response
