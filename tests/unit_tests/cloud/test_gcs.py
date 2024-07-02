from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import GoogleAPIError
from google.cloud.exceptions import NotFound

from error.custom_exceptions import ManualDLQError, PubsubReprocessError
from gcp.gcs import GoogleCloudStorage

bucket_name = "test-bucket"
source_blob_name = "test_file.json.gpg"
destination_blob_name = "test_file.json"
string_data = "string data"
storage_client_mock = MagicMock()
bucket_mock = MagicMock()
blob_mock = MagicMock()

gcs = GoogleCloudStorage(project_id="dummy-project")
gcs._client = storage_client_mock


def test_read_gcs_file_to_bytes_success():
    blob_mock.download_as_bytes.return_value = b"test file in bytes"
    bucket_mock.blob.return_value = blob_mock
    storage_client_mock.bucket.return_value = bucket_mock

    file_as_bytes = gcs.read_gcs_file_to_bytes(bucket_name, source_blob_name)

    assert file_as_bytes == b"test file in bytes"
    storage_client_mock.bucket.assert_called_once_with(bucket_name)
    bucket_mock.blob.assert_called_once_with(source_blob_name)
    blob_mock.download_as_bytes.assert_called_once()


def test_read_gcs_file_to_bytes_failures():
    # Test NotFound Exception
    blob_mock.download_as_bytes.side_effect = NotFound("Testing NotFound")

    with pytest.raises(ManualDLQError):
        gcs.read_gcs_file_to_bytes(bucket_name, source_blob_name)

    # Test GoogleAPIError Exception
    blob_mock.download_as_bytes.side_effect = GoogleAPIError("Testing GoogleAPIError")

    with pytest.raises(PubsubReprocessError):
        gcs.read_gcs_file_to_bytes(bucket_name, source_blob_name)

    # Test General Exception
    blob_mock.download_as_bytes.side_effect = Exception("Testing Generic Exception")

    with pytest.raises(PubsubReprocessError):
        gcs.read_gcs_file_to_bytes(bucket_name, source_blob_name)


@patch("gcp.gcs.io.BytesIO")
@patch("gcp.gcs.io.StringIO")
def test_upload_stringio_to_gcs_success(string_io, bytes_io):
    string_io.return_value.getvalue.return_value = string_data
    bytes_io.return_value.getvalue.return_value = string_data.encode()
    storage_client_mock.bucket.return_value = bucket_mock
    bucket_mock.blob.return_value = blob_mock
    gcs.upload_stringio_to_gcs(bucket_name, destination_blob_name, string_data)

    blob_mock.upload_from_file.assert_called_once_with(
        bytes_io.return_value, size=len(bytes_io.return_value.getvalue())
    )


def test_upload_stringio_to_gcs_failure():
    blob_mock.upload_from_file.side_effect = Exception("Failed to upload to GCS bucket")

    with pytest.raises(PubsubReprocessError):
        gcs.upload_stringio_to_gcs(bucket_name, destination_blob_name, string_data)


