from __future__ import annotations

import logging.config
from collections.abc import Mapping
from contextvars import ContextVar
from logging import Logger as _LoggingLogger
from types import TracebackType
from typing import Any
from typing import Protocol
from typing import TypeAlias

import yaml

_SysExcInfoType: TypeAlias = (
    tuple[type[BaseException], BaseException, TracebackType | None]
    | tuple[None, None, None]
)
ExcInfoType: TypeAlias = bool | _SysExcInfoType | BaseException | None

_LOG_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar(
    "_LOG_CONTEXT",
    default=None,
)


def configure_from_yaml(*, path: str | None = None) -> None:
    if path is None:
        path = "logging.yaml"

    with open(path) as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)


class Logger(Protocol):
    def debug(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...

    def info(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...

    def warning(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...

    def error(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...

    def exception(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...


# Context management
def add_context(**kwargs: Any) -> None:
    """Add key-value pairs to the current request-local logging context."""
    log_context = _LOG_CONTEXT.get()

    if log_context is None:
        log_context = {}
        _LOG_CONTEXT.set(log_context)

    log_context.update(kwargs)


def clear_context() -> None:
    """Clear the current request-local logging context."""
    _LOG_CONTEXT.set(None)


def get_current_context() -> dict[str, Any]:
    log_context = _LOG_CONTEXT.get()
    if log_context is None:
        log_context = {}
        _LOG_CONTEXT.set(log_context)

    return log_context


def get_logger(name: str) -> Logger:
    return _ContextLoggingWrapper(logging.getLogger(name))


class _ContextLoggingWrapper:
    """A wrapper class around logging that adds "thread-local" context to the logging."""

    __slots__ = ("_logger",)

    def __init__(self, logger: _LoggingLogger) -> None:
        self._logger = logger

    def debug(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.debug(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=self._get_extra_params(extra),
        )

    def info(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.info(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=self._get_extra_params(extra),
        )

    def warning(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.warning(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=self._get_extra_params(extra),
        )

    def error(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.error(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=self._get_extra_params(extra),
        )

    def exception(
        self,
        msg: object,
        *args: object,
        exc_info: ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.exception(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=self._get_extra_params(extra),
        )

    def _get_extra_params(
        self,
        extra: Mapping[str, object] | None = None,
    ) -> dict[str, Any]:
        params = get_current_context()
        if extra is not None:
            params |= dict(extra)

        return params
