import json
import os
import requests
import uuid
from datetime import datetime

status_url = "http://snackk-media.ddns.net:80/check-emby"
wake_url = "http://snackk-media.ddns.net:80/wake"

username = os.environ.get('WOL_USERNAME')
password = os.environ.get('WOL_PASSWORD')

def lambda_handler(event, context):
    directive = event['directive']
    header = directive['header']
    namespace = header['namespace']
    name = header['name']

    if namespace == "Alexa.Discovery":
        return handle_discovery(directive)
    elif namespace == "Alexa.PowerController":
        return handle_power_control(directive)
    elif namespace == "Alexa":
        if name == "ReportState":
            return handle_report_state(directive)

    return build_error_response(directive, "INVALID_DIRECTIVE", "Directive not supported")

def handle_discovery(directive):
    device = {
        "endpointId": "snackk-alexa-wol",
        "manufacturerName": "Diogo Santos",
        "description": "snackk-media",
        "friendlyName": "snackk-media",
        "displayCategories": ["SWITCH"],
        "additionalAttributes": {
            "manufacturer": "Diogo Santos",
            "model": "Wake on Lan",
            "serialNumber": "12345678901234567890",
            "firmwareVersion": "1.0",
            "softwareVersion": "1.0",
            "customIdentifier": "Wake On Lan"
        },
        "capabilities": [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        {"name": "powerState"}
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa",
                "version": "3"
            }
        ]
    }

    response = {
        "event": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "Discover.Response",
                "payloadVersion": "3",
                "messageId": str(uuid.uuid4())
            },
            "payload": {
                "endpoints": [device]
            }
        }
    }

    return response

def handle_power_control(directive):
    header = directive['header']
    endpoint_id = directive['endpoint']['endpointId']
    name = header['name']

    if name == "TurnOn":
        try:
            wol_response = requests.post(wake_url, auth=(username, password), timeout=10)
            print(f"wol response {wol_response}")
            power_state = "ON" if wol_response.status_code == 200 else "OFF"
        except requests.RequestException:
            power_state = "OFF"
    elif name == "TurnOff":
        # Cannot actually turn off a server remotely via WoL, so just report OFF
        power_state = "OFF"
    else:
        return build_error_response(directive, "INVALID_DIRECTIVE", f"Unknown power directive: {name}")

    alexa_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": power_state,
                    "timeOfSample": get_utc_timestamp(),
                    "uncertaintyInMilliseconds": 500
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": str(uuid.uuid4()),
                "correlationToken": header.get('correlationToken')
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": directive['endpoint']['scope']['token']
                },
                "endpointId": endpoint_id
            },
            "payload": {}
        }
    }

    return alexa_response

def handle_report_state(directive):
    endpoint_id = directive['endpoint']['endpointId']

    try:
        status_response = requests.get(status_url, auth=(username, password), timeout=10)
        print(f"status response {status_response}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            is_reachable = status_data.get("reachable", False)
            power_state = "ON" if is_reachable else "OFF"
        else:
            power_state = "OFF"
    except (requests.RequestException, json.JSONDecodeError):
        power_state = "OFF"

    alexa_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": power_state,
                    "timeOfSample": get_utc_timestamp(),
                    "uncertaintyInMilliseconds": 500
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "StateReport",
                "payloadVersion": "3",
                "messageId": str(uuid.uuid4()),
                "correlationToken": directive['header'].get('correlationToken')
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": directive['endpoint']['scope']['token']
                },
                "endpointId": endpoint_id
            },
            "payload": {}
        }
    }

    return alexa_response

def build_error_response(directive, error_type, error_message):
    response = {
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "ErrorResponse",
                "payloadVersion": "3",
                "messageId": str(uuid.uuid4()),
                "correlationToken": directive['header'].get('correlationToken')
            },
            "endpoint": {
                "endpointId": directive.get('endpoint', {}).get('endpointId', "unknown")
            },
            "payload": {
                "type": error_type,
                "message": error_message
            }
        }
    }

    return response

def get_utc_timestamp():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
