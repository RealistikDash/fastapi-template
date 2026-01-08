from __future__ import annotations

import logging.config

import yaml


def configure_from_yaml(*, path: str | None = None) -> None:
    if path is None:
        path = "logging.yaml"

    with open(path) as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)
