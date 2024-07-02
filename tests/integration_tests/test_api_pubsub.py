import json
from unittest.mock import Mock, patch

from api.data import gcs_event_data

from configuration.env import settings

TARGET_BLOB_NAME = "test/2024/05/31/test_file.json"
DESTINATION_BLOB_NAME = "test/2024/05/31/test_file.json"

def test_successful_e2e(gcs_utils, upload_test_file, api_client):
    # send the request to API endpoint which will send  file to 'test-bucket'
    with api_client as client:
        response = client.post("/", json=gcs_event_data.valid_gcs_event_data)
        result = response.json()

        # read the  file sent to test bucket
        file_as_bytes = gcs_utils.read_file(
            bucket_name=settings.target_bucket,
            source_blob_name=TARGET_BLOB_NAME,
        )

        # clean up of bucket
        gcs_utils.wipe_bucket(settings.target_bucket)

        assert json.loads(file_as_bytes) == [
                                 {
                                   "Name": "John Doe",
                                   "Age": 30,
                                   "Country": "United States"
                                 },
                                 {
                                   "Name": "Jane Doe",
                                   "Age": 25,
                                   "Country": "Canada"
                                 },
                                 {
                                   "Name": "Peter Smith",
                                   "Age": 40,
                                   "Country": "United Kingdom"
                                 }
                                ]
        assert response.status_code == 200
        assert (
                len(file_as_bytes) > 0
        ), f"No file was found in the '{settings.target_bucket}' bucket."

####TODO IMPLEMENT THESE WHEN YOU IMPLEMENT MANUAL DLQ PUBLISH FOR INVALID INBOUND PUBSUB MESSAGES USING src/utils/helper.py read_validate_message_data()
# def test_pubsub_subscriber_missing_name(
#         gcs_utils,
#         upload_test_file,
#         pubsub_utils,
#         pubsub_testing_topic,
#         pubsub_testing_subscription,
#         api_client,
# ):
#     response = api_client.post("/", json=gcs_event_data.invalid_test_missing_name)
#     result = response.json()
#
#     expected_dlq_message = gcs_event_data.invalid_test_missing_name["message"]["data"]
#
#     response_dlq = pubsub_utils.pull_messages(
#         subscription_path=pubsub_testing_subscription
#     )
#
#     # clean up
#     gcs_utils.wipe_bucket(settings.target_bucket)
#
#     actual_message = json.loads(response_dlq[0])
#
#     assert actual_message == expected_dlq_message
#     assert len(response_dlq) == 1
#     assert response.status_code == 202
#     assert result == {
#         "exception": "ManualDLQError",
#         "detail": "The following request parameters failed validation: "
#                   "[('name', \"Field required [type=missing, "
#                   "input_value={'kind': 'storage_object'...', 'etag': 'dummy_etag'}, "
#                   'input_type=dict]")]',
#     }


# def test_pubsub_subscriber_missing_name_bytes(
#         gcs_utils,
#         upload_test_file,
#         pubsub_utils,
#         pubsub_testing_topic,
#         pubsub_testing_subscription,
#         api_client,
# ):
#     response = api_client.post("/", json=gcs_event_data.invalid_test_missing_name_bytes)
#     result = response.json()
#
#     expected_dlq_message = {"bucket": "dummy_bucket"}
#
#     response_dlq = pubsub_utils.pull_messages(
#         subscription_path=pubsub_testing_subscription
#     )
#
#     # clean up
#     gcs_utils.wipe_bucket(settings.target_bucket)
#
#     actual_message = json.loads(response_dlq[0])
#
#     assert actual_message == expected_dlq_message
#     assert len(response_dlq) == 1
#     assert response.status_code == 202
#     assert result == {
#         "exception": "ManualDLQError",
#         "detail": "The following request parameters failed validation: [('name', \"Field required "
#                   "[type=missing, input_value={'bucket': 'dummy_bucket'}, input_type=dict]\")]",
#     }


