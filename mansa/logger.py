import json  # noqa: D100
import logging
import logging.config
import os

# Logger setup
default_path = "./logging.json"
default_level = logging.INFO
env_key = "LOG_CFG"


class Logger:
    """Logger class."""

    def __init__(self) -> None:
        pass

    def getLogger(self, name):  # noqa: N802
        """Get the configuration of the logger.

        Parameters
        ----------
        name : _type_
            _description_

        Returns
        -------
        _type_
            _description_
        """
        path = default_path
        value = os.getenv(env_key, None)
        if value:
            path = value
        if os.path.exists(path):
            with open(path, "rt", encoding="utf-8") as f:
                config = json.load(f)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)

        return logging.getLogger(name)
