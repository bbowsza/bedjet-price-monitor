import requests
import re
from bs4 import BeautifulSoup


def search(query, product):

    url = (
        "https://www.amazon.com/s?k="
        + query.replace(" ", "+")
    )

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=30
        )

        soup = BeautifulSoup(
            response.text,
            "lxml"
        )

        deals = []


        items = soup.select(
            "[data-component-type='s-search-result']"
        )


        for item in items:

            text = item.get_text(
                " ",
                strip=True
            ).lower()


            if not all(
                term in text
                for term in product["required_terms"]
            ):
                continue


            if any(
                term in text
                for term in product["excluded_terms"]
            ):
                continue


            price_whole = item.select_one(
                ".a-price-whole"
            )

            link = item.select_one(
                "a.a-link-normal"
            )


            if price_whole and link:

                price = float(
                    re.sub(
                        "[^0-9]",
                        "",
                        price_whole.text
                    )
                )


                deals.append(
                    {
                        "price": price,
                        "url":
                        "https://www.amazon.com"
                        + link["href"]
                    }
                )


        if deals:

            return min(
                deals,
                key=lambda x: x["price"]
            )


    except Exception as e:

        print(
            "Amazon error:",
            e
        )


    return None
