import asyncio
import time

import undetected_chromedriver as uc
from curl_cffi.requests import AsyncSession

UPDATED = {"status": False}
COOKIES = {}
COOKIES_URL = "https://solscan.io/account/"
ACCOUNT_HASH = "H6ahDptbaMtEp2Kk4CBVqHbUbZTj7WSxyPP5Yc8C7ngY"
API_ACCOUNT_URL = (
    "https://api.solscan.io/v2/account?address={account_hash}&cluster="
)
API_SPL_URL = "https://api.solscan.io/v2/account/v2/tokens?address={account_hash}&cluster="

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Apple WebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
HEADERS = {
    "au-be": "%10%06yQQwT%07zPY%04%1C",
    "referer": "https://solscan.io/",
    "origin": "https://solscan.io",
    "User-Agent": USER_AGENT,
}
MAX_RETRIES = 10


def get_cookies(url: str = COOKIES_URL):
    if not UPDATED["status"]:
        UPDATED["status"] = True
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--disable-popup-blocking")
        # chrome_options.add_argument("--headless")

        driver = uc.Chrome(use_subprocess=True, options=chrome_options)
        driver.get(url)
        driver.execute_script(f"window.open('{url}', '_blank')")
        time.sleep(10)

        cookies = driver.get_cookies()
        for item in cookies:
            if item.get("name") == "cf_clearance":
                COOKIES["cf_clearance"] = item.get("value")


async def get_request(num: int, hash: str, retry: int = 0):
    current_retry = retry
    if current_retry < MAX_RETRIES:
        async with AsyncSession() as client:
            try:
                account = await client.get(
                    API_ACCOUNT_URL.format(account_hash=hash),
                    headers=HEADERS,
                    cookies=COOKIES,
                    timeout=60,
                )
                spl = await client.get(
                    API_SPL_URL.format(account_hash=hash),
                    headers=HEADERS,
                    cookies=COOKIES,
                    timeout=60,
                )
                result = (account, spl)
                UPDATED["status"] = False
                print(f"#{num} - {account.status_code} - {spl.status_code}")
            except Exception:
                if not UPDATED["status"]:
                    # print(UPDATED["status"])
                    print(f"#{num} - Trying get new cookies")
                    get_cookies()
                result = await get_request(num, hash, current_retry + 1)

            return result
    return None


async def runner():
    # tasks = [get_request(i, API_URL) for i in range(100)]
    # await asyncio.gather(*tasks)
    result = await get_request(1, ACCOUNT_HASH)
    breakpoint()


if __name__ == "__main__":
    get_cookies()
    asyncio.run(runner())
