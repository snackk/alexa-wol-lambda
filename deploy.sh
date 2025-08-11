#!/usr/bin/env bash
set -euo pipefail   # exit on first error, undefined var, or pipeline error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="us-east-1"
AWS_PROFILE="snackk"
LAMBDA_ZIP_PATH="target/wake-on-lan-lambda.zip"

REQUIRED_VARS=("ALEXA_SKILL_ID" "WOL_USERNAME" "WOL_PASSWORD")

echo -e "${BLUE}🚀 Starting alexa-wol-lambda deploy...${NC}"

echo -e "${YELLOW}🔍 Validating environment variables...${NC}"
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo -e "${RED}❌ Error: Environment variable $var is not set${NC}"
        echo "Please set: export $var=\"your-value\""
        exit 1
    fi
    echo "✅ $var is set"
done

echo -e "${YELLOW}🔧 Configuring AWS environment...${NC}"
export AWS_DEFAULT_REGION="$AWS_REGION"
export AWS_PROFILE="$AWS_PROFILE"

if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: AWS credentials not configured or invalid${NC}"
    echo "Please configure AWS credentials for profile: $AWS_PROFILE"
    exit 1
fi
echo "✅ AWS credentials validated"

echo -e "${BLUE}🔧 Building Lambda package...${NC}"
mvn -q clean package

if [ ! -f "$LAMBDA_ZIP_PATH" ]; then
    echo -e "${RED}❌ Error: Lambda ZIP file not found: $LAMBDA_ZIP_PATH${NC}"
    echo "Maven build may have failed"
    exit 1
fi

file_size=$(du -h "$LAMBDA_ZIP_PATH" | cut -f1)
echo -e "${GREEN}✅ Lambda package created successfully ($file_size)${NC}"

echo -e "${BLUE}🏗️ Provisioning AWS resources with Terraform...${NC}"
pushd terraform >/dev/null

echo "📦 Initializing Terraform..."
terraform init -upgrade -input=false

echo "📋 Planning Terraform deployment..."
terraform plan -input=false \
  -var="alexa_skill_id=${ALEXA_SKILL_ID}" \
  -var="wol_username=${WOL_USERNAME}" \
  -var="wol_password=${WOL_PASSWORD}"

echo "🚀 Applying Terraform changes..."
terraform apply -auto-approve -input=false \
  -var="alexa_skill_id=${ALEXA_SKILL_ID}" \
  -var="wol_username=${WOL_USERNAME}" \
  -var="wol_password=${WOL_PASSWORD}"

if terraform output lambda_arn >/dev/null 2>&1; then
    LAMBDA_ARN=$(terraform output -raw lambda_arn)
    echo -e "${GREEN}📋 Lambda ARN: $LAMBDA_ARN${NC}"
else
    echo -e "${YELLOW}⚠️ Warning: Could not retrieve Lambda ARN${NC}"
fi

popd >/dev/null

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo
echo -e "${BLUE}📊 Next Steps:${NC}"
echo "1. Copy the Lambda ARN above"
echo "2. Update your Alexa skill endpoint in the Developer Console"
echo "3. Test your skill: 'Alexa, discover my devices'"
echo
echo -e "${BLUE}🔗 Lambda ARN for Alexa Console:${NC}"
echo "${LAMBDA_ARN:-"Run 'terraform output lambda_arn' in the terraform directory"}"
