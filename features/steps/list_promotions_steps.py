"""BDD steps for the Promotions List UI."""

import json
from uuid import uuid4

from behave import given, when, then
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def open_swagger_post(driver, base_url):
    """Open the real Swagger POST form using Selenium."""
    driver.get(f"{base_url.rstrip('/')}/apidocs/")

    wait = WebDriverWait(driver, 20)
    selector = ".opblock-post"

    # Expand the promotions group if it is collapsed.
    tag = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".opblock-tag")))

    if not driver.execute_script(
        "return Boolean(document.querySelector(arguments[0]));",
        ".opblock-post .opblock-summary",
    ):
        tag.click()

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{selector} .opblock-summary"))).click()

    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{selector} .try-out__btn"))).click()

    return selector


def create_promotion_via_swagger(driver, base_url, promotion):
    """Create a real Promotion through the Swagger browser UI."""
    selector = open_swagger_post(driver, base_url)
    wait = WebDriverWait(driver, 20)

    # Find the editable JSON request body.
    body = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"{selector} textarea.body-param__text")))

    # Enter the promotion details.
    body.clear()
    body.send_keys(json.dumps(promotion))

    # Execute the real POST request.
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{selector} button.execute"))).click()

    # Verify the actual HTTP 201 response.
    status = wait.until(
        lambda d: next(
            (
                item.text.strip()
                for item in d.find_elements(By.CSS_SELECTOR, f"{selector} .live-responses-table tbody .response-col_status")
                if item.text.strip()
            ),
            False,
        )
    )

    assert status.split()[0] == "201", f"Expected HTTP 201, got {status}"

    # Read the real record created by PostgreSQL.
    response = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, f"{selector} .live-responses-table " ".response-col_description pre")
        )
    )

    created = json.loads(response.text)

    assert created["name"] == promotion["name"]
    assert created.get("id") is not None

    return created


def cleanup_test_promotions(driver, base_url, promotion_ids):
    """Delete test promotions through the real Swagger UI."""
    wait = WebDriverWait(driver, 20)

    for promotion_id in promotion_ids:
        driver.get(f"{base_url.rstrip('/')}/apidocs/")
        selector = ".opblock-delete"

        # Expand the promotions group if collapsed.
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
            lambda d: next(
                (
                    item.text.strip()
                    for item in d.find_elements(
                        By.CSS_SELECTOR, f"{selector} .live-responses-table " "tbody .response-col_status"
                    )
                    if item.text.strip()
                ),
                False,
            )
        )

        assert status.split()[0] == "204", f"Failed to delete Promotion {promotion_id}: {status}"


def use_promotions_fixture(context, promotions):
    """Mock the List API response inside Chrome only."""

    source = """
    (() => {
        const promotions = __PROMOTIONS__;
        const originalFetch = window.fetch.bind(window);

        window.fetch = function(input, options) {
            const target = typeof input === "string" ? input : input.url;
            const url = new URL(target, window.location.href);
            const method = (
                options && options.method ? options.method : "GET"
            ).toUpperCase();

            if (url.pathname === "/api/promotions" && method === "GET") {
                return Promise.resolve(
                    new Response(JSON.stringify(promotions), {
                        status: 200,
                        headers: {"Content-Type": "application/json"}
                    })
                );
            }

            return originalFetch(input, options);
        };
    })();
    """

    source = source.replace("__PROMOTIONS__", json.dumps(promotions))

    result = context.driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": source},
    )
    context.list_fixture_script_id = result["identifier"]


@given("no promotions exist in the system")
def step_empty_promotions(context):
    """Prepare an empty List API response in the browser."""
    use_promotions_fixture(context, [])


@when("I open the Promotions admin page")
def step_open_admin(context):
    """Open the admin UI in the browser."""
    context.driver.get(context.base_url)


@then("I should see an empty promotion list")
def step_empty_list(context):
    """Verify no promotion rows are displayed."""
    WebDriverWait(context.driver, 10).until(
        lambda driver: driver.find_element(By.ID, "list-message").text == "No promotions available."
    )

    row_count = context.driver.execute_script("return document.querySelectorAll(" '"[data-testid=promotion-row]").length')
    assert row_count == 0


