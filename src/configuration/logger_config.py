from contextvars import ContextVar

from configuration.env import settings


class CustomLogger:
    """Class used to set logger configuration and context info"""

    def append_new_contexts(self, add_new_ctx: dict):
        self.__context.set(add_new_ctx)

    def __init__(self) -> None:
        self.__default_context_values = {"project": settings.gcp_project_id}
        self.__context = ContextVar("messageInfo", default=settings.gcp_project_id)
        self.__context.set(self.__default_context_values)

    def set_request_contexts(self, ctx_fields: dict, original_request: dict):
        context_values = {
            **self.__default_context_values,
            **ctx_fields,
            "original_request": original_request,
        }
        self.__context.set(context_values)

    @property
    def context(self):
        return self.__context


logger_config = CustomLogger()
