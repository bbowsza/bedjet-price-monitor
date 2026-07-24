import os
import json
import smtplib

from datetime import datetime, timezone
from email.message import EmailMessage

from sources import SOURCES

from stores import amazon
from stores import bestbuy
from stores import target
from stores import walmart


PRODUCT_FILE = "products.json"
STATE_FILE = "state.json"



STORE_FUNCTIONS = {

    "Amazon":
        amazon.search,

    "Best Buy":
        bestbuy.search,

    "Target":
        target.search,

    "Walmart":
        walmart.search

}



with open(PRODUCT_FILE) as f:
    PRODUCTS = json.load(f)




def send_email(product, deal):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["EMAIL_TO"]


    msg = EmailMessage()


    msg["Subject"] = (
        f"🚨 {product['name']} ${deal['price']:.2f}"
    )


    msg["From"] = sender
    msg["To"] = recipient



    msg.set_content(
f"""
🚨 DEAL ALERT

Product:
{product['name']}

Price:
${deal['price']:.2f}

Store:
{deal['source']}

Direct Link:
{deal['url']}

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


        smtp.send_message(
            msg
        )




def send_sms(product, deal):

    sender = os.environ["EMAIL_FROM"]
    password = os.environ["EMAIL_PASSWORD"]
    sms = os.environ["SMS_EMAIL"]


    msg = EmailMessage()


    msg["Subject"] = (
        product["name"]
    )


    msg["From"] = sender
    msg["To"] = sms



    msg.set_content(
f"""
🚨 {product['name']}

${deal['price']:.2f}

{deal['source']}

{deal['url']}
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


        smtp.send_message(
            msg
        )




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
    "Starting product deal monitor"
)



state = load_state()




for product in PRODUCTS:


    print(
        "\nChecking:",
        product["name"]
    )


    best_deal = None



    for source in SOURCES:


        store_name = source["name"]


        print(
            "Searching:",
            store_name
        )


        if store_name not in STORE_FUNCTIONS:

            continue



        try:

            result = STORE_FUNCTIONS[store_name](
                product["search_query"],
                product
            )


        except Exception as e:

            print(
                store_name,
                "failed:",
                e
            )

            continue



        if result:


            result["source"] = store_name


            print(
                "Found:",
                result
            )


            if (
                best_deal is None
                or result["price"]
                <
                best_deal["price"]
            ):

                best_deal = result




    if best_deal:


        print(
            "BEST DEAL:",
            best_deal
        )



        if (
            best_deal["price"]
            <=
            product["target_price"]
        ):


            alert_key = (
                product["name"]
                +
                str(best_deal["price"])
                +
                best_deal["url"]
            )



            if alert_key not in state:


                send_email(
                    product,
                    best_deal
                )


                send_sms(
                    product,
                    best_deal
                )


                state[alert_key] = True



save_state(state)


print(
    "Monitor complete"
)
