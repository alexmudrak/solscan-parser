import logging


class CustomFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = f"{record.levelname}:"
        return super().format(record)


def get_logger(
    logger_name: str,
):
    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        formatter = CustomFormatter(
            "%(levelname)-9s %(asctime)s - "
            "[%(name)s] - %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.propagate = False

    return logger
