Feature: Read a Promotion in the admin UI
    As a Promotions administrator
    I need to view a saved Promotion's details
    So that I can inspect the record in a browser

    Scenario: View details for an existing Promotion
        Given an existing Promotion is available to view
        When I open its details page
        Then the saved Promotion details are displayed
