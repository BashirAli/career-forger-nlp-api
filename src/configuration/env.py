from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gcp_project_id: str = Field(..., alias="GCP_PROJECT_ID")
    api_name: str = "gcp-cloud-run-template-api"
    target_project_id: str = Field(..., json_schema_extra={"env": "TARGET_PROJECT_ID"})
    target_bucket: str = Field(
        ..., json_schema_extra={"env": "TARGET_BUCKET_NAME"}
    )
    is_test_env: Optional[bool] = Field(
        default=False, alias="IS_TEST_ENV"
    )
    key_secret_id: str = "secret_manager_id"
    dlq_topic: str = "dlq.topic"
    datastore_namespace: str = "test_datastore"


settings = Settings()
