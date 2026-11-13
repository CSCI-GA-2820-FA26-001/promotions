
Feature: List Promotions through the Admin UI
  As a Promotions administrator
  I want to view all promotions in the browser
  So that I can browse and manage promotion records

  Scenario: Display existing promotions
    Given multiple promotions exist in the system
    When I open the Promotions admin page
    Then all promotions should appear in the list
    And their details should be displayed correctly

  Scenario: Display an empty promotion list
    Given no promotions exist in the system
    When I open the Promotions admin page
    Then I should see an empty promotion list
    And I should see a no promotions message

  Scenario: Handle a failed list request
    Given the Promotions API is unavailable
    When I open the Promotions admin page
    Then I should see an error message for the list

