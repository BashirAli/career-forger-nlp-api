import logging

from google.api_core.exceptions import BadRequest, ServiceUnavailable
from google.cloud import datastore

from configuration.env import settings
from service.logger import CustomLoggerAdapter
from error.custom_exceptions import DatastoreGenericError, InternalAPIException
from helper.utils import exponential_retry_decorator

logger = CustomLoggerAdapter(logging.getLogger(__name__), None)

ds_client = datastore.Client(project=settings.gcp_project_id, namespace=settings.namespace)

@exponential_retry_decorator(InternalAPIException, num_retries=5, logger=logger, time_to_wait = 10)
def get_entity(kind: str, filters: dict) -> datastore.entity:
    query = ds_client.query(kind=kind)
    for query_filter in filters:
        query.add_filter(query_filter, "=", filters[query_filter])

    try:
        result = list(query.fetch(limit=100))

    except BadRequest as e:
        raise DatastoreGenericError(f"Bad request: {e}")
    except ServiceUnavailable as e:
        raise InternalAPIException(f"Service Unavailable: {e}")

    return result
