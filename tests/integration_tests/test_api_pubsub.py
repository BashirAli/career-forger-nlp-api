import json

from api.data import eml_pubsub_data
from configuration.env import settings
import json
from unittest.mock import Mock, patch


def test_successful_e2e(
        pubsub_utils,
        pubsub_testing_topic,
        pubsub_testing_subscription,
        api_client,
):
    with api_client as client:
        response = client.post("/", json=eml_pubsub_data.valid_pubsub_eml_event_data)
        result = response.json()

        expected_message = eml_pubsub_data.valid_response_raw_dict

        response_topic_msgs = pubsub_utils.pull_msgs(
            subscription_path=pubsub_testing_subscription
        )

        actual_message = json.loads(response_topic_msgs[0])

        assert actual_message == expected_message

        assert response.status_code == 200


def test_pubsub_subscriber_missing_name(
        gcs_utils,
        upload_test_file,
        pubsub_utils,
        pubsub_testing_dlq_topic,
        pubsub_testing_dlq_subscription,
        api_client,
):
    response = api_client.post("/", json=eml_pubsub_data.invalid_test_missing_fields)
    result = response.json()

    expected_dlq_message = eml_pubsub_data.invalid_test_missing_fields["message"]["data"]

    response_dlq = pubsub_utils.pull_msgs(
        subscription_path=pubsub_testing_dlq_subscription
    )

    actual_message = json.loads(response_dlq[0])

    assert actual_message == expected_dlq_message
    assert len(response_dlq) == 1
    assert response.status_code == 202
    assert result == {
        "exception": "ManualDLQError",
        "detail": "The following request parameters failed validation: "
                  "[('name', \"Field required [type=missing, "
                  "input_value={'kind': 'storage_object'...', 'etag': 'dummy_etag'}, "
                  'input_type=dict]")]',
    }


def test_pubsub_subscriber_missing_name_bytes(
        gcs_utils,
        upload_test_file,
        pubsub_utils,
        pubsub_testing_dlq_topic,
        pubsub_testing_dlq_subscription,
        api_client,
):
    response = api_client.post("/", json=eml_pubsub_data.invalid_test_missing_fields_bytes)
    result = response.json()

    expected_dlq_message = {"bucket": "career_forger_email_bucket"}

    response_dlq = pubsub_utils.pull_msgs(
        subscription_path=pubsub_testing_dlq_subscription
    )

    actual_message = json.loads(response_dlq[0])

    assert actual_message == expected_dlq_message
    assert len(response_dlq) == 1
    assert response.status_code == 202
    assert result == {
        "exception": "ManualDLQError",
        "detail": "The following request parameters failed validation: [('name', \"Field required "
                  "[type=missing, input_value={'bucket': 'career_forger_email_bucket'}, input_type=dict]\")]",
    }


@patch("google.cloud.storage.Client")
def test_pubsub_subscriber_send_reprocess(
        mock_storage_client,
        gcs_utils,
        upload_test_file,
        pubsub_utils,
        pubsub_testing_dlq_topic,
        pubsub_testing_dlq_subscription,
        api_client,
):
    mock_bucket = Mock()
    mock_blob = Mock()
    mock_blob.download_as_bytes.side_effect = Exception("Generic error")

    # Configure the mock client to return the mock bucket and blob
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    response = api_client.post("/", json=eml_pubsub_data.valid_pubsub_eml_event_data)
    result = response.json()

    response_dlq = pubsub_utils.pull_msgs(
        subscription_path=pubsub_testing_dlq_subscription
    )

    assert len(response_dlq) == 0
    assert response.status_code == 500
    assert result == {
        "exception": "PubsubReprocessError",
        "detail": "Failed to read file from google cloud storage: Generic error",
    }


