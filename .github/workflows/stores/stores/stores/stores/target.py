import requests
import re
from bs4 import BeautifulSoup


def search(query, product):

    url = (
        "https://www.target.com/s?searchTerm="
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


        text = soup.get_text(
            " ",
            strip=True
        )


        prices = re.findall(
            r"\$(\d+\.\d{2})",
            text
        )


        links = [
            a["href"]
            for a in soup.find_all(
                "a",
                href=True
            )
        ]


        for price in prices:

            value=float(price)

            if value <= product["target_price"]:

                for link in links:

                    if "/p/" in link:

                        if link.startswith("/"):

                            link = (
                                "https://target.com"
                                +
                                link
                            )

                        return {
                            "price":value,
                            "url":link
                        }


    except Exception as e:

        print(
            "Target error:",
            e
        )


    return None
