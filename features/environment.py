"""
Environment for Behave Testing
"""

from os import getenv

from selenium import webdriver

WAIT_SECONDS = int(getenv("WAIT_SECONDS", "30"))
BASE_URL = getenv("BASE_URL", "http://localhost:8080")
DRIVER = getenv("DRIVER", "chrome").lower()
SELENIUM_REMOTE_URL = getenv("SELENIUM_REMOTE_URL")


def before_all(context):
    """Executed once before all tests"""
    context.base_url = BASE_URL
    context.wait_seconds = WAIT_SECONDS

    if "firefox" in DRIVER:
        context.driver = get_firefox()
    else:
        context.driver = get_chrome()

    context.driver.implicitly_wait(context.wait_seconds)
    context.driver.set_window_size(1280, 1300)
    context.config.setup_logging()


def after_all(context):
    """Executed after all tests"""
    context.driver.quit()


def get_chrome():
    """Create a headless Chrome browser"""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    if SELENIUM_REMOTE_URL:
        return webdriver.Remote(
            command_executor=SELENIUM_REMOTE_URL,
            options=options,
        )
    return webdriver.Chrome(options=options)


def get_firefox():
    """Create a headless Firefox browser"""
    options = webdriver.FirefoxOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    if SELENIUM_REMOTE_URL:
        return webdriver.Remote(
            command_executor=SELENIUM_REMOTE_URL,
            options=options,
        )
    return webdriver.Firefox(options=options)


def after_scenario(context, scenario):
    """Remove browser mock after each scenario."""

    script_id = getattr(context, "list_fixture_script_id", None)

    if script_id:
        context.driver.execute_cdp_cmd(
            "Page.removeScriptToEvaluateOnNewDocument",
            {"identifier": script_id},
        )
