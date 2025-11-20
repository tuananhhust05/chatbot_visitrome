

import requests


# --------------------------------------------------------------
# Test endpoint verificiation
# --------------------------------------------------------------
def test_endpoint_verification(challenge: str, settings: object):
    response = requests.get("https://cheetah-well-serval.ngrok-free.app/webhook",
        params={
            'hub.mode': 'subscribe',
            'hub.challenge': challenge,
            'hub.verify_token': settings.VERIFY_TOKEN
        }
    )
    return response


# --------------------------------------------------------------
# Send a template WhatsApp message
# --------------------------------------------------------------
def send_whatsapp_template(
        recipient_waid: str, 
        template_name: str, 
        settings: object,
        language_code: str = "en_US"
    ):
    url = f"https://graph.facebook.com/{settings.VERSION}/{settings.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient_waid,
        "type": "template",
        "template": {"name": template_name, "language": {"code": language_code}},
    }
    response = requests.post(url, headers=headers, json=data)
    return response


# --------------------------------------------------------------
# Send a text message
# --------------------------------------------------------------
def send_whatsapp_text(
        recipient_waid: str,
        message: str, 
        settings: object,
        preview_url: bool = False
    ):
    try:
        url = f"https://graph.facebook.com/{settings.VERSION}/{settings.PHONE_NUMBER_ID}/messages"
        print(url)
        headers = {
                "Content-type": "application/json",
                "Authorization": f"Bearer {settings.ACCESS_TOKEN}",
            }
        data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient_waid,
                "type": "text",
                "text": {"preview_url": preview_url, "body": message},
            }

        response = requests.post(url=url, json=data, headers=headers, timeout=10)

        if response.status_code == 200:
            print("Status:", response.status_code)
            print("Content-type:", response.headers["content-type"])
            print("Body:", response.text)
            return response
        else:
            print(response.status_code)
            print(response.text)
            return response
    except Exception as e:
        print("exception send_whatsapp_text",e)
    
