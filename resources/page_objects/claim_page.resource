*** Settings ***
Documentation       Claim form locators, input actions, and result assertions.


*** Variables ***
${CLAIM_TYPE}               css:[data-testid="claim-type"]
${CLAIM_AMOUNT}             css:[data-testid="claim-amount"]
${CLAIM_DATE}               css:[data-testid="claim-date"]
${CLAIM_DESCRIPTION}        css:[data-testid="claim-description"]
${CLAIM_SUBMIT}             css:[data-testid="claim-submit"]
${CLAIM_ERROR}              css:[data-testid="claim-error"]
${CLAIM_CONFIRMATION}       css:[data-testid="claim-confirmation"]
${DASHBOARD_NAVIGATION}     css:[data-testid="dashboard-navigation"]


*** Keywords ***
Fill Claim Form
    [Documentation]    Populate all claim fields with the provided test data.
    [Arguments]    ${coverage}    ${amount}    ${service_date}    ${description}
    Select From List By Value    ${CLAIM_TYPE}    ${coverage}
    Input Text    ${CLAIM_AMOUNT}    ${amount}
    ${date_input}=    Get WebElement    ${CLAIM_DATE}
    Execute Javascript
    ...    ARGUMENTS    ${date_input}    ${service_date}
    ...    JAVASCRIPT
    ...    arguments[0].value = arguments[1];
    ...    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
    ...    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
    Input Text    ${CLAIM_DESCRIPTION}    ${description}

Submit Claim
    [Documentation]    Submit the visible claim form.
    Click Element    ${CLAIM_SUBMIT}

Submit Claim With Required Fields Removed
    [Documentation]    Bypass browser-required checks to exercise server-side validation.
    Execute Javascript
    ...    document.querySelectorAll(
    ...    '[data-testid="claim-type"], [data-testid="claim-amount"],'
    ...    + '[data-testid="claim-date"], [data-testid="claim-description"]'
    ...    ).forEach((element) => element.removeAttribute('required'))
    Click Element    ${CLAIM_SUBMIT}

Claim Error Should Be
    [Documentation]    Verify the exact server-side claim validation message.
    [Arguments]    ${expected}
    Wait Until Element Is Visible    ${CLAIM_ERROR}
    Element Text Should Be    ${CLAIM_ERROR}    ${expected}

Claim Confirmation Should Be
    [Documentation]    Verify the successful claim confirmation message.
    [Arguments]    ${expected}
    Wait Until Element Is Visible    ${CLAIM_CONFIRMATION}
    Element Text Should Be    ${CLAIM_CONFIRMATION}    ${expected}

Return To Benefits Dashboard
    [Documentation]    Return from the claim confirmation to the balance dashboard.
    Click Element    ${DASHBOARD_NAVIGATION}
    Wait Until Element Is Visible    ${HEALTH_REMAINING}
