import os
import json
import smtplib
import requests

from datetime import datetime, timezone
from email.message import EmailMessage


TARGET_PRICE = 500.00

PRODUCT_URL = (
    "https://bedjet.com/products/"
    "bedjet-3-climate-comfort-system-with-biorhythm-sleep-technology.js"
)

STATE_FILE = "state.json"


def get_price():

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        PRODUCT_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    prices = []

    for variant in data.get("variants", []):

        price = variant.get("price")

        if price:
            prices.append(
                float(price) / 100
            )

    if prices:
        return min(prices)

    return None



def send_email(price):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["EMAIL_TO"]


    msg = EmailMessage()

    msg["Subject"] = (
        f"🚨 BedJet 3 Alert: ${price:.2f}"
    )

    msg["From"] = sender
    msg["To"] = recipient


    msg.set_content(
f"""
BedJet 3 has dropped below your target price.

Current price:
${price:.2f}

Your target:
${TARGET_PRICE:.2f}

Product:
https://bedjet.com/

Checked:
{datetime.now(timezone.utc)}
"""
    )


    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            sender,
            password
        )

        smtp.send_message(msg)



def load_state():

    try:

        with open(STATE_FILE) as f:
            return json.load(f)

    except:

        return {}



def save_state(state):

    with open(
        STATE_FILE,
        "w"
    ) as f:

        json.dump(
            state,
            f,
            indent=2
        )



print("Starting BedJet price check...")

price = get_price()

print("Detected price:", price)


state = load_state()


if price is not None:

    if price < TARGET_PRICE:

        if not state.get("alerted"):

            send_email(price)
            send_sms(price)

            state["alerted"] = True


    else:

        state["alerted"] = False


    state["last_price"] = price
    state["last_check"] = str(
        datetime.now(timezone.utc)
    )

    save_state(state)

def send_sms(price):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    sms_address = os.environ["SMS_EMAIL"]

    msg = EmailMessage()

    msg["Subject"] = "BedJet Alert"
    msg["From"] = sender
    msg["To"] = sms_address

    msg.set_content(
        f"🚨 BedJet 3 is ${price:.2f}! "
        f"Below your $300 target."
    )

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            sender,
            password
        )

        smtp.send_message(msg)
