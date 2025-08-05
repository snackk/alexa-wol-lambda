import json
import os
import requests

def lambda_handler(event, context):
    url = "http://snackk-media.ddns.net:80/send-wol/"
    username = os.environ.get('WOL_USERNAME')
    password = os.environ.get('WOL_PASSWORD')

    try:
        response = requests.post(url, auth=(username, password))
        if response.status_code == 200:
            return {
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "wooosh, computer should turn on now!"
                    },
                    "shouldEndSession": True
                }
            }
        else:
            return {
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "Computer went potato, have you tried switching on and off sir?"
                    },
                    "shouldEndSession": True
                }
            }
    except Exception as e:
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Uh, maybe your potato head didn't turn on raspberry pi zero?"
                },
                "shouldEndSession": True
            }
        }
