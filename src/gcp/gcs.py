import logging.config

from google.api_core.exceptions import GoogleAPIError
from google.cloud import storage
from google.cloud.exceptions import NotFound

from configuration.logger_config import logger_config
from error.custom_exceptions import ManualDLQError, PubsubReprocessError
from pydantic_model.api_model import ErrorEnum
from service.logger import CustomLoggerAdapter
import os

logger = CustomLoggerAdapter(logging.getLogger(__name__), None)


class GoogleCloudStorage:
    """Class to interact with Google cloud storage"""

    def __init__(self, project_id):
        self._client = self._init_client(project_id)

    def _init_client(self, project_id):
        return storage.Client(project_id)

    def download_model_from_gcs(self, bucket_name, model_blob_name, local_model_dir):
        """
        Download model files from GCS bucket to local directory.
        """
        try:
            bucket = self._client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=model_blob_name)
            for blob in blobs:
                local_path = os.path.join(local_model_dir, os.path.relpath(blob.name, model_blob_name))
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                blob.download_to_filename(local_path)

        except NotFound as e:
            error_value = f"Failed to read file from google cloud storage: {e}"
            logger.error(msg=error_value)
            raise ManualDLQError(
                original_request=logger_config.context.get().get("original_request"),
                error_desc=error_value,
                error_stage=ErrorEnum.FILE_NOT_FOUND,
            )

        except (GoogleAPIError, Exception) as e:
            error_value = f"Failed to read file from google cloud storage: {e}"
            logger.error(msg=error_value)
            raise PubsubReprocessError(
                original_request=logger_config.context.get().get("original_request"),
                error_desc=error_value,
                error_stage=ErrorEnum.GOOGLE_API_ERROR,
            )
