*** Settings ***
Documentation       Coverage dashboard locators and balance assertions.


*** Variables ***
${HEALTH_LIMIT}         css:[data-testid="health-limit"]
${HEALTH_REMAINING}     css:[data-testid="health-remaining"]
${DENTAL_LIMIT}         css:[data-testid="dental-limit"]
${DENTAL_REMAINING}     css:[data-testid="dental-remaining"]
${CLAIM_NAVIGATION}     css:[data-testid="claim-navigation"]


*** Keywords ***
Health Coverage Should Show Seeded Balances
    [Documentation]    Verify the seeded health limit and remaining balance.
    Wait Until Element Is Visible    ${HEALTH_REMAINING}
    Element Text Should Be    ${HEALTH_LIMIT}    $2,500.00
    Element Text Should Be    ${HEALTH_REMAINING}    $1,200.00

Dental Coverage Should Show Seeded Balances
    [Documentation]    Verify the seeded dental limit and remaining balance.
    Wait Until Element Is Visible    ${DENTAL_REMAINING}
    Element Text Should Be    ${DENTAL_LIMIT}    $1,500.00
    Element Text Should Be    ${DENTAL_REMAINING}    $800.00

Open Claim Form
    [Documentation]    Navigate from the dashboard to the claim form.
    Click Element    ${CLAIM_NAVIGATION}
    Wait Until Element Is Visible    css:[data-testid="claim-submit"]

Health Remaining Balance Should Be
    [Documentation]    Assert the displayed health remaining balance.
    [Arguments]    ${expected}
    Wait Until Element Is Visible    ${HEALTH_REMAINING}
    Element Text Should Be    ${HEALTH_REMAINING}    ${expected}

Dental Remaining Balance Should Be
    [Documentation]    Assert the displayed dental remaining balance.
    [Arguments]    ${expected}
    Wait Until Element Is Visible    ${DENTAL_REMAINING}
    Element Text Should Be    ${DENTAL_REMAINING}    ${expected}
