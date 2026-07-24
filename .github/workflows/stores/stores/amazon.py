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
                "User-Agent":
                "Mozilla/5.0"
            },
            timeout=30
        )

        soup = BeautifulSoup(
            response.text,
            "lxml"
        )


        results = []


        for item in soup.select(
            "[data-component-type='s-search-result']"
        ):

            title = item.get_text(
                " ",
                strip=True
            ).lower()


            if not all(
                term in title
                for term in product["required_terms"]
            ):
                continue


            if any(
                term in title
                for term in product["excluded_terms"]
            ):
                continue


            price = item.select_one(
                ".a-price-whole"
            )


            link = item.select_one(
                "a.a-link-normal"
            )


            if price and link:

                amount = float(
                    re.sub(
                        "[^0-9]",
                        "",
                        price.text
                    )
                )


                results.append(
                    {
                        "price": amount,
                        "url":
                        "https://amazon.com"
                        + link["href"]
                    }
                )


        if results:

            return min(
                results,
                key=lambda x:x["price"]
            )


    except Exception as e:

        print(
            "Amazon error:",
            e
        )


    return None