def test_pubsub_subscriber_non_dict_data(
        gcs_utils,
        upload_test_file,
        pubsub_utils,
        pubsub_testing_dlq_topic,
        pubsub_testing_dlq_subscription,
        api_client,
):
    response = api_client.post("/", json=eml_pubsub_data.invalid_test_non_dict_data)
    result = response.json()

    expected_dlq_message = eml_pubsub_data.invalid_test_non_dict_data["message"]["data"]

    response_dlq = pubsub_utils.pull_msgs(
        subscription_path=pubsub_testing_dlq_subscription
    )

    actual_message = json.loads(response_dlq[0])

    assert actual_message == expected_dlq_message
    assert len(response_dlq) == 1
    assert response.status_code == 202
    assert result == {
        "exception": "Request Validation Error",
        "detail": "The following request parameters failed validation: "
                  "[{'parameter': 'bytes', 'reason': 'Input should be a valid bytes'}, "
                  "{'parameter': 'dict[str,any]', 'reason': 'Input should be a valid dictionary'}]",
    }


def test_pubsub_subscriber_missing_message_id(
        gcs_utils,
        upload_test_file,
        pubsub_utils,
        pubsub_testing_dlq_topic,
        pubsub_testing_dlq_subscription,
        api_client,
):
    response = api_client.post("/", json=eml_pubsub_data.invalid_test_non_dict_data)
    result = response.json()

    expected_dlq_message = eml_pubsub_data.invalid_test_non_dict_data["message"]["data"]

    response_dlq = pubsub_utils.pull_msgs(
        subscription_path=pubsub_testing_dlq_subscription
    )

    actual_message = json.loads(response_dlq[0])

    assert actual_message == expected_dlq_message
    assert len(response_dlq) == 1
    assert response.status_code == 202
    assert result == {
        "exception": "Request Validation Error",
        "detail": "The following request parameters failed validation: "
                  "[{'parameter': 'bytes', 'reason': 'Input should be a valid bytes'}, "
                  "{'parameter': 'dict[str,any]', 'reason': 'Input should be a valid dictionary'}]",
    }


@patch("google.cloud.pubsub_v1.PublisherClient")
def test_api_pubsub_timeout_error(
        mock_PublisherClient, api_client, pubsub_testing_dlq_subscription, pubsub_utils
):
    mock_future = Mock()
    mock_future.result.side_effect = TimeoutError("Publishing timed out")
    mock_PublisherClient.return_value.publish.return_value = mock_future

    result = api_client.post("/", json=eml_pubsub_data.invalid_test_missing_fields_bytes)

    response_dlq = pubsub_utils.pull_msgs(
        subscription_path=pubsub_testing_dlq_subscription
    )

    assert len(response_dlq) == 0
    assert result.status_code == 500
    assert result.json() == {
        "exception": "Pubsub Publish Error",
        "detail": "Publishing timed out",
    }


@patch("google.cloud.pubsub_v1.PublisherClient")
def test_api_pubsub_type_error(
        mock_PublisherClient, api_client, pubsub_testing_dlq_subscription, pubsub_utils
):
    mock_future = Mock()
    mock_future.result.side_effect = TypeError("Type Error")
    mock_PublisherClient.return_value.publish.return_value = mock_future

    result = api_client.post("/", json=eml_pubsub_data.invalid_test_missing_fields_bytes)

    response_dlq = pubsub_utils.pull_msgs(
        subscription_path=pubsub_testing_dlq_subscription
    )

    assert len(response_dlq) == 0
    assert result.status_code == 500
    assert result.json() == {
        "exception": "Pubsub Publish Error",
        "detail": "Type Error",
    }


@patch("google.cloud.pubsub_v1.PublisherClient")
def test_api_pubsub_unknown_error(
        mock_PublisherClient, api_client, pubsub_testing_dlq_subscription, pubsub_utils
):
    mock_future = Mock()
    mock_future.result.side_effect = Exception("Unknown Error")
    mock_PublisherClient.return_value.publish.return_value = mock_future

    result = api_client.post("/", json=eml_pubsub_data.invalid_test_missing_fields_bytes)

    response_dlq = pubsub_utils.pull_msgs(
        subscription_path=pubsub_testing_dlq_subscription
    )

    assert len(response_dlq) == 0
    assert result.status_code == 500
    assert result.json() == {
        "exception": "Pubsub Publish Error",
        "detail": "Unknown Error",
    }
