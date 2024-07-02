from pydantic_model.api_model import Message


class ManualDLQError(Exception):
    """Custom Exception for manual DLQ

    Args:
        Exception ([type]): [description]
    """

    def __init__(
        self, original_request: Message, error_desc: str, error_stage: str
    ):
        self.original_request = original_request
        self.error_desc = error_desc
        self.error_stage = error_stage


class PubsubReprocessError(Exception):
    """Custom exception to reprocess a message

    Args:
        Exception ([type]): [description]
    """

    def __init__(self, original_request, error_desc, error_stage):
        self.original_request = original_request
        self.error_desc = error_desc
        self.error_stage = error_stage


class MessageDecodeError(Exception):
    """Custom Exception for pubsub decode validation

    Args:
        Exception ([type]): [description]
    """
class MessageValidationError(Exception):
    """Custom Exception for pubsub data validation

    Args:
        Exception ([type]): [description]
    """

class PubsubPublishException(Exception):
    """Custom Exception for PubSub Publish Exceptions

    Args:
        Exception ([type]): [description]
    """

class ModelValidationError(Exception):
    """Custom Exception for Pydantic Model Validation

    Args:
        Exception ([type]): [description]
    """


class InternalAPIException(Exception):
    """Custom Exception for Internal api exceptions

    Args:
        Exception ([type]): [description]
    """