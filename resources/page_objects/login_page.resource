*** Settings ***
Documentation       Sign-in page locators and authentication actions.


*** Variables ***
${LOGIN_EMAIL}          css:[data-testid="login-email"]
${LOGIN_PASSWORD}       css:[data-testid="login-password"]
${LOGIN_SUBMIT}         css:[data-testid="login-submit"]
${LOGIN_ERROR}          css:[data-testid="login-error"]


*** Keywords ***
Open Sign-in Page
    [Documentation]    Navigate to the sign-in form and wait for its email field.
    Go To    ${PORTAL_URL}/login
    Wait Until Element Is Visible    ${LOGIN_EMAIL}

Sign In With Valid Credentials
    [Documentation]    Submit the configured member credentials without logging the password.
    Input Text    ${LOGIN_EMAIL}    ${PORTAL_USERNAME}
    Input Password    ${LOGIN_PASSWORD}    ${PORTAL_PASSWORD}
    Click Element    ${LOGIN_SUBMIT}

Sign In With Invalid Credentials
    [Documentation]    Submit the seeded disabled-member credentials.
    Input Text    ${LOGIN_EMAIL}    ${INVALID_EMAIL}
    Input Password    ${LOGIN_PASSWORD}    ${INVALID_PASSWORD}
    Click Element    ${LOGIN_SUBMIT}

Sign-in Error Should Be Visible
    [Documentation]    Verify that invalid authentication is rejected with a clear message.
    Wait Until Element Is Visible    ${LOGIN_ERROR}
    Element Text Should Be    ${LOGIN_ERROR}    Email or password is incorrect.

Benefits Dashboard Should Be Visible
    [Documentation]    Wait until the authenticated benefits dashboard is visible.
    Wait Until Element Is Visible    css:[data-testid="health-remaining"]
