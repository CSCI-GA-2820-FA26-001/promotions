"""Selenium steps for viewing a Promotion in the admin UI."""

from uuid import uuid4
from urllib.parse import quote

from behave import given, then, when
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


def cleanup_promotions_through_swagger(driver, base_url, promotion_ids):
    """Delete BDD-created records through the browser-based Swagger UI."""
    wait = WebDriverWait(driver, 20)

    for promotion_id in promotion_ids:
        driver.get(f"{base_url.rstrip('/')}/apidocs/")
        selector = ".opblock-delete"
        tag = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".opblock-tag")))

        if not driver.execute_script(
            "return Boolean(document.querySelector(arguments[0]));",
            f"{selector} .opblock-summary",
        ):
            tag.click()

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{selector} .opblock-summary"))).click()

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{selector} .try-out__btn"))).click()

        field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{selector} .parameters input")))

        field.clear()
        field.send_keys(str(promotion_id))

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{selector} button.execute"))).click()
        status = wait.until(
            lambda page: next(
                (
                    item.text.strip()
                    for item in page.find_elements(
                        By.CSS_SELECTOR, f"{selector} .live-responses-table " "tbody .response-col_status"
                    )
                    if item.text.strip()
                ),
                False,
            )
        )
        assert status.split()[0] == "204", f"Failed to delete Promotion {promotion_id}: {status}"


@given("an existing Promotion is available to view")
def step_existing_promotion_is_available(context):
    """Create a Promotion through the Admin UI for this browser scenario."""
    driver = context.driver
    context.promotion_name = f"BDD Read {uuid4().hex[:8]}"
    context.created_promotion_ids = []
    context.add_cleanup(
        cleanup_promotions_through_swagger,
        driver,
        context.base_url,
        context.created_promotion_ids,
    )

    driver.get(context.base_url)
    wait = WebDriverWait(driver, context.wait_seconds)
    wait.until(EC.visibility_of_element_located((By.ID, "create-promotion-form")))

    form = driver.find_element(By.ID, "create-promotion-form")
    form.find_element(By.NAME, "name").send_keys(context.promotion_name)
    Select(form.find_element(By.NAME, "promotion_type")).select_by_value("PERCENTAGE_OFF")
    form.find_element(By.NAME, "value").send_keys("15")
    form.find_element(By.NAME, "product_id").send_keys("81240")

    for field, value in {
        "start_date": "2026-11-01",
        "end_date": "2026-12-31",
    }.items():
        driver.execute_script(
            "arguments[0].value = arguments[1];",
            form.find_element(By.NAME, field),
            value,
        )

    active_checkbox = form.find_element(By.NAME, "active")
    if active_checkbox.is_selected():
        active_checkbox.click()

    driver.find_element(By.CSS_SELECTOR, '[data-testid="create-button"]').click()
    wait.until(
        lambda page: page.find_element(By.ID, "create-message").get_attribute("data-state")
        == "success"
    )

    def find_created_row(page):
        try:
            for row in page.find_elements(By.CSS_SELECTOR, '[data-testid="promotion-row"]'):
                name = row.find_element(By.CSS_SELECTOR, '[data-testid="promotion-name"]').text
                if name == context.promotion_name:
                    return row
        except StaleElementReferenceException:
            return False
        return False

    row = WebDriverWait(driver, context.wait_seconds, poll_frequency=0.1).until(find_created_row)
    context.promotion_id = row.find_element(
        By.CSS_SELECTOR,
        '[data-testid="promotion-id"]',
    ).text
    context.created_promotion_ids.append(context.promotion_id)


@when("I open its details page")
def step_open_promotion_details(context):
    """Navigate to the Promotion details view with Selenium."""
    url = f"{context.base_url.rstrip('/')}/?id={quote(context.promotion_id)}"
    context.driver.get(url)


@then("the saved Promotion details are displayed")
def step_saved_promotion_details_are_displayed(context):
    """Verify the details view rendered every saved field in the browser."""
    wait = WebDriverWait(context.driver, context.wait_seconds)
    wait.until(
        EC.text_to_be_present_in_element(
            (By.ID, "lookup-status"),
            f"Promotion {context.promotion_id} loaded.",
        )
    )

    details = context.driver.find_element(By.ID, "promotion-details")
    assert details.is_displayed()
    assert context.driver.find_element(By.ID, "promotion-id").text == context.promotion_id

    expected_values = {
        "promotion-name": context.promotion_name,
        "promotion-type": "PERCENTAGE_OFF",
        "promotion-value": "15",
        "promotion-product-id": "81240",
        "promotion-start-date": "2026-11-01",
        "promotion-end-date": "2026-12-31",
        "promotion-active": "Inactive",
    }
    for field_id, expected in expected_values.items():
        actual = context.driver.find_element(By.ID, field_id).text
        assert actual == expected, f"Expected {field_id} to be {expected!r}, got {actual!r}"

    for field_id in ("promotion-created-at", "promotion-updated-at"):
        assert context.driver.find_element(By.ID, field_id).text
