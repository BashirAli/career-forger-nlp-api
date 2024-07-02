import logging

import pytest
from fastapi.testclient import TestClient
import json
from configuration.env import settings
from main import app
from google.cloud import datastore


from utils.cloud_storage_utils import CloudStorageUtils
from utils.pubsub_utils import PubSubUtils

TEST_GCS_FILE_PATH = "/home/appuser/tests/integration_tests/api/data/test_gcs_upload_file.json"
####TODO ADD MORE USECASES IN HERE WHEN MORE IMPLEMENTATION IS DEVELOPED
TEST_CONSUMER_ENDPOINT_USE_CASES= "/home/appuser/tests/integration_tests/api/data/test_consumer_endpoint.json"

DESTINATION_BLOB_NAME = "test/2024/05/31/test_file.json"


@pytest.fixture
def consumer_example_payloads():
    with open(TEST_CONSUMER_ENDPOINT_USE_CASES, "r") as f:
        test_file = json.loads(f.read())

    return test_file


@pytest.fixture
def upload_test_file(gcs_utils):
    with open(TEST_GCS_FILE_PATH, "r") as f:
        test_file = f.read()
    gcs_utils.upload_file_from_buffer(
        bucket=settings.target_bucket,
        file_name=DESTINATION_BLOB_NAME,
        string_data=test_file,
    )

    return test_file

@pytest.fixture(scope="session")
def dummy_datastore_data():
    return {}


@pytest.fixture
def gcs_utils():
    return CloudStorageUtils()


@pytest.fixture
def pubsub_utils():
    return PubSubUtils()


@pytest.fixture()
def pubsub_testing_topic(pubsub_utils):
    # Create a new Pub/Sub topic for testing
    topic_path = pubsub_utils.create_temporary_topic(settings.dlq_topic)
    logging.warning(f"TOPIC PATH {topic_path}")
    yield topic_path

    # Clean up the topic after testing
    pubsub_utils.delete_temporary_topic(topic_path)


@pytest.fixture
def pubsub_testing_subscription(pubsub_utils, pubsub_testing_topic):
    # Create a new Pub/Sub subscription for testing
    subscription_path = pubsub_utils.create_temporary_subscription(
        topic_path=pubsub_testing_topic, subscription_name="dlq_dummy_subscription"
    )
    logging.warning(f"SUB PATH {subscription_path}")
    logging.warning(f"ATTACHED SUB TO TOPIC {pubsub_testing_topic}")
    yield subscription_path

    # Clean up the subscription after testing
    pubsub_utils.delete_temporary_subscription(subscription_path)

@pytest.fixture(scope="session")
def mock_datastore(dummy_datastore_data):
    """Create a Datastore client and load in our dummy data"""
    mock_datastore = datastore.Client(project=settings.gcp_project_id, namespace=settings.datastore_namespace)
    # # Load dummy data
    # for data in dummy_datastore_data:
    #     entity_key = mock_datastore.key("key")
    #     entity = datastore.Entity(key=entity_key)
    #     entity.update(**data["row"])
    #     mock_datastore.put(entity=entity)

    # Off to the tests
    yield mock_datastore

    # # Post testing cleanup
    # for data in dummy_datastore_data:
    #     key = mock_datastore.key("key")
    #     mock_datastore.delete(key)


@pytest.fixture(scope="function")
def api_client(mock_datastore, request):
    """Generate an API test client

    Need to parametrize with a ScheduleModeEnum member, eg:
       @pytest.mark.parametrize("api_client", [ScheduleModeEnum.ALWAYS_ON], indirect=True)
    """
    # Override the datastore dependency in the API for these tests
    app.state.datastore = mock_datastore

    yield TestClient(app)