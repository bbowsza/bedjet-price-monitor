import requests
import re
from bs4 import BeautifulSoup


def search(query, product):

    url = (
        "https://www.walmart.com/search?q="
        +
        query.replace(" ", "+")
    )


    try:

        response=requests.get(
            url,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            },
            timeout=30
        )


        soup=BeautifulSoup(
            response.text,
            "lxml"
        )


        links=[]


        for a in soup.find_all(
            "a",
            href=True
        ):

            if "/ip/" in a["href"]:

                links.append(
                    a["href"]
                )


        prices=re.findall(
            r"\$(\d+\.\d{2})",
            soup.text
        )


        if prices and links:

            price=min(
                float(x)
                for x in prices
            )


            return {
                "price":price,
                "url":
                "https://walmart.com"
                +
                links[0]
            }


    except Exception as e:

        print(
            "Walmart error:",
            e
        )


    return None
