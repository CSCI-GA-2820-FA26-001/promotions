"""BDD steps for performing Promotion actions through the Admin UI."""

from uuid import uuid4

from behave import given, then, when
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


ROW = '[data-testid="promotion-row"]'


def cleanup_promotions_through_swagger(driver, base_url, promotion_ids):
    """Delete BDD-created Promotions through the browser-based Swagger UI."""
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
                        By.CSS_SELECTOR,
                        f"{selector} .live-responses-table tbody .response-col_status",
                    )
                    if item.text.strip()
                ),
                False,
            )
        )
        assert status.split()[0] == "204", f"Failed to delete Promotion {promotion_id}: {status}"


def find_promotion_row(context):
    """Find the created Promotion's row in the browser list."""

    def find_row(driver):
        try:
            for row in driver.find_elements(By.CSS_SELECTOR, ROW):
                name = row.find_element(By.CSS_SELECTOR, '[data-testid="promotion-name"]').text
                if name == context.promotion_name:
                    return row
        except StaleElementReferenceException:
            return False
        return False

    return WebDriverWait(context.driver, context.wait_seconds, poll_frequency=0.1).until(find_row)


def create_promotion_through_admin_ui(context, active):
    """Create a test Promotion through the Admin Create form."""
    driver = context.driver
    context.promotion_name = f"BDD Action {uuid4().hex[:8]}"
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
    if active_checkbox.is_selected() != active:
        active_checkbox.click()

    driver.find_element(By.CSS_SELECTOR, '[data-testid="create-button"]').click()
    wait.until(
        lambda page: page.find_element(By.ID, "create-message").get_attribute("data-state")
        == "success"
    )

    row = find_promotion_row(context)
    context.promotion_id = row.find_element(By.CSS_SELECTOR, '[data-testid="promotion-id"]').text
    context.created_promotion_ids.append(context.promotion_id)


def promotion_action_button(context, action):
    """Find and validate the requested action button for the created record."""
    row = find_promotion_row(context)
    button = row.find_element(By.CSS_SELECTOR, '[data-testid="promotion-action"]')
    assert button.get_attribute("data-action") == action
    return button


@given("an inactive Promotion is available in the Admin UI")
def step_inactive_promotion_available(context):
    create_promotion_through_admin_ui(context, active=False)


@given("an active Promotion is available in the Admin UI")
def step_active_promotion_available(context):
    create_promotion_through_admin_ui(context, active=True)


@when("I activate it from the Promotion list")
def step_activate_promotion(context):
    promotion_action_button(context, "activate").click()


@when("I deactivate it from the Promotion list")
def step_deactivate_promotion(context):
    promotion_action_button(context, "deactivate").click()


@when("I deactivate it while the action service is unavailable")
def step_deactivate_unavailable(context):
    """Simulate a failed action response inside the browser."""
    context.driver.execute_script(
        """
        const originalFetch = window.fetch.bind(window);
        window.fetch = (input, options = {}) => {
            const target = typeof input === "string" ? input : input.url;
            const url = new URL(target, window.location.href);
            const method = (options.method || "GET").toUpperCase();

            if (method === "PUT" && url.pathname.endsWith("/deactivate")) {
                return Promise.resolve(new Response(JSON.stringify({
                    message: "The action service is temporarily unavailable."
                }), {
                    status: 503,
                    headers: {"Content-Type": "application/json"}
                }));
            }

            return originalFetch(input, options);
        };
        """
    )
    promotion_action_button(context, "deactivate").click()


def assert_promotion_state(context, expected_active):
    """Check the action result and persisted state through the browser UI."""
    row = find_promotion_row(context)
    actual_active = row.find_element(By.CSS_SELECTOR, '[data-testid="promotion-active"]').text
    assert actual_active.lower() == str(expected_active).lower()
    expected_action = "Deactivate" if expected_active else "Activate"
    button = row.find_element(By.CSS_SELECTOR, '[data-testid="promotion-action"]')
    assert button.text == expected_action


@then("the Promotion is active and the action succeeds")
def step_promotion_activated(context):
    message = WebDriverWait(context.driver, context.wait_seconds).until(
        lambda page: page.find_element(By.ID, "action-message")
        if page.find_element(By.ID, "action-message").get_attribute("data-state") == "success"
        else False
    )
    assert message.get_attribute("data-state") == "success"
    assert message.text == f"Promotion {context.promotion_id} activated successfully."
    assert_promotion_state(context, True)

    context.driver.refresh()
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda page: page.find_element(By.ID, "list-message").text != "Loading promotions..."
    )
    assert_promotion_state(context, True)


@then("the Promotion is inactive and the action succeeds")
def step_promotion_deactivated(context):
    message = WebDriverWait(context.driver, context.wait_seconds).until(
        lambda page: page.find_element(By.ID, "action-message")
        if page.find_element(By.ID, "action-message").get_attribute("data-state") == "success"
        else False
    )
    assert message.get_attribute("data-state") == "success"
    assert message.text == f"Promotion {context.promotion_id} deactivated successfully."
    assert_promotion_state(context, False)

    context.driver.refresh()
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda page: page.find_element(By.ID, "list-message").text != "Loading promotions..."
    )
    assert_promotion_state(context, False)


@then("an action error is displayed and the Promotion remains active")
def step_action_failed(context):
    message = WebDriverWait(context.driver, context.wait_seconds).until(
        lambda page: page.find_element(By.ID, "action-message")
        if page.find_element(By.ID, "action-message").get_attribute("data-state") == "error"
        else False
    )
    assert message.text == (
        f"Unable to deactivate Promotion {context.promotion_id}: "
        "The action service is temporarily unavailable."
    )
    assert_promotion_state(context, True)

    context.driver.refresh()
    WebDriverWait(context.driver, context.wait_seconds).until(
        lambda page: page.find_element(By.ID, "list-message").text != "Loading promotions..."
    )
    assert_promotion_state(context, True)
