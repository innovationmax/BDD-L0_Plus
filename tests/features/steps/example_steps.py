from behave import given, when, then
from behave.runner import Context

@given('I have numbers {a:d} and {b:d}')
def step_given_numbers(context: Context, a, b):
    context.a = a
    context.b = b

@when('I add them')
def step_when_add(context: Context):
    context.result = context.a + context.b

@when('I subtract them')
def step_when_subtract(context: Context):
    context.result = context.a - context.b

@then('the result should be {expected:d}')
def step_then_result(context: Context, expected):
    assert context.result == expected, f"Expected {expected}, got {context.result}"
