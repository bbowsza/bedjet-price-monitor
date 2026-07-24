import os
import json
import re
import smtplib
import requests

from datetime import datetime, timezone
from email.message import EmailMessage
from bs4 import BeautifulSoup

from sources import SOURCES


PRODUCT_FILE = "products.json"
STATE_FILE = "state.json"


with open(PRODUCT_FILE) as f:
    PRODUCTS = json.load(f)



def send_email(product, price, source, url):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["EMAIL_TO"]

    msg = EmailMessage()

    msg["Subject"] = (
        f"🚨 {product['name']} Deal: ${price:.2f}"
    )

    msg["From"] = sender
    msg["To"] = recipient


    msg.set_content(
f"""
{product['name']} DEAL ALERT

Price:
${price:.2f}

Store:
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




def send_sms(product, price, source):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    sms = os.environ["SMS_EMAIL"]

    msg = EmailMessage()

    msg["Subject"] = product["name"]

    msg["From"] = sender
    msg["To"] = sms


    msg.set_content(
        f"🚨 {product['name']} ${price:.2f} at {source}"
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




def get_shopify_price(url):

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent":"Mozilla/5.0"
            },
            timeout=30
        )


        data = response.json()


        prices = []


        for variant in data.get(
            "variants",
            []
        ):

            if variant.get("price"):

                prices.append(
                    float(
                        variant["price"]
                    ) / 100
                )


        if prices:
            return min(prices)


    except Exception as e:

        print(
            "Shopify error:",
            e
        )


    return None




def search_page(url, product):

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent":"Mozilla/5.0"
            },
            timeout=30
        )


        text = BeautifulSoup(
            response.text,
            "lxml"
        ).get_text(
            " ",
            strip=True
        )


        text_lower = text.lower()



        if not all(
            term in text_lower
            for term in product["required_terms"]
        ):
            return None



        if any(
            term in text_lower
            for term in product["excluded_terms"]
        ):
            return None



        prices = re.findall(
            r"\$(\d{2,4}(?:\.\d{2})?)",
            text
        )


        prices = [
    float(p)
    for p in prices
    if product["target_price"] * 1.5 >= float(p)
]
        ]


        if prices:

            return min(prices)


    except Exception as e:

        print(
            "Search error:",
            e
        )


    return None




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




print(
    "Starting multi-product monitor"
)


state = load_state()



for product in PRODUCTS:


    print(
        "\nChecking:",
        product["name"]
    )


    best_price = None
    best_source = None
    best_url = None



    for source in SOURCES:


        print(
            "Checking:",
            source["name"]
        )


        url = source["url_template"].format(
            query=product["search_query"].replace(
                " ",
                "+"
            )
        )


        price = None


        if source["type"] == "shopify":

            price = get_shopify_price(
                url
            )

        else:

            price = search_page(
                url,
                product
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
                best_url = url




    if best_price:


        print(
            "BEST PRICE:",
            best_price
        )


        alert_key = (
            product["name"]
            +
            str(best_price)
        )


        if (
            best_price <= product["target_price"]
            and alert_key not in state
        ):


            send_email(
                product,
                best_price,
                best_source,
                best_url
            )


            send_sms(
                product,
                best_price,
                best_source
            )


            state[alert_key] = True



save_state(state)