@then("I should see a no promotions message")
def step_no_promotions_message(context):
    """Verify the empty state message."""
    message = context.driver.find_element(By.ID, "list-message")
    assert message.text == "No promotions available."


@given("the Promotions API is unavailable")
def step_api_unavailable(context):
    """Simulate an API failure in the Chrome browser."""
    base = context.base_url.rstrip("/")

    context.driver.execute_cdp_cmd("Network.enable", {})
    context.driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {
            "urls": [
                f"{base}/promotions*",
                f"{base}/api/promotions*",
            ]
        },
    )


@then("I should see an error message for the list")
def step_list_error(context):
    """Verify the UI shows an error when loading fails."""
    try:
        message = WebDriverWait(context.driver, 10).until(
            lambda driver: driver.find_element(
                By.CSS_SELECTOR,
                '[data-testid="list-error"]',
            )
        )

        assert message.text == "Unable to load promotions."

        rows = context.driver.find_elements(
            By.CSS_SELECTOR,
            '[data-testid="promotion-row"]',
        )
        assert len(rows) == 0

    finally:
        context.driver.execute_cdp_cmd(
            "Network.setBlockedURLs",
            {"urls": []},
        )


@given("multiple promotions exist in the system")
def step_multiple_promotions(context):
    """Create real Promotions through Selenium and Swagger UI."""

    suffix = uuid4().hex[:8]

    context.expected_promotions = [
        {
            "name": f"BDD Summer {suffix}",
            "promotion_type": "PERCENTAGE_OFF",
            "value": 20,
            "product_id": 101,
            "start_date": "2026-11-01",
            "end_date": "2026-12-31",
            "active": True,
        },
        {
            "name": f"BDD Winter {suffix}",
            "promotion_type": "AMOUNT_OFF",
            "value": 15,
            "product_id": 102,
            "start_date": "2026-11-01",
            "end_date": "2026-12-31",
            "active": True,
        },
    ]

    context.created_promotion_ids = []

    context.add_cleanup(
        cleanup_test_promotions,
        context.driver,
        context.base_url,
        context.created_promotion_ids,
    )

    for promotion in context.expected_promotions:
        created = create_promotion_via_swagger(
            context.driver,
            context.base_url,
            promotion,
        )

        promotion["id"] = created["id"]
        context.created_promotion_ids.append(created["id"])


@then("all promotions should appear in the list")
def step_all_promotions_displayed(context):
    """Wait for the real promotions to appear in the list."""

    expected_names = {promotion["name"] for promotion in context.expected_promotions}

    def promotions_loaded(driver):
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, '[data-testid="promotion-row"]')

            actual_names = {row.find_element(By.CSS_SELECTOR, '[data-testid="promotion-name"]').text.strip() for row in rows}

            return expected_names.issubset(actual_names)

        except StaleElementReferenceException:
            return False

    WebDriverWait(context.driver, 20).until(promotions_loaded)


@then("their details should be displayed correctly")
def step_promotion_details(context):
    """Verify the real promotion details in the Admin table."""

    rows = context.driver.find_elements(By.CSS_SELECTOR, '[data-testid="promotion-row"]')

    for expected in context.expected_promotions:
        matched_row = None

        for row in rows:
            name = row.find_element(By.CSS_SELECTOR, '[data-testid="promotion-name"]').text.strip()

            if name == expected["name"]:
                matched_row = row
                break

        assert matched_row is not None, f"Promotion not found: {expected['name']}"

        def get_cell(field):
            return matched_row.find_element(By.CSS_SELECTOR, f'[data-testid="promotion-{field}"]').text.strip()

        assert int(get_cell("id")) == expected["id"]
        assert get_cell("name") == expected["name"]

        assert get_cell("promotion_type") == expected["promotion_type"]

        assert float(get_cell("value")) == expected["value"]

        assert int(get_cell("product_id")) == expected["product_id"]

        assert get_cell("start_date") == expected["start_date"]
        assert get_cell("end_date") == expected["end_date"]

        assert get_cell("active").lower() == "true"