# @patch("google.cloud.storage.Client")
# def test_pubsub_subscriber_send_reprocess(
#         mock_storage_client,
#         gcs_utils,
#         upload_test_file,
#         pubsub_utils,
#         pubsub_testing_topic,
#         pubsub_testing_subscription,
#         api_client,
# ):
#     mock_bucket = Mock()
#     mock_blob = Mock()
#     mock_blob.download_as_bytes.side_effect = Exception("Generic error")
#
#     # Configure the mock client to return the mock bucket and blob
#     mock_storage_client.return_value.bucket.return_value = mock_bucket
#     mock_bucket.blob.return_value = mock_blob
#
#     response = api_client.post("/", json=gcs_event_data.valid_gcs_event_data)
#     result = response.json()
#
#     response_dlq = pubsub_utils.pull_messages(
#         subscription_path=pubsub_testing_subscription
#     )
#
#     # clean up
#     gcs_utils.wipe_bucket(settings.target_bucket)
#
#     assert len(response_dlq) == 0
#     assert response.status_code == 500
#     assert result == {
#         "exception": "PubsubReprocessError",
#         "detail": "Failed to read file from google cloud storage: Generic error",
#     }
#
#
# def test_pubsub_subscriber_non_dict_data(
#         gcs_utils,
#         upload_test_file,
#         pubsub_utils,
#         pubsub_testing_topic,
#         pubsub_testing_subscription,
#         api_client,
# ):
#     response = api_client.post("/", json=gcs_event_data.invalid_test_non_dict_data)
#     result = response.json()
#
#     expected_dlq_message = gcs_event_data.invalid_test_non_dict_data["message"]["data"]
#
#     response_dlq = pubsub_utils.pull_messages(
#         subscription_path=pubsub_testing_subscription
#     )
#
#     # clean up
#     gcs_utils.wipe_bucket(settings.target_bucket)
#
#     actual_message = json.loads(response_dlq[0])
#
#     assert actual_message == expected_dlq_message
#     assert len(response_dlq) == 1
#     assert response.status_code == 202
#     assert result == {
#         "exception": "Request Validation Error",
#         "detail": "The following request parameters failed validation: "
#                   "[{'parameter': 'bytes', 'reason': 'Input should be a valid bytes'}, "
#                   "{'parameter': 'dict[str,any]', 'reason': 'Input should be a valid dictionary'}]",
#     }
#
#
# def test_pubsub_subscriber_missing_message_id(
#         gcs_utils,
#         upload_test_file,
#         pubsub_utils,
#         pubsub_testing_topic,
#         pubsub_testing_subscription,
#         api_client,
# ):
#     response = api_client.post("/", json=gcs_event_data.invalid_test_non_dict_data)
#     result = response.json()
#
#     expected_dlq_message = gcs_event_data.invalid_test_non_dict_data["message"]["data"]
#
#     response_dlq = pubsub_utils.pull_messages(
#         subscription_path=pubsub_testing_subscription
#     )
#
#     # clean up
#     gcs_utils.wipe_bucket(settings.target_bucket)
#
#     actual_message = json.loads(response_dlq[0])
#
#     assert actual_message == expected_dlq_message
#     assert len(response_dlq) == 1
#     assert response.status_code == 202
#     assert result == {
#         "exception": "Request Validation Error",
#         "detail": "The following request parameters failed validation: "
#                   "[{'parameter': 'bytes', 'reason': 'Input should be a valid bytes'}, "
#                   "{'parameter': 'dict[str,any]', 'reason': 'Input should be a valid dictionary'}]",
#     }
#
#
# @patch("google.cloud.pubsub_v1.PublisherClient")
# def test_api_pubsub_timeout_error(
#         mock_PublisherClient, api_client, pubsub_testing_subscription, pubsub_utils
# ):
#     mock_future = Mock()
#     mock_future.result.side_effect = TimeoutError("Publishing timed out")
#     mock_PublisherClient.return_value.publish.return_value = mock_future
#
#     result = api_client.post("/", json=gcs_event_data.invalid_test_missing_name_bytes)
#
#     response_dlq = pubsub_utils.pull_messages(
#         subscription_path=pubsub_testing_subscription
#     )
#
#     assert len(response_dlq) == 0
#     assert result.status_code == 500
#     assert result.json() == {
#         "exception": "Pubsub Publish Error",
#         "detail": "Publishing timed out",
#     }
#
#
# @patch("google.cloud.pubsub_v1.PublisherClient")
# def test_api_pubsub_type_error(
#         mock_PublisherClient, api_client, pubsub_testing_subscription, pubsub_utils
# ):
#     mock_future = Mock()
#     mock_future.result.side_effect = TypeError("Type Error")
#     mock_PublisherClient.return_value.publish.return_value = mock_future
#
#     result = api_client.post("/", json=gcs_event_data.invalid_test_missing_name_bytes)
#
#     response_dlq = pubsub_utils.pull_messages(
#         subscription_path=pubsub_testing_subscription
#     )
#
#     assert len(response_dlq) == 0
#     assert result.status_code == 500
#     assert result.json() == {
#         "exception": "Pubsub Publish Error",
#         "detail": "Type Error",
#     }
#
#
# @patch("google.cloud.pubsub_v1.PublisherClient")
# def test_api_pubsub_unknown_error(
#         mock_PublisherClient, api_client, pubsub_testing_subscription, pubsub_utils
# ):
#     mock_future = Mock()
#     mock_future.result.side_effect = Exception("Unknown Error")
#     mock_PublisherClient.return_value.publish.return_value = mock_future
#
#     result = api_client.post("/", json=gcs_event_data.invalid_test_missing_name_bytes)
#
#     response_dlq = pubsub_utils.pull_messages(
#         subscription_path=pubsub_testing_subscription
#     )
#
#     assert len(response_dlq) == 0
#     assert result.status_code == 500
#     assert result.json() == {
#         "exception": "Pubsub Publish Error",
#         "detail": "Unknown Error",
#     }
