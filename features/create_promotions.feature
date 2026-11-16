
Feature: Create Promotions through the Admin UI
  As a Promotions administrator
  I want to create promotions through the browser
  So that I can manage promotions easily

  Scenario: Successfully create a promotion
    Given I am on the Promotions creation page
    When I enter valid promotion details
    And I submit the create form
    Then I should see a creation success message
    And the new promotion should appear in the list
    And the saved promotion details should be correct

  Scenario: Create an inactive promotion
    Given I am on the Promotions creation page
    When I enter valid promotion details
    And I set the promotion to inactive
    And I submit the create form
    Then the new promotion should appear in the list
    And its active status should be False

  Scenario: Reject missing required information
    Given I am on the Promotions creation page
    When I submit the form without a promotion name
    Then I should see a required field validation message
    And no promotion should be created

  Scenario: Handle an unsuccessful creation
    Given I am on the Promotions creation page
    And the create request will fail
    When I enter valid promotion details
    And I submit the create form
    Then I should see a creation error message
    And I should not see a creation success message
