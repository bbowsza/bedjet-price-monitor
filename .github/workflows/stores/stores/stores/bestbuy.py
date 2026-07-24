import requests
import re
from bs4 import BeautifulSoup


def search(query, product):

    url = (
        "https://www.bestbuy.com/site/searchpage.jsp?st="
        +
        query.replace(" ", "+")
    )


    try:

        response = requests.get(
            url,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            },
            timeout=30
        )


        soup = BeautifulSoup(
            response.text,
            "lxml"
        )


        items = soup.select(
            ".sku-item"
        )


        deals=[]


        for item in items:

            text = item.get_text(
                " ",
                strip=True
            ).lower()


            if not all(
                x in text
                for x in product["required_terms"]
            ):
                continue


            prices = re.findall(
                r"\$(\d+\.\d{2})",
                text
            )


            link = item.find(
                "a",
                href=True
            )


            if prices and link:

                deals.append(
                    {
                        "price":
                        float(prices[0]),

                        "url":
                        "https://bestbuy.com"
                        +
                        link["href"]
                    }
                )


        if deals:

            return min(
                deals,
                key=lambda x:x["price"]
            )


    except Exception as e:

        print(
            "Best Buy error:",
            e
        )


    return None
