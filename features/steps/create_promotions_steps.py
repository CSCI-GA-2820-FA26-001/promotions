
"""BDD tests for creating promotions through Selenium."""

from uuid import uuid4
from selenium.common.exceptions import StaleElementReferenceException
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait


ROW = '[data-testid="promotion-row"]'
NAME = '[data-testid="promotion-name"]'


def wait_for_list(context):
    """Wait until the list finishes loading."""
    WebDriverWait(context.driver, 10).until(
        lambda driver: driver.find_element(
            By.ID, "list-message"
        ).text != "Loading promotions..."
    )


def fill_form(context, name):
    """Fill the creation form through the browser."""
    driver = context.driver

    fields = {
        "name": name,
        "value": "20",
        "product_id": "101",
    }

    for field, value in fields.items():
        element = driver.find_element(By.NAME, field)
        element.clear()
        if value:
            element.send_keys(value)

    Select(
        driver.find_element(By.NAME, "promotion_type")
    ).select_by_value("PERCENTAGE_OFF")

    # Set HTML date input values in the browser.
    for field, value in {
        "start_date": "2026-11-01",
        "end_date": "2026-12-31",
    }.items():
        element = driver.find_element(By.NAME, field)
        driver.execute_script(
            "arguments[0].value = arguments[1];",
            element,
            value,
        )


def get_created_row(context):
    """Wait for creation to finish and find the new promotion."""

    WebDriverWait(context.driver, 10).until(
        lambda driver: driver.find_element(
            By.ID, "create-message"
        ).get_attribute("data-state") == "success"
    )

    def find_row(driver):
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, ROW)

            for row in rows:
                name = row.find_element(
                    By.CSS_SELECTOR, NAME
                ).text

                if name == context.promotion_name:
                    return row

        except StaleElementReferenceException:
            return False

        return False

    return WebDriverWait(
        context.driver, 10, poll_frequency=0.1
    ).until(find_row)


def get_cell(row, field):
    """Read a cell from the displayed promotion."""
    return row.find_element(
        By.CSS_SELECTOR,
        f'[data-testid="promotion-{field}"]'
    ).text


@given("I am on the Promotions creation page")
def step_open_create(context):
    context.driver.execute_cdp_cmd("Network.enable", {})
    context.driver.execute_cdp_cmd(
        "Network.setBlockedURLs", {"urls": []}
    )

    context.driver.get(context.base_url)

    WebDriverWait(context.driver, 10).until(
        lambda driver: driver.find_element(
            By.ID, "create-promotion-form"
        )
    )

    wait_for_list(context)

    context.original_count = len(
        context.driver.find_elements(By.CSS_SELECTOR, ROW)
    )
    context.should_fail = False


@given("the create request will fail")
def step_prepare_failure(context):
    context.should_fail = True


@when("I enter valid promotion details")
def step_enter_valid(context):
    context.promotion_name = (
        "BDD Create " + uuid4().hex[:8]
    )
    fill_form(context, context.promotion_name)


@when("I set the promotion to inactive")
def step_set_inactive(context):
    checkbox = context.driver.find_element(
        By.NAME, "active"
    )
    if checkbox.is_selected():
        checkbox.click()


@when("I submit the create form")
def step_submit_create(context):
    if context.should_fail:
        # Simulate a failed API request in Chrome.
        base = context.base_url.rstrip("/")
        context.driver.execute_cdp_cmd(
            "Network.setBlockedURLs",
            {
                "urls": [
                    f"{base}/promotions*",
                    f"{base}/api/promotions*",
                ]
            },
        )

    context.driver.find_element(
        By.CSS_SELECTOR,
        '[data-testid="create-button"]'
    ).click()


@when("I submit the form without a promotion name")
def step_missing_name(context):
    fill_form(context, "")
    context.driver.find_element(
        By.CSS_SELECTOR,
        '[data-testid="create-button"]'
    ).click()


@then("I should see a creation success message")
def step_create_success(context):
    WebDriverWait(context.driver, 10).until(
        lambda driver: driver.find_element(
            By.ID, "create-message"
        ).get_attribute("data-state") == "success"
    )

    message = context.driver.find_element(
        By.ID, "create-message"
    )
    assert "Promotion created successfully" in message.text


@then("the new promotion should appear in the list")
def step_new_promotion_displayed(context):
    row = get_created_row(context)
    assert get_cell(row, "name") == context.promotion_name


@then("the saved promotion details should be correct")
def step_verify_created_details(context):
    row = get_created_row(context)

    assert get_cell(row, "promotion_type") == "PERCENTAGE_OFF"
    assert float(get_cell(row, "value")) == 20.0
    assert get_cell(row, "product_id") == "101"
    assert get_cell(row, "start_date") == "2026-11-01"
    assert get_cell(row, "end_date") == "2026-12-31"
    assert get_cell(row, "active").lower() == "true"


@then("its active status should be False")
def step_verify_inactive(context):
    row = get_created_row(context)
    assert get_cell(row, "active").lower() == "false"


@then("I should see a required field validation message")
def step_required_validation(context):
    message = WebDriverWait(context.driver, 10).until(
        lambda driver: driver.find_element(
            By.ID, "create-message"
        )
        if driver.find_element(
            By.ID, "create-message"
        ).get_attribute("data-state") == "error"
        else False
    )

    assert "name" in message.text.lower()


@then("no promotion should be created")
def step_no_promotion_created(context):
    current_count = len(
        context.driver.find_elements(By.CSS_SELECTOR, ROW)
    )
    assert current_count == context.original_count


@then("I should see a creation error message")
def step_creation_error(context):
    try:
        message = WebDriverWait(context.driver, 10).until(
            lambda driver: driver.find_element(
                By.ID, "create-message"
            )
            if driver.find_element(
                By.ID, "create-message"
            ).get_attribute("data-state") == "error"
            else False
        )
        assert message.text.strip()
    finally:
        # Restore networking for other BDD scenarios.
        context.driver.execute_cdp_cmd(
            "Network.setBlockedURLs", {"urls": []}
        )


@then("I should not see a creation success message")
def step_no_success_message(context):
    message = context.driver.find_element(
        By.ID, "create-message"
    )
    assert message.get_attribute("data-state") != "success"
    assert "created successfully" not in message.text.lower()
