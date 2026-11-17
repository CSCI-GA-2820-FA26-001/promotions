"""
Query Promotion UI steps for Behave tests
"""

from uuid import uuid4

# pylint: disable=not-callable
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions


def create_promotion_through_ui(
    context,
    promotion_type,
    value,
    product_id,
    active=True,
):
    """Create a Promotion entirely through the browser UI."""
    driver = context.driver

    driver.get(context.base_url)

    WebDriverWait(driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located(
            (By.ID, "create-promotion-form")
        )
    )

    promotion_name = f"BDD Query {uuid4().hex[:8]}"

    fields = {
        "name": promotion_name,
        "value": str(value),
        "product_id": str(product_id),
    }

    for field_name, field_value in fields.items():
        element = driver.find_element(By.NAME, field_name)
        element.clear()
        element.send_keys(field_value)

    Select(
        driver.find_element(By.NAME, "promotion_type")
    ).select_by_value(promotion_type)

    for field_name, field_value in {
        "start_date": "2026-11-01",
        "end_date": "2026-12-31",
    }.items():
        element = driver.find_element(By.NAME, field_name)
        driver.execute_script(
            "arguments[0].value = arguments[1];",
            element,
            field_value,
        )

    active_checkbox = driver.find_element(By.NAME, "active")

    if active_checkbox.is_selected() != active:
        active_checkbox.click()

    driver.find_element(
        By.CSS_SELECTOR,
        '[data-testid="create-button"]',
    ).click()

    WebDriverWait(driver, context.wait_seconds).until(
        lambda current_driver: current_driver.find_element(
            By.ID, "create-message"
        ).get_attribute("data-state") == "success"
    )

    return promotion_name


@given("multiple Promotions exist with different attributes")
def step_multiple_promotions_exist(context):
    """Create multiple Promotions with different searchable attributes."""
    create_promotion_through_ui(
        context,
        promotion_type="PERCENTAGE_OFF",
        value=20,
        product_id=101,
        active=True,
    )

    create_promotion_through_ui(
        context,
        promotion_type="AMOUNT_OFF",
        value=15,
        product_id=202,
        active=False,
    )


@given("Promotions exist in the system")
def step_promotions_exist(context):
    """Create a Promotion through the browser for the no-match scenario."""
    create_promotion_through_ui(
        context,
        promotion_type="PERCENTAGE_OFF",
        value=20,
        product_id=101,
        active=True,
    )


@given("I have filtered the Promotion list using a query")
def step_filtered_promotion_list(context):
    """Create Promotions and filter them through the Query UI."""
    create_promotion_through_ui(
        context,
        promotion_type="PERCENTAGE_OFF",
        value=20,
        product_id=101,
        active=True,
    )

    create_promotion_through_ui(
        context,
        promotion_type="AMOUNT_OFF",
        value=15,
        product_id=202,
        active=False,
    )

    context.driver.get(context.base_url)

    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located(
            (By.ID, "query-attribute")
        )
    )

    dropdown = Select(
        context.driver.find_element(By.ID, "query-attribute")
    )
    dropdown.select_by_visible_text("Promotion Type")

    search_input = context.driver.find_element(By.ID, "query-value")
    search_input.clear()
    search_input.send_keys("AMOUNT_OFF")

    context.driver.find_element(By.ID, "search-btn").click()

    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda driver: "Promotion(s) found."
        in driver.find_element(By.ID, "flash-message").text
    )


@given("I am on the Promotions admin page")
def step_on_promotions_admin_page(context):
    """Open the Promotions admin UI through Selenium."""
    context.driver.get(context.base_url)

    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located(
            (By.ID, "query-attribute")
        )
    )


@when('I select "{attribute}" as the search attribute')
def step_select_search_attribute(context, attribute):
    """Select the query attribute."""
    dropdown = Select(
        context.driver.find_element(By.ID, "query-attribute")
    )
    dropdown.select_by_visible_text(attribute)


@when('I enter "{value}" as the search value')
def step_enter_search_value(context, value):
    """Enter the query value."""
    search_input = context.driver.find_element(By.ID, "query-value")
    search_input.clear()
    search_input.send_keys(value)


@when("I submit the search")
def step_submit_search(context):
    """Submit the query through the UI."""
    context.driver.find_element(By.ID, "search-btn").click()


@then('only Promotions matching "{promotion_type}" are displayed')
def step_verify_matching_promotions(context, promotion_type):
    """Verify that all displayed Promotions match the query."""
    rows = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#promotion-list tr")
        )
    )

    assert rows

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        assert cells[2].text == promotion_type


@then("no Promotion records are displayed")
def step_verify_no_promotions(context):
    """Verify that no Promotion rows are displayed."""
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "flash-message"),
            "No matching Promotions were found.",
        )
    )

    rows = context.driver.find_elements(
        By.CSS_SELECTOR,
        "#promotion-list tr",
    )

    assert len(rows) == 0


@then("the UI indicates that no matching Promotions were found")
def step_verify_no_match_message(context):
    """Verify the no-match message."""
    message = context.driver.find_element(By.ID, "flash-message")

    assert message.text == "No matching Promotions were found."


@when("I clear the search criteria")
def step_clear_search(context):
    """Clear the Promotion query through the UI."""
    context.driver.find_element(By.ID, "clear-btn").click()


@then("the full Promotion list is displayed again")
def step_verify_full_list(context):
    """Verify that the full Promotion list is restored."""
    rows = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#promotion-list tr")
        )
    )

    assert len(rows) >= 2
