import json
import os
import requests
import uuid
import threading
from datetime import datetime

BASE_URL = "https://home.snackk-media.com:443"
status_url = f"{BASE_URL}/check-emby"
wake_url = f"{BASE_URL}/send-wol/"
climate_status_url = f"{BASE_URL}/climate/status"
climate_set_url = f"{BASE_URL}/climate"
shutdown_url = f"{BASE_URL}/shutdown"
shutter_departure_url = f"{BASE_URL}/netatmo/departure"
shutter_wakeup_url = f"{BASE_URL}/netatmo/wakeup"

username = os.environ.get('WOL_USERNAME')
password = os.environ.get('WOL_PASSWORD')

AC_DEVICES = {
    'sala': 'Living Room AC',
    'suite': 'Suite AC',
    'escritorio': 'Office AC',
    'cozinha': 'Kitchen AC',
    'visitas': 'Guest Room AC'
}

SHUTTER_SCENES = {
    'shutter-close-all': ('Fecha Estores', shutter_departure_url),
    'shutter-wakeup': ('Abre Estores', shutter_wakeup_url),
}

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
    endpoints = []
    
    # Existing PC device
    endpoints.append({
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
                    "proactivelyReported": False,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa",
                "version": "3"
            }
        ]
    })

    # AC Devices
    for ac_id, ac_name in AC_DEVICES.items():
        endpoints.append({
            "endpointId": f"ac-{ac_id}",
            "manufacturerName": "Diogo Santos",
            "description": f"AC {ac_name}",
            "friendlyName": ac_name,
            "displayCategories": ["THERMOSTAT"],
            "additionalAttributes": {
                "manufacturer": "Diogo Santos",
                "model": "Air Conditioner",
                "serialNumber": f"AC-{ac_id.upper()}",
                "firmwareVersion": "1.0",
                "softwareVersion": "1.0",
                "customIdentifier": f"AC {ac_id}"
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
                        "proactivelyReported": False,
                        "retrievable": True
                    }
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa",
                    "version": "3"
                }
            ]
        })

    # Shutter Scene Devices
    for scene_id, (scene_name, _) in SHUTTER_SCENES.items():
        endpoints.append({
            "endpointId": scene_id,
            "manufacturerName": "Diogo Santos",
            "description": f"Shutter {scene_name}",
            "friendlyName": scene_name,
            "displayCategories": ["SCENE_TRIGGER"],
            "additionalAttributes": {
                "manufacturer": "Diogo Santos",
                "model": "Netatmo Shutters",
                "serialNumber": f"SHUTTER-{scene_id.upper()}",
                "firmwareVersion": "1.0",
                "softwareVersion": "1.0",
                "customIdentifier": scene_id
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
                        "proactivelyReported": False,
                        "retrievable": False
                    }
                },
                {
                    "type": "AlexaInterface",
                    "interface": "Alexa",
                    "version": "3"
                }
            ]
        })

    response = {
        "event": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "Discover.Response",
                "payloadVersion": "3",
                "messageId": str(uuid.uuid4())
            },
            "payload": {
                "endpoints": endpoints
            }
        }
    }

    return response

def handle_power_control(directive):
    header = directive['header']
    endpoint_id = directive['endpoint']['endpointId']
    name = header['name']

    power_state = "OFF"
    if endpoint_id == "snackk-alexa-wol":
        if name == "TurnOn":
            try:
                wol_response = requests.post(wake_url, auth=(username, password), timeout=10)
                print(f"wol response {wol_response}")
                power_state = "ON" if wol_response.status_code == 200 else "OFF"
            except requests.RequestException:
                power_state = "OFF"
        elif name == "TurnOff":
            try:
                shutdown_response = requests.post(shutdown_url, auth=(username, password), timeout=10)
                print(f"shutdown response {shutdown_response}")
                power_state = "OFF" if shutdown_response.status_code == 200 else "ON"
            except requests.RequestException:
                power_state = "ON"
    elif endpoint_id.startswith("ac-"):
        ac_id = endpoint_id.replace("ac-", "")
        if ac_id in AC_DEVICES:
            status = "ON" if name == "TurnOn" else "OFF"
            try:
                payload = {"roomId": ac_id, "status": status}
                # Using session cookie might be needed if basic auth doesn't work for json post, 
                # but based on the provided Flask code, let's try direct POST.
                # If it needs session, we'd need to login first. 
                # Assuming basic auth works or it's not strictly enforced for this endpoint if called from internal/trusted source.
                # Actually, requires_auth is NOT on /climate POST in the provided Flask code.
                response = requests.post(climate_set_url, json=payload, auth=(username, password), timeout=10)
                if response.status_code == 200:
                    power_state = status
                else:
                    power_state = "OFF" # Or keep current state if we knew it
            except requests.RequestException:
                power_state = "OFF"
    elif endpoint_id in SHUTTER_SCENES:
        _, scene_url = SHUTTER_SCENES[endpoint_id]
        # Fire and forget - trigger the request in a background thread
        # and respond to Alexa immediately to avoid timeout
        def trigger_scene():
            try:
                requests.post(scene_url, auth=(username, password), timeout=60)
            except requests.RequestException:
                pass
        thread = threading.Thread(target=trigger_scene)
        thread.start()
        power_state = "ON"
    else:
        return build_error_response(directive, "INVALID_DIRECTIVE", f"Unknown endpoint: {endpoint_id}")

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
    power_state = "OFF"

    try:
        if endpoint_id == "snackk-alexa-wol":
            status_response = requests.get(status_url, auth=(username, password), timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                is_reachable = status_data.get("reachable", False)
                power_state = "ON" if is_reachable else "OFF"
        elif endpoint_id.startswith("ac-"):
            ac_id = endpoint_id.replace("ac-", "")
            status_response = requests.get(climate_status_url, auth=(username, password), timeout=10)
            if status_response.status_code == 200:
                status_data = status_response.json()
                # The Flask app returns: {"devices": {"sala": {"power": True, ...}, ...}, ...}
                device_info = status_data.get("devices", {}).get(ac_id, {})
                if device_info.get("online", False):
                    power_state = "ON" if device_info.get("power", False) else "OFF"
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
