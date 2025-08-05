# Alexa Wake-on-LAN Lambda Function

An AWS Lambda function that enables Amazon Alexa to remotely wake up network devices using Wake-on-LAN through voice commands. 
This serverless function acts as a bridge between Alexa Skills and a Wake-on-LAN web service.

## Prerequisites

- AWS Account with Lambda access
- Amazon Developer Account for Alexa Skills
- Wake-on-LAN web service (compatible endpoint)
- Python 3.x runtime environment

## Architecture
Alexa Device → Alexa Skills Kit → AWS Lambda → Wake-on-LAN Service → Target Device

## Installation

### 1. Lambda Function Setup

1. Create a new AWS Lambda function
2. Choose Python 3.x runtime
3. Upload the function code
4. Configure environment variables (see Configuration section)
5. Set appropriate execution role with basic Lambda permissions

### 3. Alexa Skill Configuration

1. Create a new Alexa Skill in the Amazon Developer Console
2. Set the endpoint to your Lambda function ARN
3. Configure intents and utterances for wake commands
4. Enable the skill for testing

## Configuration

## Deployment

### Manual Deployment

Create deployment package:
`zip -r wake-on-lan-lambda.zip lambda_function.py`

### Environment Variables

Set the following environment variables in your Lambda function:

| Variable | Description | Required |
|----------|-------------|----------|
| `WOL_USERNAME` | Username for Wake-on-LAN service authentication | Yes |
| `WOL_PASSWORD` | Password for Wake-on-LAN service authentication | Yes |

### Setting Environment Variables in AWS Lambda

1. Go to your Lambda function in AWS Console
2. Navigate to "Configuration" → "Environment variables"
3. Add the required variables:
   - Key: `WOL_USERNAME`, Value: `your_username`
   - Key: `WOL_PASSWORD`, Value: `your_password`

## Usage

### Voice Commands

Once configured, you can use voice commands like:
- "Alexa, turn on my computer"
- "Alexa, wake up my PC"
- "Alexa, start my workstation"

### Alexa Responses

The function provides different responses based on the outcome:

- **Success**: "wooosh, computer should turn on now!"
- **HTTP Error**: "Computer went potato, have you tried switching on and off sir?"
- **Network/Exception Error**: "Uh, maybe your potato head didn't turn on raspberry pi zero?"

  Written by [@snackk](https://github.com/snackk).
