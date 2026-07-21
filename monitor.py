import os
import json
import re
import smtplib
import requests

from datetime import datetime, timezone
from email.message import EmailMessage
from bs4 import BeautifulSoup

from sources import SOURCES


TARGET_PRICE = 500.00
STATE_FILE = "state.json"


def send_email(price, source, url):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["EMAIL_TO"]

    msg = EmailMessage()

    msg["Subject"] = (
        f"🚨 BedJet 3 Deal Found: ${price:.2f}"
    )

    msg["From"] = sender
    msg["To"] = recipient

    msg.set_content(
f"""
BEDJET 3 DEAL ALERT

Price:
${price:.2f}

Source:
{source}

Link:
{url}

Time:
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



def send_sms(price, source):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    sms = os.environ["SMS_EMAIL"]

    msg = EmailMessage()

    msg["Subject"] = "BedJet 3 Deal"
    msg["From"] = sender
    msg["To"] = sms

    msg.set_content(
        f"🚨 BedJet 3 ${price:.2f} at {source}"
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



def get_bedjet_price(url):

    response = requests.get(
        url,
        headers={"User-Agent":"Mozilla/5.0"},
        timeout=30
    )

    if response.status_code != 200:
        return None

    try:
        data = response.json()

        prices = []

        for variant in data.get("variants", []):

            if variant.get("price"):

                prices.append(
                    float(
                        variant["price"]
                    ) / 100
                )

        if prices:
            return min(prices)

    except:
        pass

    return None



def search_page(url):

    try:

        response = requests.get(
            url,
            headers={"User-Agent":"Mozilla/5.0"},
            timeout=30
        )

        text = BeautifulSoup(
            response.text,
            "html.parser"
        ).get_text(
            " ",
            strip=True
        )

        if "bedjet 3" not in text.lower():
            return None

        prices = re.findall(
            r"\$(\d{2,4}(?:\.\d{2})?)",
            text
        )

        prices = [
            float(p)
            for p in prices
            if float(p) > 100
        ]

        if prices:
            return min(prices)

    except:
        pass

    return None



def load_state():

    try:

        with open(STATE_FILE) as f:
            return json.load(f)

    except:

        return {}



def save_state(data):

    with open(
        STATE_FILE,
        "w"
    ) as f:

        json.dump(
            data,
            f,
            indent=2
        )



print("Starting BedJet 3 deal monitor")

best_price = None
best_source = None
best_url = None


for source in SOURCES:

    print(
        "Checking:",
        source["name"]
    )

    price = None

    if source["type"] == "shopify":

        price = get_bedjet_price(
            source["url"]
        )

    else:

        price = search_page(
            source["url"]
        )


    print(
        "Price:",
        price
    )


    if price:

        if (
            best_price is None
            or price < best_price
        ):

            best_price = price
            best_source = source["name"]
            best_url = source["url"]



if best_price:

    print(
        "LOWEST PRICE:",
        best_price,
        best_source
    )


    state = load_state()

    already_alerted = (
        state.get("alerted_price")
        == best_price
    )


    if (
        best_price <= TARGET_PRICE
        and not already_alerted
    ):

        send_email(
            best_price,
            best_source,
            best_url
        )

        send_sms(
            best_price,
            best_source
        )

        state["alerted_price"] = best_price


    save_state(state)
