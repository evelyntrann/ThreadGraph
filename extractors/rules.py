import re

def extract_intent(payload: dict) -> str:
    text = (payload.get("subject", "") + " " + payload.get("snippet", "")).lower()

    if any(k in text for k in ["available", "schedule", "time", "when"]):
        return "schedule"
    if any(k in text for k in ["reply", "confirm", "respond"]):
        return "reply"
    return "info"


def is_promotional(payload: dict) -> bool:
    sender = payload.get("from", "").lower()
    return any(k in sender for k in ["noreply", "newsletter", "promo"])

def extract_action_item(payload: dict) -> list[str]:
    text = payload.get("snippet", "").lower()
    actions = []
    if "are you available" in text:
        actions.append("Provide availability")
    return actions