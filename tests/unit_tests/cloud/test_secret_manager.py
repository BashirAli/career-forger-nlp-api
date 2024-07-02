from unittest.mock import patch

import pytest
from google.api_core.exceptions import GoogleAPICallError
from pydantic import BaseModel

from configuration.env import settings
from error.custom_exceptions import InternalAPIException
from gcp.secret import SecretManager

message_id = "12345"


class DummyPayload(BaseModel):
    data: bytes


class DummyResponse(BaseModel):
    payload: DummyPayload


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_secret_manager_success(mock_secret_manager):
    encoded_sample_data = '{"TestingSecretManager": "test"}'.encode("UTF-8")

    instance = mock_secret_manager.return_value
    instance.secret_version_path.return_value = "DummySuccessPath"
    instance.access_secret_version.return_value = DummyResponse(
        payload=DummyPayload(data=encoded_sample_data)
    )
    secret_id = "dummy-secret-1"
    version = "latest"
    secret_manager = SecretManager()
    secret_manager.get_secret(secret_id=secret_id)
    expected_name = "DummySuccessPath"
    instance.access_secret_version.assert_called_once_with(
        request={"name": expected_name}
    )
    instance.secret_version_path.assert_called_once_with(
        settings.gcp_project_id, secret_id, version
    )


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_pubsub_publish_secret_access_error(mock_secret_manager):
    with pytest.raises(InternalAPIException) as secret_access_error:
        instance = mock_secret_manager.return_value
        instance.secret_version_path.return_value = None
        instance.access_secret_version.side_effect = GoogleAPICallError(
            "Secret Access Error"
        )
        secret_manager = SecretManager()
        secret_manager.get_secret(
            secret_id="dummy-secret-2",
        )

    assert (
        str(secret_access_error.value)
        == "Error Fetching Secret: None Secret Access Error"
    )
