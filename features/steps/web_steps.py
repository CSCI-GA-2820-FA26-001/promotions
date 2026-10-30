"""
Web Steps for Promotions BDD tests
"""

# pylint: disable=not-callable
from behave import when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


@when("I open the Promotions application")
def step_open_promotions_application(context):
    """Open the Promotions application using Selenium"""
    context.driver.get(context.base_url)


@then("the application should be displayed in the browser")
def step_application_displayed(context):
    """Verify that the application rendered in the browser"""
    body = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert body is not None
    assert body.text.strip()
