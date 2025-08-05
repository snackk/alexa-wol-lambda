#!/usr/bin/env bash
set -euo pipefail   # exit on first error, undefined var, or pipeline error

echo "🔧  Building Lambda package ..."
mvn -q clean package

echo "🏗️  ️Deploying AWS resources with Terraform ..."
pushd terraform >/dev/null
terraform init -upgrade -input=false
terraform apply -auto-approve -input=false
LAMBDA_ARN=$(terraform output -raw lambda_arn)
popd >/dev/null

echo "🔗  Updating skill manifest with Lambda ARN: $LAMBDA_ARN"
jq --arg arn "$LAMBDA_ARN" \
   '.manifest.apis.custom.endpoint.uri = $arn' \
   skill-package/skill.json > skill-package/skill.tmp
mv skill-package/skill.tmp skill-package/skill.json

echo "🚀  Deploying Alexa skill ..."
ask deploy

echo "✅  Deployment complete!"
