*** Settings ***
Documentation       End-to-end tests for the local Group Benefits Portal demonstration mock.

Resource            ../resources/common.resource

Suite Setup         Prepare Portal
Suite Teardown      Stop Mock Portal
Test Setup          Prepare Test
Test Teardown       Finish Test


*** Test Cases ***
Valid Member Can Sign In
    [Documentation]    Given a seeded member, when they sign in, then the benefits dashboard opens.
    [Tags]    smoke    auth    regression
    Given The Member Opens The Sign-in Page
    When The Member Signs In With Valid Credentials
    Then The Benefits Dashboard Should Be Visible

Invalid Credentials Are Rejected
    [Documentation]    Given invalid test credentials, when submitted, then authentication is denied.
    [Tags]    auth    negative
    Given The Member Opens The Sign-in Page
    When The Member Signs In With Invalid Credentials
    Then The Sign-in Error Should Be Visible

Health Coverage Shows Its Seeded Limit And Remaining Balance
    [Documentation]    Given an authenticated member, then the seeded health totals are displayed.
    [Tags]    smoke    balance    health    regression
    Given The Member Is Signed In
    Then Health Coverage Should Show Seeded Balances

Dental Coverage Shows Its Seeded Limit And Remaining Balance
    [Documentation]    Given an authenticated member, then the seeded dental totals are displayed.
    [Tags]    balance    dental
    Given The Member Is Signed In
    Then Dental Coverage Should Show Seeded Balances

Successful Health Claim Reduces The Health Balance
    [Documentation]    Given a member with health coverage, when a valid claim is submitted, the balance decreases.
    [Tags]    smoke    claim    health    regression
    Given The Member Is Signed In
    When The Member Submits A Health Claim For 125 Dollars
    Then The Health Claim Is Confirmed And The Remaining Balance Is 1075 Dollars

Successful Dental Claim Reduces The Dental Balance
    [Documentation]    Given a member with dental coverage, when a valid claim is submitted, the balance decreases.
    [Tags]    claim    dental
    Given The Member Is Signed In
    When The Member Submits A Dental Claim For 75 Dollars
    Then The Dental Claim Is Confirmed And The Remaining Balance Is 725 Dollars

Claim Above The Coverage Balance Is Rejected
    [Documentation]    Given a health balance, when a larger claim is submitted, then it is rejected unchanged.
    [Tags]    claim    negative    health    regression
    Given The Member Is Signed In
    When The Member Submits A Health Claim For 1250 Dollars
    Then The Over-limit Error Is Shown And The Health Balance Is Unchanged

Claim Equal To The Remaining Health Balance Succeeds
    [Documentation]    Given the full seeded health balance, when exactly that amount is claimed, it succeeds.
    [Tags]    claim    health    regression
    Given The Member Is Signed In
    When The Member Submits A Health Claim For The Exact Remaining Balance
    Then The Exact-balance Health Claim Succeeds

Claim One Cent Above The Remaining Health Balance Is Rejected
    [Documentation]    Given the seeded health balance, then one cent above it is rejected.
    [Tags]    claim    negative    health    regression
    Given The Member Is Signed In
    When The Member Submits A Health Claim For One Cent Above The Remaining Balance
    Then The Over-limit Error Is Shown And The Health Balance Is Unchanged

Zero Amount Claim Is Rejected
    [Documentation]    Given the claim form, when a zero amount is submitted, then validation rejects it.
    [Tags]    claim    negative    health    regression
    Given The Member Is Signed In
    When The Member Submits A Zero-dollar Health Claim
    Then The Positive-amount Validation Error Is Shown

Negative Amount Claim Is Rejected
    [Documentation]    Given the claim form, when a negative amount is submitted, then validation rejects it.
    [Tags]    claim    negative    health    regression
    Given The Member Is Signed In
    When The Member Submits A Negative-dollar Health Claim
    Then The Positive-amount Validation Error Is Shown

Claim With Missing Required Fields Is Rejected
    [Documentation]    Given an empty claim form, when client checks are bypassed, then server validation rejects it.
    [Tags]    claim    negative    regression
    Given The Member Is Signed In
    When The Member Submits A Claim With Required Fields Missing
    Then The Required-fields Validation Error Is Shown


*** Keywords ***
The Member Opens The Sign-in Page
    [Documentation]    Navigate to the member sign-in page.
    Open Sign-in Page

