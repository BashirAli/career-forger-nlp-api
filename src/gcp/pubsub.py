import decimal
import json
from concurrent import futures
from datetime import date, datetime

from google.cloud import pubsub_v1

from error.custom_exceptions import PubsubPublishException
from service.logger import CustomLoggerAdapter, configure_logger

PUBSUB_PUBLISH_TIMEOUT_SEC = 10

logger = CustomLoggerAdapter(configure_logger(), None)


class PubSubPublisher:
    def __init__(self, project_id, topic):
        self._project_id = project_id
        self._topic = topic
        self._ps_client = self._get_publisher_client()

    @staticmethod
    def _get_publisher_client() -> pubsub_v1.PublisherClient:
        return pubsub_v1.PublisherClient()

    @staticmethod
    def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return int(obj)
        raise TypeError(f"Type {type(obj)} is not serializable")

    def publish(self, data, source_message_uuid, source_publish_time) -> None:
        logger.info(f"Publishing to DLQ topic: {self._topic}")
        try:
            data_str = json.dumps(data, default=self.json_serial)
            publish_future = self._ps_client.publish(
                topic=f"projects/{self._project_id}/topics/{self._topic}",
                data=data_str.encode("utf-8"),
                source_message_uuid=str(source_message_uuid),
                source_publish_time=str(source_publish_time),
            )
            message_id = publish_future.result(timeout=PUBSUB_PUBLISH_TIMEOUT_SEC)
            logger.info(
                f"Message published to DLQ topic with the following id: {message_id}"
            )
        except futures.TimeoutError as te:
            logger.error(
                f"Publishing data timed after {PUBSUB_PUBLISH_TIMEOUT_SEC} "
                f"seconds to pubsub topic {self._topic}."
            )
            raise PubsubPublishException(str(te))
        except Exception as ge:
            logger.error(f"Unknown exception occured while publishing to DLQ: {ge}")
            raise PubsubPublishException(str(ge))
