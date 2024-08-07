import logging

import pytest
from fastapi.testclient import TestClient

from configuration.env import settings
from main import app
from utils.cloud_storage_utils import CloudStorageUtils
from utils.pubsub_utils import PubSubUtils

NLP_MODEL_FOLDER_PATH = "/home/appuser/tests/integration_tests/models/en_core_web_lg/"
DESTINATION_FOLDER_PATH = "models/en_core_web_lg/"


@pytest.fixture
def upload_spacy_model(gcs_utils):
    with open(NLP_MODEL_FOLDER_PATH, "r") as f:
        test_file = f.read()
    gcs_utils.upload_entire_folder(
        bucket_name=settings.target_bucket,
        folder_path=NLP_MODEL_FOLDER_PATH,
        prefix=DESTINATION_FOLDER_PATH,
    )

    return test_file


@pytest.fixture
def gcs_utils():
    return CloudStorageUtils()


@pytest.fixture
def pubsub_utils():
    return PubSubUtils()


@pytest.fixture()
def pubsub_testing_topic(pubsub_utils):
    # Create a new Pub/Sub topic for testing
    topic_path = pubsub_utils.create_temporary_topic(settings.pubsub_publish_topic_id)
    logging.warning(f"TOPIC PATH {topic_path}")
    yield topic_path

    # Clean up the topic after testing
    pubsub_utils.delete_temporary_topic(topic_path)


@pytest.fixture
def pubsub_testing_subscription(pubsub_utils, pubsub_testing_topic):
    # Create a new Pub/Sub subscription for testing
    subscription_path = pubsub_utils.create_temporary_subscription(
        topic_path=pubsub_testing_topic, subscription_name="dummy_subscription"
    )
    logging.warning(f"SUB PATH {subscription_path}")
    logging.warning(f"ATTACHED SUB TO TOPIC {pubsub_testing_topic}")
    yield subscription_path

    # Clean up the subscription after testing
    pubsub_utils.delete_temporary_subscription(subscription_path)


@pytest.fixture(scope="function")
def api_client(request):
    """Generate an API test client

    Need to parametrize with a ScheduleModeEnum member, eg:
       @pytest.mark.parametrize("api_client", [ScheduleModeEnum.ALWAYS_ON], indirect=True)
    """

    yield TestClient(app)
