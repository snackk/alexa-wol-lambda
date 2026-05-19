pipeline {
    agent any

    environment {
        // AWS and Maven configuration
        AWS_DEFAULT_REGION = 'eu-west-1'
        AWS_PROFILE = 'snackk'
        MAVEN_OPTS = '-Xmx1024m'

        // Tool versions
        MAVEN_VERSION = '3.9.4'
        TERRAFORM_VERSION = '1.9.2'
        NODE_VERSION = '18'

        // Deployment configuration
        LAMBDA_ZIP_PATH = 'target/wake-on-lan-lambda.zip'
        SKILL_MANIFEST_PATH = 'skill-package/skill.json'
    }

    tools {
        maven "${MAVEN_VERSION}"
        nodejs "${NODE_VERSION}"
    }

    parameters {
        choice(
            name: 'DEPLOYMENT_ENV',
            choices: ['dev', 'staging', 'prod'],
            description: 'Environment to deploy to'
        )
        booleanParam(
            name: 'FORCE_DEPLOY',
            defaultValue: false,
            description: 'Force deployment even if no changes detected'
        )
        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Skip Maven tests during build'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "🔄 Checking out source code..."
                    checkout scm

                    echo """
                    🏗️ Build Information:
                    - Branch: ${env.GIT_BRANCH}
                    - Commit: ${env.GIT_COMMIT?.take(8)}
                    - Environment: ${params.DEPLOYMENT_ENV}
                    - Force Deploy: ${params.FORCE_DEPLOY}
                    """
                }
            }
        }

        stage('Setup Tools') {
            parallel {
                stage('Install Terraform') {
                    steps {
                        script {
                            echo "📦 Installing Terraform ${TERRAFORM_VERSION}..."
                            sh """
                                if ! terraform version | grep -q '${TERRAFORM_VERSION}'; then
                                    wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
                                    unzip -o terraform_${TERRAFORM_VERSION}_linux_amd64.zip
                                    sudo mv terraform /usr/local/bin/
                                    rm -f terraform_${TERRAFORM_VERSION}_linux_amd64.zip
                                fi
                                terraform version
                            """
                        }
                    }
                }

                stage('Install JQ') {
                    steps {
                        script {
                            echo "📦 Installing jq..."
                            sh """
                                if ! command -v jq &> /dev/null; then
                                    sudo apt-get update && sudo apt-get install -y jq
                                fi
                                jq --version
                            """
                        }
                    }
                }
            }
        }

        stage('Build Lambda Package') {
            steps {
                script {
                    echo "🔧 Building Lambda package..."

                    def mvnCommand = "mvn clean package -q"
                    if (params.SKIP_TESTS) {
                        mvnCommand += " -DskipTests"
                    }

                    sh mvnCommand

                    sh """
                        if [ ! -f "${LAMBDA_ZIP_PATH}" ]; then
                            echo "❌ Lambda ZIP file not found: ${LAMBDA_ZIP_PATH}"
                            exit 1
                        fi
                        echo "✅ Lambda package created: \$(ls -lah ${LAMBDA_ZIP_PATH})"
                    """
                }
            }

            post {
                success {
                    archiveArtifacts artifacts: "${LAMBDA_ZIP_PATH}", fingerprint: true
                }
            }
        }

        stage('Terraform Plan') {
            steps {
                script {
                    echo "📋 Planning Terraform deployment..."
                    dir('terraform') {
                        sh """
                            terraform init -upgrade -input=false
                            terraform plan -input=false -out=tfplan
                        """
                    }
                }
            }

            post {
                always {
                    archiveArtifacts artifacts: 'terraform/tfplan', allowEmptyArchive: true
                }
            }
        }

        stage('Terraform Apply') {
            when {
                anyOf {
                    expression { params.FORCE_DEPLOY }
                    expression { params.DEPLOYMENT_ENV == 'dev' }
                    branch 'main'
                }
            }

            steps {
                script {
                    echo "🏗️ Deploying AWS resources with Terraform..."

                    dir('terraform') {
                        sh "terraform apply -auto-approve -input=false tfplan"

                        env.LAMBDA_ARN = sh(
                            script: "terraform output -raw lambda_arn",
                            returnStdout: true
                        ).trim()

                        echo "✅ Lambda deployed with ARN: ${env.LAMBDA_ARN}"
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                echo "🧹 Cleaning up workspace..."

                // Clean up temporary files
                sh """
                    rm -f terraform/tfplan
                    rm -f ${SKILL_MANIFEST_PATH}.backup
                    rm -f response.json
                """
            }
        }

        success {
            script {
                echo """
                ✅ Deployment Successful!

                📊 Summary:
                - Environment: ${params.DEPLOYMENT_ENV}
                - Lambda ARN: ${env.LAMBDA_ARN ?: 'Not deployed'}
                - Build Number: ${env.BUILD_NUMBER}
                - Git Commit: ${env.GIT_COMMIT?.take(8)}
                """
            }
        }

        failure {
            script {
                echo """
                ❌ Deployment Failed!

                Please check the build logs for details.
                Build: ${env.BUILD_URL}
                """
            }
        }

        unstable {
            script {
                echo "⚠️ Build completed with warnings"
            }
        }
    }
}
