import os
import json
import re
import smtplib
import requests

from datetime import datetime, timezone
from email.message import EmailMessage
from bs4 import BeautifulSoup

from sources import SOURCES
from stores import amazon
from stores import bestbuy
from stores import target
from stores import walmart

STORE_FUNCTIONS = {
    "Amazon": amazon.search,
    "Best Buy": bestbuy.search,
    "Target": target.search,
    "Walmart": walmart.search
}


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
🚨 {product['name']} DEAL ALERT

Price:
${price:.2f}

Store:
{source}

Direct Link:
{url}

Target Price:
${product['target_price']:.2f}

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



def send_sms(product, price, source, url):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    sms = os.environ["SMS_EMAIL"]

    msg = EmailMessage()

    msg["Subject"] = product["name"]

    msg["From"] = sender
    msg["To"] = sms


    msg.set_content(
f"""
🚨 {product['name']}

${price:.2f}
{source}

{url}
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


        for variant in data.get("variants", []):

            if variant.get("price"):

                prices.append(
                    float(
                        variant["price"]
                    ) / 100
                )


        if prices:

            return {
                "price": min(prices),
                "url": url
            }


    except Exception as e:

        print(
            "Shopify error:",
            e
        )


    return None




def extract_product_links(soup):

    links = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if href.startswith("/"):

            href = "https://www." + href

        if href.startswith("http"):

            links.append(href)


    return links




def search_page(url, product):

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent":"Mozilla/5.0"
            },
            timeout=30
        )


        soup = BeautifulSoup(
            response.text,
            "lxml"
        )


        text = soup.get_text(
            " ",
            strip=True
        )


        text_lower = text.lower()



        unavailable = [
            "out of stock",
            "sold out",
            "unavailable"
        ]


        if any(
            word in text_lower
            for word in unavailable
        ):

            return None



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
            if float(p) <= product["target_price"] * 1.5
        ]



        if not prices:

            return None



        best_price = min(prices)



        links = extract_product_links(
            soup
        )


        product_link = url


        for link in links:

            if any(
                word in link.lower()
                for word in product["required_terms"]
            ):

                product_link = link
                break



        return {
            "price": best_price,
            "url": product_link
        }



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
    "Starting price monitor"
)


state = load_state()



for product in PRODUCTS:


    print(
        "\nChecking:",
        product["name"]
    )


    best = None



    for source in SOURCES:


        url = source["url_template"].format(
            query=product["search_query"].replace(
                " ",
                "+"
            )
        )


        print(
            source["name"],
            url
        )



        if source["type"] == "shopify":

            result = get_shopify_price(
                url
            )

        else:

            result = search_page(
                url,
                product
            )



        if result:

            if (
                best is None
                or result["price"] < best["price"]
            ):

                best = {
                    "price": result["price"],
                    "source": source["name"],
                    "url": result["url"]
                }



    if best:


        print(
            "BEST DEAL:",
            best
        )



        if best["price"] <= product["target_price"]:


            alert_key = (
                product["name"]
                +
                str(best["price"])
            )



            if alert_key not in state:


                send_email(
                    product,
                    best["price"],
                    best["source"],
                    best["url"]
                )


                send_sms(
                    product,
                    best["price"],
                    best["source"],
                    best["url"]
                )


                state[alert_key] = True




save_state(state)
