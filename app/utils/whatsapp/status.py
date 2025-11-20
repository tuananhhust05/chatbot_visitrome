
def is_valid_whatsapp_status(payload):
    """
    Check if the incoming webhook event has a valid WhatsApp status update structure.
    """
    return(
        payload.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("statuses")
    )