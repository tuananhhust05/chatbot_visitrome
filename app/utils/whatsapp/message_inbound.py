import re, json
from fastapi import FastAPI, Request, Response, responses, Query



def process_whatsapp_message(payload):
    
    payload_entry = payload.get("entry")[0]
    payload_entry_changes_value = payload_entry.get("changes")[0].get("value")

    account_id = payload_entry.get("id")
    metadata = payload_entry_changes_value.get("metadata")
    contacts = payload_entry_changes_value.get("contacts")[0]
    messages = payload_entry_changes_value.get("messages")[0]
    
    message_type = messages.get("type")

    return account_id, metadata, contacts, message_type, messages


def is_valid_whatsapp_message(payload):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        payload.get("object")
        and payload.get("entry")
        and payload["entry"][0].get("changes")
        and payload["entry"][0]["changes"][0].get("value")
        and payload["entry"][0]["changes"][0]["value"].get("messages")
        and payload["entry"][0]["changes"][0]["value"]["messages"][0]
    )



def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text

""""

# def get_message_payload(payload):
#     return payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

# get_message_payload(tmp)

# tmp.get("entry")[0].get("id")

# tmp = {
#   "object": "whatsapp_business_account",
#   "entry": [
#     {
#       "id": "456272337558434",
#       "changes": [
#         {
#           "value": {
#             "messaging_product": "whatsapp",
#             "metadata": {
#               "display_phone_number": "15556268712",
#               "phone_number_id": "423309444198813"
#             },
#             "contacts": [
#               {
#                 "profile": {
#                   "name": "Ek Hong"
#                 },
#                 "wa_id": "6593691018"
#               }
#             ],
#             "messages": [
#               {
#                 "from": "6593691018",
#                 "id": "wamid.HBgKNjU5MzY5MTAxOBUCABIYIEM4MTkwRTBBNDUzNzcyOERFNzUxODlFQzJCMDM5NTNFAA==",
#                 "timestamp": "1729756628",
#                 "text": {
#                   "body": "Test"
#                 },
#                 "type": "text"
#               }
#             ]
#           },
#           "field": "messages"
#         }
#       ]
#     }
#   ]
# }

## example of video payload
## - for eg. https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#video-message
## - many types of payload: "text", "image", "video", "location", "sticker"......
# "messages": [
#   {
#     "from": "6593691018",
#     "id": "wamid.HBgKNjU5MzY5MTAxOBUCABIYIEM4MTkwRTBBNDUzNzcyOERFNzUxODlFQzJCMDM5NTNFAA==",
#     "timestamp": "1729756628",
#     "type": "video",
#     "video": {
#       "caption": "Check this out!",
#       "media_url": "https://api.whatsapp.com/media_url",  // URL to the video
#       "mime_type": "video/mp4",
#       "sha256": "abcdef1234567890"  // Checksum for verification
#     }
#   }
# ]
"""






