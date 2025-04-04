import json
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

SELENOID_URL = "http://selenoid:4444/wd/hub"

# Глобальный экземпляр драйвера
driver_instance = None


def get_driver(force_reset=False):
    global driver_instance
    if driver_instance is None or force_reset:
        if driver_instance is not None:
            try:
                driver_instance.quit()
            except Exception:
                pass
        chrome_options = Options()
        chrome_options.set_capability("browserName", "chrome")
        chrome_options.set_capability("browserVersion", "116.0")
        chrome_options.set_capability("selenoid:options", {
            "enableVNC": True,
            "enableVideo": False
        })
        driver_instance = webdriver.Remote(
            command_executor=SELENOID_URL,
            options=chrome_options
        )
    return driver_instance


def wait_for_json(driver, timeout):
    def condition(driver):
        text = driver.page_source.strip()
        if text.lower().startswith("<html"):
            match = re.search(r"<body.*?>(.*?)</body>", text, flags=re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1).strip()

        try:
            data = json.loads(text)

            return data  # Если JSON успешно распарсился, возвращаем данные
        except Exception:
            return False

    return WebDriverWait(driver, timeout).until(condition)


def get_cart_count_selenium(timeout=30):
    try:
        driver = get_driver()
        driver.get("https://ticket.hc-avto.ru/ru/cart/count")
        data = wait_for_json(driver, timeout)
        return data.get("count", 0)
    except Exception as e:
        try:
            driver = get_driver(force_reset=True)
            driver.get("https://ticket.hc-avto.ru/ru/cart/count")
            data = wait_for_json(driver, timeout)
            return data.get("count", 0)
        except Exception as inner_e:
            raise ValueError("Не удалось получить JSON с сайта повторно: " + str(inner_e))