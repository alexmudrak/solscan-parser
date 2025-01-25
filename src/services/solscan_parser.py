import time
from datetime import datetime
from urllib.parse import urljoin

import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from core.config import settings
from core.logger import get_logger
from schemas.parse_schemas import SolscanResult
from services.google_sheets import GoogleSheets

logger = get_logger(__name__)


class SolscanParser:
    def __init__(self, hashes: list[str]):
        self.google_sheets = GoogleSheets()
        self.url = settings.main_url
        self.hashes = hashes
        self.driver = None

    def __enter__(self):
        logger.info("Entering to the browser...")

        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--headless")

        self.driver = uc.Chrome(use_subprocess=True, options=chrome_options)

        return self

    def __exit__(self, exc_type, exc_value, _):
        logger.info("Exiting from the browser...")
        if exc_type:
            logger.error(f"An exception occurred: {exc_value}")

        if self.driver:
            self.driver.close()

        return False

    def proccess_sol(
        self, result: SolscanResult, elem: WebElement
    ) -> SolscanResult:
        logger.debug(f"Trying process SOL for {result.hash}: {elem.text}")
        if elem:
            row_text = elem.text
            sol_balance = row_text.split(" ")[0].strip()
            result.sol_count = sol_balance

        return result

    def proccess_spl(
        self, result: SolscanResult, elem: WebElement
    ) -> SolscanResult:
        logger.debug(f"Trying process SPL for {result.hash}: {elem.text}")
        if elem:
            row_text = elem.text
            spl_count, spl_usd = row_text.split("\n")
            spl_count = spl_count.split(" ")[0]
            spl_usd = (
                spl_usd.replace("(", "").replace(")", "").replace("$", "")
            )

            result.spl_count = spl_count
            result.spl_usd = spl_usd

        return result

    def parse_sol_values(self, result: SolscanResult, driver) -> SolscanResult:
        logger.debug(f"Trying parse SOL for {result.hash}")
        sol_balance_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    ("//div[text()='SOL Balance']/following::div"),
                )
            )
        )
        result = self.proccess_sol(result, sol_balance_element)

        return result

    def parse_spl_values(self, result: SolscanResult, driver) -> SolscanResult:
        logger.debug(f"Trying parse SPL for {result.hash}")
        spl_balance_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    ("//div[text()='Token Balance']/following::div"),
                )
            )
        )
        result = self.proccess_spl(result, spl_balance_element)

        return result

    def fix_cf_just_moment(self, url: str, driver):
        # Fix CF `Just moment...` loading
        driver.execute_script(f"window.open('{url}', '_blank')")
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(3)
        driver.close()

    def get_parse_result(self, hash: str) -> SolscanResult:
        if not self.driver:
            msg = "Please use context for the `SolscanParser`"
            logger.critical(msg)
            raise ValueError(msg)

        result = SolscanResult(date=datetime.now(), hash=hash)
        url = urljoin(self.url, hash)

        logger.info(f"Try parse: {result.hash}")

        driver = self.driver
        driver.get(url)

        self.fix_cf_just_moment(url, driver)
        driver.switch_to.window(driver.window_handles[0])

        try:
            result = self.parse_sol_values(result, driver)
            result = self.parse_spl_values(result, driver)
        except TimeoutException:
            logger.info(
                f"Can't found SQL Balance or Token values: {result.hash}"
            )
            pass

        return result

    def process_hashes(self):
        for hash in self.hashes:
            parse_result = self.get_parse_result(hash)
            self.google_sheets.manage_spreadsheet(parse_result)
