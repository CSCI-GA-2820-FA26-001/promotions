"""
BDD steps for deleting Promotions through the Admin UI.
"""

from uuid import uuid4

# pylint: disable=not-callable
from behave import given, when, then
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select, WebDriverWait


ROW = '[data-testid="promotion-row"]'
NAME = '[data-testid="promotion-name"]'
DELETE_BUTTON = '[data-testid="delete-promotion"]'


def find_promotion_row(driver, promotion_name):
    """Find a displayed Promotion row by its name."""
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, ROW)

        for row in rows:
            try:
                name = row.find_element(
                    By.CSS_SELECTOR,
                    NAME,
                ).text.strip()

                if name == promotion_name:
                    return row

            except StaleElementReferenceException:
                return None

    except StaleElementReferenceException:
        return None

    return None


def wait_for_promotion(context):
    """Wait until the test Promotion appears in the list."""
    return WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        lambda driver: find_promotion_row(
            driver,
            context.delete_promotion_name,
        )
    )


def reset_network_blocks(context):
    """Ensure browser network requests are not blocked."""
    context.driver.execute_cdp_cmd(
        "Network.enable",
        {},
    )
    context.driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {"urls": []},
    )


def cleanup_promotion(context):
    """Delete leftover test data through the browser UI."""
    reset_network_blocks(context)

    context.driver.get(context.base_url)

    try:
        row = WebDriverWait(
            context.driver,
            5,
        ).until(
            lambda driver: find_promotion_row(
                driver,
                context.delete_promotion_name,
            )
        )
    except Exception:  # pylint: disable=broad-exception-caught
        return

    row.find_element(
        By.CSS_SELECTOR,
        DELETE_BUTTON,
    ).click()

    alert = WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        expected_conditions.alert_is_present()
    )
    alert.accept()

    WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        lambda driver: find_promotion_row(
            driver,
            context.delete_promotion_name,
        )
        is None
    )


@given("a Promotion exists for deletion")
def step_promotion_exists_for_deletion(context):
    """Create a real Promotion using only the browser UI."""
    reset_network_blocks(context)

    context.driver.get(context.base_url)

    WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        expected_conditions.presence_of_element_located(
            (By.ID, "create-promotion-form")
        )
    )

    context.delete_promotion_name = (
        f"BDD Delete {uuid4().hex[:8]}"
    )

    fields = {
        "name": context.delete_promotion_name,
        "value": "20",
        "product_id": "101",
    }

    for field_name, value in fields.items():
        field = context.driver.find_element(
            By.NAME,
            field_name,
        )
        field.clear()
        field.send_keys(value)

    Select(
        context.driver.find_element(
            By.NAME,
            "promotion_type",
        )
    ).select_by_value("PERCENTAGE_OFF")

    for field_name, value in {
        "start_date": "2026-11-01",
        "end_date": "2026-12-31",
    }.items():
        field = context.driver.find_element(
            By.NAME,
            field_name,
        )
        context.driver.execute_script(
            "arguments[0].value = arguments[1];",
            field,
            value,
        )

    active = context.driver.find_element(
        By.NAME,
        "active",
    )

    if not active.is_selected():
        active.click()

    context.driver.find_element(
        By.CSS_SELECTOR,
        '[data-testid="create-button"]',
    ).click()

    WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        lambda driver: driver.find_element(
            By.ID,
            "create-message",
        ).get_attribute("data-state")
        == "success"
    )

    wait_for_promotion(context)

    context.add_cleanup(
        cleanup_promotion,
        context,
    )


@given("I am viewing the Promotions list")
def step_viewing_promotions_list(context):
    """Open the Admin UI and locate the test Promotion."""
    context.driver.get(context.base_url)
    wait_for_promotion(context)


@given("the delete request will fail")
def step_delete_request_fails(context):
    """Block the real DELETE request in the browser."""
    row = wait_for_promotion(context)

    promotion_id = row.find_element(
        By.CSS_SELECTOR,
        '[data-testid="promotion-id"]',
    ).text.strip()

    base_url = context.base_url.rstrip("/")

    context.driver.execute_cdp_cmd(
        "Network.enable",
        {},
    )
    context.driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {
            "urls": [
                f"{base_url}/api/promotions/{promotion_id}"
            ]
        },
    )


@when("I select Delete for that Promotion")
def step_select_delete(context):
    """Click Delete for the test Promotion."""
    row = wait_for_promotion(context)

    row.find_element(
        By.CSS_SELECTOR,
        DELETE_BUTTON,
    ).click()

    WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        expected_conditions.alert_is_present()
    )


@when("I confirm the deletion")
def step_confirm_delete(context):
    """Confirm the browser deletion dialog."""
    context.driver.switch_to.alert.accept()


@when("I cancel the deletion")
def step_cancel_delete(context):
    """Cancel the browser deletion dialog."""
    context.driver.switch_to.alert.dismiss()


@then("the Promotion no longer appears in the list")
def step_promotion_removed(context):
    """Verify that the deleted Promotion disappears."""
    WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        lambda driver: find_promotion_row(
            driver,
            context.delete_promotion_name,
        )
        is None
    )


@then("the UI indicates that the deletion succeeded")
def step_delete_success_message(context):
    """Verify the deletion success message."""
    message = WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        expected_conditions.presence_of_element_located(
            (By.ID, "delete-message")
        )
    )

    WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        lambda driver: message.get_attribute(
            "data-state"
        )
        == "success"
    )

    assert (
        message.text
        == "Promotion deleted successfully!"
    )


@then("the Promotion remains in the list")
def step_promotion_remains(context):
    """Verify cancellation does not delete the Promotion."""
    row = wait_for_promotion(context)

    assert row is not None


@then("the UI displays a deletion error message")
def step_delete_error_message(context):
    """Verify a failed deletion is reported."""
    message = WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        expected_conditions.presence_of_element_located(
            (By.ID, "delete-message")
        )
    )

    WebDriverWait(
        context.driver,
        context.wait_seconds,
    ).until(
        lambda driver: message.get_attribute(
            "data-state"
        )
        == "error"
    )

    assert message.text == "Unable to delete Promotion."


@then(
    "the UI does not indicate that the Promotion was deleted"
)
def step_no_delete_success(context):
    """Verify failure is not reported as a success."""
    message = context.driver.find_element(
        By.ID,
        "delete-message",
    )

    assert message.get_attribute("data-state") != "success"
