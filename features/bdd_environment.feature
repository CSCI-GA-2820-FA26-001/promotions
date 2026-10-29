Feature: Promotions BDD testing environment
    As a developer
    I want Behave and Selenium to access the Promotions application
    So that Promotion UI workflows can be tested from the outside in

    Scenario: Access the Promotions application through Selenium
        When I open the Promotions application
        Then the application should be displayed in the browser