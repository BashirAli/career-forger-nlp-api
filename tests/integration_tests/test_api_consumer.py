import json
import hashlib
import uuid
from datetime import datetime
from error.custom_exceptions import InternalAPIException
from unittest.mock import Mock, patch

from configuration.env import settings

default_headers = {
    'request-id': 'Test',
    'request-timestamp': datetime.now().isoformat()
}

invalid_headers_no_headers = {}

invalid_headers_no_requestid = {
    'request-timestamp': datetime.now().isoformat()
}

invalid_headers_no_request_timestamp = {
    'request-id': str(uuid.uuid4()),
}


def test_server_connection(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200

    # response = requests.get(f"{host}/health").json()
    assert response.json() == {"Status": "OK"}

def test_default_use_case_e2e(consumer_example_payloads, api_client):
    default_use_case_data = consumer_example_payloads[0]["USE_CASE_TYPICAL"]
    response = api_client.post("/v1/hello_world", json=default_use_case_data, headers=default_headers)

    assert response.status_code == 200
    response_payload = response.json()

    response_data = response_payload['response']['result']

    assert isinstance(response_data, dict)
    assert response_data['message'] == "Hello"
    assert response_data['hashed_message_id'] == hashlib.md5("Test_ID".encode('utf-8')).hexdigest() + "_Test_ID"
    assert response_data['secret_manager_key'] == "12345"

####TODO FIX THIS ANOTHER TIME
# def test_no_headers_400(consumer_example_payloads, api_client):
#     default_use_case_data = consumer_example_payloads[0][
#         "USE_CASE_TYPICAL"]
#     response = api_client.post("/v1/hello_world", json=default_use_case_data,
#                            headers=invalid_headers_no_headers)
#
#     assert response.status_code == 400
#     assert "Validation Exception" in str(response.content)
#     assert "request-id" in str(response.content)
#     assert "request-timestamp" in str(response.content)
#
# def test_no_request_header_400(consumer_example_payloads, api_client):
#     default_use_case_data = consumer_example_payloads[0][
#         "USE_CASE_TYPICAL"]
#     response = api_client.post("/v1/hello_world", json=default_use_case_data,
#                            headers=invalid_headers_no_requestid)
#
#     assert response.status_code == 400
#     assert "Validation Exception" in str(response.content)
#     assert "request-id" in str(response.content)
#
# def test_no_request_timestamp_header_400(consumer_example_payloads, api_client):
#     default_use_case_data = consumer_example_payloads[0][
#         "USE_CASE_TYPICAL"]
#     response = api_client.post("/v1/hello_world", json=default_use_case_data,
#                            headers=invalid_headers_no_request_timestamp)
#
#     assert response.status_code == 400
#     assert "Validation Exception" in str(response.content)
#     assert "request-timestamp" in str(response.content)
#
# @patch("main.gcp_template_response")
# def test_500_Internal_Exception_handled(consumer_example_payloads, api_client, mock_response):
#     mock_response.side_effect = InternalException("My Custom Error 500 error thrown")
#     default_use_case_data = consumer_example_payloads[0][
#         "USE_CASE_TYPICAL"]
#     response = api_client.post("/v1/hello_world", json=default_use_case_data,
#                            headers=default_headers)
#     assert response.status_code == 500
#     assert "Internal Error Occurred" in str(response.content)
#     assert "CRITICAL" in str(response.content)
#
# @patch("main.gcp_template_response")
# def test_500_Exception_handled(consumer_example_payloads, api_client, mock_response):
#     mock_response.side_effect = Exception("My 500 Exception error thrown")
#     default_use_case_data = consumer_example_payloads[0][
#         "USE_CASE_TYPICAL"]
#     response = api_client.post("/v1/hello_world", json=default_use_case_data,
#                            headers=default_headers)
#     assert response.status_code == 500
#     assert "My 500 Exception error thrown" in str(response.content)
#     assert "CRITICAL" in str(response.content)
