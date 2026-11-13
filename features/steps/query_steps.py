"""
Query Promotion UI steps for Behave tests
"""

# pylint: disable=not-callable
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions


@given("I am on the Promotions admin page")
def step_on_promotions_admin_page(context):
    """Open the Promotions admin UI through Selenium"""
    context.driver.get(context.base_url)

    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located((By.ID, "query-attribute"))
    )


@when('I select "{attribute}" as the search attribute')
def step_select_search_attribute(context, attribute):
    """Select the query attribute"""
    dropdown = Select(context.driver.find_element(By.ID, "query-attribute"))
    dropdown.select_by_visible_text(attribute)


@when('I enter "{value}" as the search value')
def step_enter_search_value(context, value):
    """Enter the query value"""
    search_input = context.driver.find_element(By.ID, "query-value")
    search_input.clear()
    search_input.send_keys(value)


@when("I submit the search")
def step_submit_search(context):
    """Submit the query through the UI"""
    context.driver.find_element(By.ID, "search-btn").click()


@then('only Promotions matching "{promotion_type}" are displayed')
def step_verify_matching_promotions(context, promotion_type):
    """Verify that all displayed Promotions match the query"""
    rows = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#search-results tr")
        )
    )

    assert rows

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        assert cells[2].text == promotion_type


@then("no Promotion records are displayed")
def step_verify_no_promotions(context):
    """Verify that no Promotion rows are displayed"""
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "flash-message"),
            "No matching Promotions were found.",
        )
    )

    rows = context.driver.find_elements(By.CSS_SELECTOR, "#search-results tr")

    assert len(rows) == 0


@then("the UI indicates that no matching Promotions were found")
def step_verify_no_match_message(context):
    """Verify the no-match message"""
    message = context.driver.find_element(By.ID, "flash-message")

    assert message.text == "No matching Promotions were found."


@when("I clear the search criteria")
def step_clear_search(context):
    """Clear the Promotion query through the UI"""
    context.driver.find_element(By.ID, "clear-btn").click()


@then("the full Promotion list is displayed again")
def step_verify_full_list(context):
    """Verify that the full Promotion list is restored"""
    rows = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#search-results tr")
        )
    )

    assert len(rows) >= 2
