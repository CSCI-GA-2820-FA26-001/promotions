Feature: Delete Promotions through the Admin UI
    As an administrator of the Promotions service
    I need to delete Promotions through the browser
    So that I can remove Promotions that are no longer needed

    Scenario: Successfully delete a Promotion
        Given a Promotion exists for deletion
        And I am viewing the Promotions list
        When I select Delete for that Promotion
        And I confirm the deletion
        Then the Promotion no longer appears in the list
        And the UI indicates that the deletion succeeded

    Scenario: Cancel deleting a Promotion
        Given a Promotion exists for deletion
        And I am viewing the Promotions list
        When I select Delete for that Promotion
        And I cancel the deletion
        Then the Promotion remains in the list

    Scenario: Handle an unsuccessful deletion
        Given a Promotion exists for deletion
        And I am viewing the Promotions list
        And the delete request will fail
        When I select Delete for that Promotion
        And I confirm the deletion
        Then the UI displays a deletion error message
        And the UI does not indicate that the Promotion was deleted
