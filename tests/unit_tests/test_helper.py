import json
import os
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from error.custom_exceptions import ManualDLQError, MessageDecodeError
from pydantic_model.api_model import GcsToPubsubEvent, Message, PubSubMessage
from helper.utils import (
    format_pydantic_validation_error_message,
    create_pydantic_validation_error_message,
    decode_pubsub_message_data,
    extract_trace_and_request_type,
    read_validate_message_data,
    remove_file_extension
)

CURRENT_PATH = os.path.dirname(__file__)


def test_decode_pubsub_message_data():
    test_data_decoded = {
        "new_mac": "mac_add1",
        "old_mac": "mac_add2",
        "insert_timestamp": "2014-12-17T09:55:47Z",
    }
    test_data_encoded = b"eyJuZXdfbWFjIjogIm1hY19hZGQxIiwgIm9sZF9tYWMiOiAibWFjX2FkZDIiLCAiaW5zZXJ0X3RpbWVzdGFtcCI6ICIyMDE0LTEyLTE3VDA5OjU1OjQ3WiJ9"
    decoded_test_data = decode_pubsub_message_data(test_data_encoded)
    assert type(decoded_test_data) is str
    assert type(json.loads(decoded_test_data)) is dict
    assert decoded_test_data == json.dumps(test_data_decoded)


def test_decode_pubsub_message_data_already_decoded():
    test_data = {
        "new_mac": "mac_add1",
        "old_mac": "mac_add2",
        "insert_timestamp": "2014-12-17T09:55:47Z",
    }
    decoded_test_data = decode_pubsub_message_data(test_data)
    assert type(decoded_test_data) is str
    assert type(json.loads(decoded_test_data)) is dict
    assert json.dumps(test_data) == decoded_test_data


def test_decode_pubsub_message_data_invalid_format():
    test_data_incorrect = []
    with pytest.raises(MessageDecodeError) as ex:
        decoded_test_data = decode_pubsub_message_data(test_data_incorrect)
    assert str(ex.value) == (
        "Unknown DataType for PubSub message data - unable to decode. argument should be a "
        "bytes-like object or ASCII string, not 'list'"
    )


def test_decode_pubsub_message_data_not_strict_list():
    test_data_list = ["test", 123]
    decoded_test_data = decode_pubsub_message_data(test_data_list, strict=False)
    assert type(decoded_test_data) is str
    assert type(json.loads(decoded_test_data)) is list
    assert json.dumps(test_data_list) == decoded_test_data


def test_decode_pubsub_message_data_not_strict_none():
    test_data = None
    decoded_test_data = decode_pubsub_message_data(test_data, strict=False)
    assert type(decoded_test_data) is str
    assert json.loads(decoded_test_data) is None
    assert json.dumps(test_data) == decoded_test_data


def test_decode_pubsub_message_data_base64_error():
    test_data_incorrect = "hello"
    with pytest.raises(MessageDecodeError) as ex:
        decoded_test_data = decode_pubsub_message_data(test_data_incorrect)
    assert str(ex.value) == (
        "Pubsub Message Data Base64 error: Invalid base64-encoded string: "
        "number of data characters (5) cannot be 1 more than a multiple of 4"
    )


def test_decode_pubsub_message_data_unicode_decode_error():
    test_data_incorrect = "hel"
    with pytest.raises(MessageDecodeError) as ex:
        decoded_test_data = decode_pubsub_message_data(test_data_incorrect)
    assert str(ex.value) == "Pubsub Message Data Base64 error: Incorrect padding"


def test_create_pydantic_validation_error_message():
    message = (
        "1 validation error for IngestionData\ntarget_message_uuid\nField required "
        "[type=missing, input_value={'_table_name': 'wf...41.c000.snappy.parquet'}, "
        "input_type=dict]\nFor further information visit https://errors.pydantic.dev/2.3/v/missing"
    )

    result = create_pydantic_validation_error_message(message)

    assert result == (
        "The following request parameters failed validation: [('target_message_uuid', "
        "\"Field required [type=missing, input_value={'_table_name': "
        "'wf...41.c000.snappy.parquet'}, input_type=dict]\")]"
    )


def test_format_pydantic_validation_error_message():
    test_data = [
        {
            "type": "missing",
            "loc": ("body", "message", "publish_time"),
            "msg": "Field required",
            "input": {
                "data": {
                    "_table_name": "wfm_activity",
                },
                "message_id": "test_message_id",
            },
            "url": "https://errors.pydantic.dev/2.3/v/missing",
        }
    ]
    result = format_pydantic_validation_error_message(test_data)
    assert result == (
        "The following request parameters failed validation: "
        "[{'parameter': 'publish_time', 'reason': 'Field required'}]"
    )


@patch("helper.utils.decode_pubsub_message_data")
def test_read_validate_message_data(mock_decode):
    # Configure the mock objects
    example_data = {"bucket": "test_bucket", "name": "table"}
    mock_decode.return_value = json.dumps(example_data)

    mock_request = Message(
        message=PubSubMessage(
            data=json.dumps(example_data).encode("utf-8"),
            message_id="123",
            publish_time="2023-07-31T15:01:06.058022+01:00",
            attributes={},
        )
    )

    result = read_validate_message_data(mock_request)

    # Assert
    mock_decode.assert_called_with(mock_request.message.data)
    assert result == GcsToPubsubEvent(**example_data)


def test_read_validate_message_data_json_error():
    mock_request = Message(
        message=PubSubMessage(
            data="InBheWxvYWQiOiB7CiAgICAgICAgICAgICAgICAidmVyaW50X3RhYmxlX25hbWUiOiAid2ZtX2FjdGl2aXR5IiwKICAgICAgICAgICAgICAgICJmaWxlX25hbWUiOiAiIiwKICAgICAgICAgICAgICAgICJ0YXJnZXRfbWVzc2FnZV91dWlkCiAgICAgICAgICAgIH0=",
            message_id="123",
            publish_time="2023-07-31T15:01:06.058022+01:00",
            attributes={},
        )
    )

    with pytest.raises(ManualDLQError):
        read_validate_message_data(mock_request)


def test_extract_trace_and_request_type():
    mock_request = Mock()
    mock_request.headers = {"X-Cloud-Trace-Context": "test_trace_id/test_span_id"}
    mock_request.scope = {"path": "/test/path"}

    result = extract_trace_and_request_type(mock_request)

    expected_trace = f"projects/dummy-project/traces/test_trace_id"
    assert result["logging.googleapis.com/trace"] == expected_trace
    assert result["requestType"] == mock_request.scope["path"]


def test_remove_file_extension():
    encrypted_file_extension = "dummy.json.gpg"
    incorrect_file_extension = "dummy.jsongpg"
    json_file_extension = "dummy.json"

    assert remove_file_extension(encrypted_file_extension, "gpg") == "dummy.json"
    assert remove_file_extension(encrypted_file_extension, "json") == "dummy.gpg"
    assert remove_file_extension(incorrect_file_extension, "gpg") == incorrect_file_extension
    assert remove_file_extension(json_file_extension, "csv") == json_file_extension
