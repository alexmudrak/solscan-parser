from core.config import settings
from core.logger import get_logger
from services.solscan_parser import SolscanParser

logger = get_logger(__name__)


def read_hashes_from_file(file_path: str) -> list[str]:
    try:
        with open(file_path, "r") as file:
            return [
                line.replace('"', "").replace("'", "").strip()
                for line in file
                if line.strip() and not line.startswith("#")
            ]
    except Exception as e:
        logger.exception(
            "An error occurred while reading hashes from the file."
        )
        raise e


if __name__ == "__main__":
    # TODO: get hashes from Google sheet
    file_path = settings.hashes_file_path
    if not file_path:
        msg = "The path to the hashes file is not specified in the settings."
        logger.error(msg)
        raise ValueError(msg)

    hashes = read_hashes_from_file(file_path)

    with SolscanParser(hashes) as parser:
        parser.process_hashes()
