*** Settings ***
Documentation       Shared lifecycle, browser setup, and reusable page objects.

Variables           ../config/local.py
Library             OperatingSystem
Library             String
Library             SeleniumLibrary    timeout=${TIMEOUT}
Library             libraries.portal_library.PortalLibrary
Resource            page_objects/login_page.resource
Resource            page_objects/benefits_page.resource
Resource            page_objects/claim_page.resource


*** Keywords ***
Prepare Portal
    [Documentation]    Validate runtime settings and start or check the selected portal.
    Validate Configuration
    ...    ${BROWSER}
    ...    ${PORTAL_URL}
    ...    ${PORTAL_USERNAME}
    ...    ${PORTAL_PASSWORD}
    ...    ${TIMEOUT}
    ...    ${WINDOW_SIZE}
    ...    ${CI}
    IF    not $PORTAL_URL
        ${local_url}=    Start Mock Portal
        VAR    ${PORTAL_URL}    ${local_url}    scope=SUITE
    END
    Wait For Portal Health    ${PORTAL_URL}    ${TIMEOUT}

Prepare Test
    [Documentation]    Reset local state and open a fresh configured browser.
    Reset Portal State    ${PORTAL_URL}
    Create Directory    ${OUTPUT DIR}${/}screenshots
    ${options}=    Get Browser Options    ${BROWSER}    ${HEADLESS}    ${CI}
    Open Browser    ${PORTAL_URL}    ${BROWSER}    options=${options}
    ${dimensions}=    Split String    ${WINDOW_SIZE}    x
    Set Window Size    ${dimensions}[0]    ${dimensions}[1]

Finish Test
    [Documentation]    Capture a failed browser state and close all browser sessions.
    ${browser_ids}=    Get Browser Ids
    IF    $browser_ids
        IF    '${TEST STATUS}' == 'FAIL'
            ${screenshot_name}=    Safe Screenshot Name    ${TEST NAME}
            Capture Page Screenshot
            ...    ${OUTPUT DIR}${/}screenshots${/}${screenshot_name}.png
        END
        Close All Browsers
    END
