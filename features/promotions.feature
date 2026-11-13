Feature: Query Promotions through the admin UI
    As an administrator of the Promotions service
    I need to search for Promotions using their attributes
    So that I can quickly find Promotions matching specific criteria

    Scenario: Search Promotions by a supported attribute
        Given multiple Promotions exist with different attributes
        And I am on the Promotions admin page
        When I select "Promotion Type" as the search attribute
        And I enter "AMOUNT_OFF" as the search value
        And I submit the search
        Then only Promotions matching "AMOUNT_OFF" are displayed

    Scenario: Search with no matching Promotions
        Given Promotions exist in the system
        And I am on the Promotions admin page
        When I select "Product ID" as the search attribute
        And I enter "999999" as the search value
        And I submit the search
        Then no Promotion records are displayed
        And the UI indicates that no matching Promotions were found

    Scenario: Clear the search criteria
        Given I have filtered the Promotion list using a query
        When I clear the search criteria
        Then the full Promotion list is displayed again