The Member Signs In With Valid Credentials
    [Documentation]    Authenticate with the active seeded member.
    Sign In With Valid Credentials

The Member Signs In With Invalid Credentials
    [Documentation]    Attempt sign-in with the disabled seeded member.
    Sign In With Invalid Credentials

The Sign-in Error Should Be Visible
    [Documentation]    Verify the authentication error message.
    Sign-in Error Should Be Visible

The Benefits Dashboard Should Be Visible
    [Documentation]    Verify that the member dashboard is open.
    Benefits Dashboard Should Be Visible

The Member Is Signed In
    [Documentation]    Sign in and wait for the dashboard before a scenario.
    Open Sign-in Page
    Sign In With Valid Credentials
    Benefits Dashboard Should Be Visible

The Member Submits A Health Claim For 125 Dollars
    [Documentation]    Submit a valid health claim for one hundred twenty-five dollars.
    Open Claim Form
    Fill Claim Form    health    125.00    2026-10-28    Routine health visit
    Submit Claim

The Health Claim Is Confirmed And The Remaining Balance Is 1075 Dollars
    [Documentation]    Verify the health confirmation and updated remaining balance.
    Claim Confirmation Should Be    Health claim submitted successfully.
    Return To Benefits Dashboard
    Health Remaining Balance Should Be    $1,075.00

The Member Submits A Dental Claim For 75 Dollars
    [Documentation]    Submit a valid dental claim for seventy-five dollars.
    Open Claim Form
    Fill Claim Form    dental    75.00    2026-10-28    Routine dental visit
    Submit Claim

The Dental Claim Is Confirmed And The Remaining Balance Is 725 Dollars
    [Documentation]    Verify the dental confirmation and updated remaining balance.
    Claim Confirmation Should Be    Dental claim submitted successfully.
    Return To Benefits Dashboard
    Dental Remaining Balance Should Be    $725.00

The Member Submits A Health Claim For 1250 Dollars
    [Documentation]    Submit a health claim above the seeded remaining amount.
    Open Claim Form
    Fill Claim Form    health    1250.00    2026-10-28    Over-limit health claim
    Submit Claim

The Member Submits A Health Claim For The Exact Remaining Balance
    [Documentation]    Submit a health claim equal to the full seeded remaining amount.
    Open Claim Form
    Fill Claim Form    health    1200.00    2026-10-28    Full remaining health balance
    Submit Claim

The Member Submits A Health Claim For One Cent Above The Remaining Balance
    [Documentation]    Submit a health claim one cent above the seeded remaining amount.
    Open Claim Form
    Fill Claim Form    health    1200.01    2026-10-28    One cent over health balance
    Submit Claim

The Over-limit Error Is Shown And The Health Balance Is Unchanged
    [Documentation]    Verify an over-limit error and ensure the balance is unchanged.
    Claim Error Should Be    Claim amount exceeds remaining health coverage balance of $1,200.00.
    Go To    ${PORTAL_URL}/benefits
    Health Remaining Balance Should Be    $1,200.00

The Exact-balance Health Claim Succeeds
    [Documentation]    Verify an exact-balance claim succeeds and consumes the balance.
    Claim Confirmation Should Be    Health claim submitted successfully.
    Return To Benefits Dashboard
    Health Remaining Balance Should Be    $0.00

The Member Submits A Zero-dollar Health Claim
    [Documentation]    Submit a health claim with an invalid zero amount.
    Open Claim Form
    Fill Claim Form    health    0.00    2026-10-28    Zero amount validation
    Submit Claim

The Member Submits A Negative-dollar Health Claim
    [Documentation]    Submit a health claim with an invalid negative amount.
    Open Claim Form
    Fill Claim Form    health    -1.00    2026-10-28    Negative amount validation
    Submit Claim

The Positive-amount Validation Error Is Shown
    [Documentation]    Verify the server rejects zero and negative claim amounts.
    Claim Error Should Be    Claim amount must be greater than zero.

The Member Submits A Claim With Required Fields Missing
    [Documentation]    Submit an empty form after bypassing browser-side required checks.
    Open Claim Form
    Submit Claim With Required Fields Removed

The Required-fields Validation Error Is Shown
    [Documentation]    Verify the server rejects a claim with missing required fields.
    Claim Error Should Be    Please complete all required fields.
