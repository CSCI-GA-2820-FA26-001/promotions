
"""BDD steps for the Promotions List UI."""

import json

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

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
        lambda driver: driver.find_element(
            By.ID, "list-message"
        ).text == "No promotions available."
    )

    row_count = context.driver.execute_script(
        'return document.querySelectorAll('
        '"[data-testid=promotion-row]").length'
    )
    assert row_count == 0


@then("I should see a no promotions message")
def step_no_promotions_message(context):
    """Verify the empty state message."""
    message = context.driver.find_element(
        By.ID, "list-message"
    )
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
    """Prepare two promotions for the browser UI test."""

    promotions = [
        {
            "id": 1001,
            "name": "BDD Summer Sale",
            "promotion_type": "PERCENTAGE_OFF",
            "value": 20,
            "product_id": 101,
            "start_date": "2026-11-01",
            "end_date": "2026-12-31",
            "active": True,
        },
        {
            "id": 1002,
            "name": "BDD Winter Sale",
            "promotion_type": "AMOUNT_OFF",
            "value": 15,
            "product_id": 102,
            "start_date": "2026-11-01",
            "end_date": "2026-12-31",
            "active": True,
        },
    ]

    use_promotions_fixture(context, promotions)



@then("all promotions should appear in the list")
def step_all_promotions_displayed(context):
    """Verify both prepared promotions are listed."""
    rows = context.driver.find_elements(
        By.CSS_SELECTOR,
        '[data-testid="promotion-row"]'
    )

    names = [
        row.find_element(
            By.CSS_SELECTOR,
            '[data-testid="promotion-name"]'
        ).text
        for row in rows
    ]

    assert len(rows) == 2
    assert "BDD Summer Sale" in names
    assert "BDD Winter Sale" in names


@then("their details should be displayed correctly")
def step_promotion_details(context):
    """Verify the displayed promotion fields."""
    rows = context.driver.find_elements(
        By.CSS_SELECTOR,
        '[data-testid="promotion-row"]'
    )

    expected = {
        "BDD Summer Sale": ("PERCENTAGE_OFF", 20, 101),
        "BDD Winter Sale": ("AMOUNT_OFF", 15, 102),
    }

    for row in rows:
        name = row.find_element(
            By.CSS_SELECTOR,
            '[data-testid="promotion-name"]'
        ).text

        promotion_type = row.find_element(
            By.CSS_SELECTOR,
            '[data-testid="promotion-promotion_type"]'
        ).text

        value = row.find_element(
            By.CSS_SELECTOR,
            '[data-testid="promotion-value"]'
        ).text

        product_id = row.find_element(
            By.CSS_SELECTOR,
            '[data-testid="promotion-product_id"]'
        ).text

        assert name in expected
        expected_type, expected_value, expected_product = expected[name]

        assert promotion_type == expected_type
        assert float(value) == expected_value
        assert int(product_id) == expected_product

        assert row.find_element(
            By.CSS_SELECTOR,
            '[data-testid="promotion-start_date"]'
        ).text == "2026-11-01"

        assert row.find_element(
            By.CSS_SELECTOR,
            '[data-testid="promotion-end_date"]'
        ).text == "2026-12-31"
