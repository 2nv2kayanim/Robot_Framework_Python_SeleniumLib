pipeline {
    agent {
        label 'linux-python-browser'
    }

    options {
        timeout(time: 120, unit: 'MINUTES')
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '20'))
        disableConcurrentBuilds(abortPrevious: false)
    }

    parameters {
        string(name: 'GIT_REF', defaultValue: 'refs/heads/main', description: 'Exact Git branch, tag, or pull-request ref to test.')
        string(name: 'GIT_SHA', defaultValue: '', description: 'Optional triggering commit SHA used to verify checkout.')
        string(name: 'REPO_URL', defaultValue: '', description: 'Git repository URL supplied by the caller.')
        choice(name: 'BROWSER', choices: ['chrome', 'firefox'], description: 'Browser used by SeleniumLibrary.')
        string(name: 'PORTAL_URL', defaultValue: '', description: 'Blank starts the local mock; otherwise use a disposable external test portal.')
        string(name: 'TAGS', defaultValue: '', description: 'Optional Robot tag expression.')
        booleanParam(name: 'USE_EXTERNAL_CREDENTIALS', defaultValue: false, description: 'Bind external test credentials from Jenkins.')
    }

    environment {
        CI = 'true'
        HEADLESS = 'true'
        BROWSER = "${params.BROWSER}"
        PORTAL_URL = "${params.PORTAL_URL}"
        TAGS = "${params.TAGS}"
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    if (!params.REPO_URL?.trim()) {
                        error('REPO_URL is required.')
                    }
                    def remote = [
                        url: params.REPO_URL,
                        refspec: '+refs/heads/*:refs/remotes/origin/* +refs/pull/*:refs/remotes/origin/pr/*'
                    ]
                    if (env.REPO_CREDENTIALS_ID?.trim()) {
                        remote.credentialsId = env.REPO_CREDENTIALS_ID
                    }
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: params.GIT_REF]],
                        userRemoteConfigs: [remote]
                    ])
                }
                script {
                    if (params.GIT_SHA?.trim()) {
                        def checkedOutSha = sh(
                            script: 'git rev-parse HEAD',
                            returnStdout: true
                        ).trim()
                        if (checkedOutSha != params.GIT_SHA) {
                            error("Checkout SHA ${checkedOutSha} does not match requested GIT_SHA.")
                        }
                    }
                }
            }
        }

        stage('Setup venv and install') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/python -m pip install --upgrade pip
                    .venv/bin/python -m pip install -r requirements.lock.txt
                '''
            }
        }

        stage('Lint, typecheck, and unit tests') {
            steps {
                sh '''
                    .venv/bin/python -m ruff check libraries mock_portal config tests_unit
                    .venv/bin/python -m robocop check --ignore SPC03 --ignore MISC04 --ignore VAR05 resources tests
                    .venv/bin/python -m robotidy --check resources tests
                    .venv/bin/python -m mypy
                    .venv/bin/python -m pytest
                '''
            }
        }

        stage('Robot tests') {
            steps {
                script {
                    if (params.USE_EXTERNAL_CREDENTIALS) {
                        if (!params.PORTAL_URL?.trim()) {
                            error('PORTAL_URL is required when USE_EXTERNAL_CREDENTIALS is true.')
                        }
                        withCredentials([
                            string(credentialsId: 'benefits-test-email', variable: 'PORTAL_USERNAME'),
                            string(credentialsId: 'benefits-test-password', variable: 'PORTAL_PASSWORD')
                        ]) {
                            runRobotTests()
                        }
                    } else {
                        runRobotTests()
                    }
                }
            }
        }

        stage('Publish') {
            steps {
                echo 'Robot and Allure reports are published from the always post condition.'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'results/**', allowEmptyArchive: true
            script {
                if (fileExists('results/output.xml')) {
                    step([
                        $class: 'RobotPublisher',
                        outputPath: 'results',
                        outputFileName: 'output.xml',
                        reportFileName: 'report.html',
                        logFileName: 'log.html',
                        disableArchiveOutput: false
                    ])
                }
            }
            script {
                if (fileExists('results/allure-results')) {
                    try {
                        allure includeProperties: false, results: [[path: 'results/allure-results']]
                    } catch (NoSuchMethodError error) {
                        echo 'Allure Jenkins plugin is not installed; Allure JSON remains archived.'
                    }
                }
            }
            cleanWs()
        }
    }
}

def runRobotTests() {
    sh '''
        mkdir -p results/allure-results
        if [ -n "$TAGS" ]; then
            .venv/bin/python libraries/run_robot.py --include "$TAGS" --outputdir results tests/group_benefits.robot
        else
            .venv/bin/python libraries/run_robot.py --outputdir results tests/group_benefits.robot
        fi
    '''
}
