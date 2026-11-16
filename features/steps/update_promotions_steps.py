
"""BDD steps for updating promotions through the Admin UI."""

from uuid import uuid4

from behave import given, when, then
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait


ROW = '[data-testid="promotion-row"]'


def get_test_row(context):
    """Find the promotion created for this test."""

    def find_row(driver):
        try:
            for row in driver.find_elements(By.CSS_SELECTOR, ROW):
                promotion_id = row.find_element(
                    By.CSS_SELECTOR, '[data-testid="promotion-id"]'
                ).text

                if promotion_id == context.promotion_id:
                    return row
        except StaleElementReferenceException:
            return False

        return False

    return WebDriverWait(
        context.driver, 10, poll_frequency=0.1
    ).until(find_row)


def get_cell(row, field):
    """Read a field from the displayed promotion row."""
    return row.find_element(
        By.CSS_SELECTOR,
        f'[data-testid="promotion-{field}"]'
    ).text


def create_test_promotion(context):
    """Create test data using the browser UI only."""
    driver = context.driver
    driver.get(context.base_url)

    WebDriverWait(driver, 10).until(
    lambda d: d.find_element(
        By.ID, "create-promotion-form"
    ).is_displayed()
)

    form = driver.find_element(By.ID, "create-promotion-form")

    context.original_name = "BDD Update " + uuid4().hex[:8]
    context.original_value = 20.0

    form.find_element(
        By.NAME, "name"
    ).send_keys(context.original_name)

    Select(
        form.find_element(By.NAME, "promotion_type")
    ).select_by_value("PERCENTAGE_OFF")

    form.find_element(By.NAME, "value").send_keys("20")
    form.find_element(By.NAME, "product_id").send_keys("101")

    for field, value in {
        "start_date": "2026-11-01",
        "end_date": "2026-12-31",
    }.items():
        driver.execute_script(
            "arguments[0].value = arguments[1];",
            form.find_element(By.NAME, field),
            value,
        )

    form.find_element(
        By.CSS_SELECTOR, '[data-testid="create-button"]'
    ).click()

    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(
            By.ID, "create-message"
        ).get_attribute("data-state") == "success"
    )

    def find_new_row(d):
        try:
            for row in d.find_elements(By.CSS_SELECTOR, ROW):
                if get_cell(row, "name") == context.original_name:
                    return row
        except StaleElementReferenceException:
            return False
        return False

    row = WebDriverWait(driver, 10).until(find_new_row)
    context.promotion_id = get_cell(row, "id")


def open_edit_form(context):
    """Open the editor for this test promotion."""
    row = get_test_row(context)

    row.find_element(
        By.CSS_SELECTOR, '[data-testid="edit-button"]'
    ).click()

    WebDriverWait(context.driver, 10).until(
        lambda d: d.find_element(
            By.ID, "edit-promotion-form"
        ).is_displayed()
    )


def prepare_editor(context):
    """Create a promotion and open its editor."""
    create_test_promotion(context)
    open_edit_form(context)


@given("a promotion exists in the admin UI")
def step_existing_promotion(context):
    create_test_promotion(context)


@when("I click Edit for that promotion")
def step_click_edit(context):
    open_edit_form(context)


@then("the edit form should show its current details")
def step_verify_edit_form(context):
    form = context.driver.find_element(
        By.ID, "edit-promotion-form"
    )

    assert form.find_element(
        By.NAME, "name"
    ).get_attribute("value") == context.original_name

    assert float(
        form.find_element(
            By.NAME, "value"
        ).get_attribute("value")
    ) == context.original_value

    assert Select(
        form.find_element(By.NAME, "promotion_type")
    ).first_selected_option.get_attribute("value") == "PERCENTAGE_OFF"


@given("I am editing an existing promotion")
def step_edit_existing(context):
    prepare_editor(context)


@given("I am editing an existing PERCENTAGE_OFF promotion")
def step_edit_percentage(context):
    prepare_editor(context)


@when('I change the promotion name to "{new_name}"')
def step_change_name(context, new_name):
    context.expected_name = new_name

    form = context.driver.find_element(
        By.ID, "edit-promotion-form"
    )

    field = form.find_element(By.NAME, "name")
    field.clear()
    field.send_keys(new_name)


@when("I click Save")
def step_save(context):
    context.driver.find_element(
        By.CSS_SELECTOR, '[data-testid="save-button"]'
    ).click()


@then("I should see a success message")
def step_success(context):
    WebDriverWait(context.driver, 10).until(
        lambda d: d.find_element(
            By.ID, "edit-message"
        ).get_attribute("data-state") == "success"
    )

    message = context.driver.find_element(
        By.ID, "edit-message"
    )

    assert "updated successfully" in message.text.lower()


@then('the promotion name should be "{expected_name}"')
def step_updated_name(context, expected_name):
    row = get_test_row(context)
    assert get_cell(row, "name") == expected_name


@then("the updated name should remain after reloading")
def step_persisted_name(context):
    context.driver.refresh()

    row = get_test_row(context)

    assert get_cell(row, "name") == context.expected_name


@when("I click Cancel")
def step_cancel(context):
    context.driver.find_element(
        By.CSS_SELECTOR, '[data-testid="cancel-button"]'
    ).click()


@then("the original promotion name should remain unchanged")
def step_cancel_unchanged(context):
    section = context.driver.find_element(
        By.ID, "edit-section"
    )
    assert not section.is_displayed()

    row = get_test_row(context)
    assert get_cell(row, "name") == context.original_name

    context.driver.refresh()
    row = get_test_row(context)
    assert get_cell(row, "name") == context.original_name


@when("I change its discount value to 150")
def step_invalid_value(context):
    form = context.driver.find_element(
        By.ID, "edit-promotion-form"
    )

    field = form.find_element(By.NAME, "value")
    field.clear()
    field.send_keys("150")


@then("I should see an error message")
def step_update_error(context):
    WebDriverWait(context.driver, 10).until(
        lambda d: d.find_element(
            By.ID, "edit-message"
        ).get_attribute("data-state") == "error"
    )

    message = context.driver.find_element(
        By.ID, "edit-message"
    )
    assert "update failed" in message.text.lower()


@then("I should not see a success message")
def step_no_update_success(context):
    message = context.driver.find_element(
        By.ID, "edit-message"
    )

    assert message.get_attribute("data-state") != "success"
    assert "updated successfully" not in message.text.lower()


@then("the original promotion details should remain unchanged")
def step_original_details(context):
    context.driver.refresh()

    row = get_test_row(context)

    assert get_cell(row, "name") == context.original_name
    assert float(get_cell(row, "value")) == context.original_value
    assert get_cell(row, "promotion_type") == "PERCENTAGE_OFF"
