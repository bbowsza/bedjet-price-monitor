import os
import json
import re
import smtplib
import requests

from datetime import datetime, timezone
from email.message import EmailMessage
from bs4 import BeautifulSoup


PRODUCT_URL = (
    "https://bedjet.com/products/"
    "bedjet-3-climate-comfort-system"
)

TARGET_PRICE = 1000.00
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

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    text = soup.get_text(
        " ",
        strip=True
    )

    prices = re.findall(
        r"\$(\d+\.\d{2})",
        text
    )

    prices = [
        float(p)
        for p in prices
        if float(p) > 100
    ]

    if prices:
        return min(prices)

    return None


def send_email(price):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["EMAIL_TO"]


    msg = EmailMessage()

    msg["Subject"] = (
        f"🚨 BedJet 3 Price Alert ${price:.2f}"
    )

    msg["From"] = sender
    msg["To"] = recipient


    msg.set_content(
f"""
BedJet 3 has dropped below your target price.

Current price:
${price:.2f}

Target:
${TARGET_PRICE:.2f}

Purchase link:
{PRODUCT_URL}

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

    if os.path.exists(STATE_FILE):

        with open(STATE_FILE) as f:
            return json.load(f)

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



price = get_price()

state = load_state()


if price:

    print(
        "Current BedJet price:",
        price
    )


    already_alerted = state.get(
        "alerted",
        False
    )


    if price < TARGET_PRICE and not already_alerted:

        send_email(price)

        state["alerted"] = True


    elif price >= TARGET_PRICE:

        state["alerted"] = False


    state["last_price"] = price

    state["last_check"] = str(
        datetime.now(timezone.utc)
    )

    save_state(state)
