from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gcp_project_id: str = Field(..., alias="GCP_PROJECT_ID")
    api_name: str = "career-forger-nlp-api"
    nlp_bucket: str = Field(
        ..., json_schema_extra={"env": "NLP_BUCKET"}
    )
    is_test_env: Optional[bool] = Field(
        default=False, alias="IS_TEST_ENV"
    )
    pubsub_topic: str = "career_forger_analysis.topic"
    dlq_topic: str = "career_forger_analysis_dlq.topic"


settings = Settings()
