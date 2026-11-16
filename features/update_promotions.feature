
Feature: Update Promotions through the Admin UI
  As a Promotions administrator
  I want to edit an existing promotion
  So that I can keep promotion details accurate

  Scenario: Open a promotion for editing
    Given a promotion exists in the admin UI
    When I open the Promotions admin page
    And I click Edit for that promotion
    Then the edit form should show its current details

  Scenario: Successfully update a promotion
    Given I am editing an existing promotion
    When I change the promotion name to "Updated Promotion"
    And I click Save
    Then I should see a success message
    And the promotion name should be "Updated Promotion"
    And the updated name should remain after reloading

  Scenario: Cancel editing
    Given I am editing an existing promotion
    When I change the promotion name to "Not Saved"
    And I click Cancel
    Then the original promotion name should remain unchanged

  Scenario: Handle an unsuccessful update
    Given I am editing an existing PERCENTAGE_OFF promotion
    When I change its discount value to 150
    And I click Save
    Then I should see an error message
    And I should not see a success message
    And the original promotion details should remain unchanged
