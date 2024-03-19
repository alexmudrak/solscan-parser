import logging
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Logger config
    log_level: str = "INFO"
    logging.basicConfig(level=log_level)

    if log_level != "DEBUG":
        logging.getLogger("googleapiclient").setLevel(logging.WARNING)
        logging.getLogger("undetected_chromedriver").setLevel(logging.WARNING)

    # Source settings
    hases_file_path: str | None = os.getenv("HASHES_FILE_PATH", None)

    # Parse settings
    main_url: str = "https://solscan.io/account/"

    # Google sheets settings
    sheet_scopes: list[str] = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    sheet_title: str = "[RESULT] SOLSCAN parse"
    sheet_first_list_name: str = "Result"
    sheet_range: str = f"{sheet_first_list_name}!A2:F"
    sheet_headers: list[str] = [
        "Date",
        "Hash",
        "SOL count",
        "SOL usd",
        "SPL count",
        "SPL usd",
    ]


settings = Settings()
