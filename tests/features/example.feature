Feature: Example feature
  To demonstrate the live dashboard

  Scenario: Successful addition
    Given I have numbers 1 and 2
    When I add them
    Then the result should be 3

  Scenario: Failing subtraction
    Given I have numbers 5 and 2
    When I subtract them
    Then the result should be 0
