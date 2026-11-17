Feature: Perform actions on Promotions in the Admin UI
  As a Promotions manager
  I want to activate or deactivate a Promotion from the admin page
  So that I can manage its active status without using the REST API directly

  Scenario: Activate an inactive Promotion
    Given an inactive Promotion is available in the Admin UI
    When I activate it from the Promotion list
    Then the Promotion is active and the action succeeds

  Scenario: Deactivate an active Promotion
    Given an active Promotion is available in the Admin UI
    When I deactivate it from the Promotion list
    Then the Promotion is inactive and the action succeeds

  Scenario: Keep the Promotion unchanged when an action fails
    Given an active Promotion is available in the Admin UI
    When I deactivate it while the action service is unavailable
    Then an action error is displayed and the Promotion remains active
