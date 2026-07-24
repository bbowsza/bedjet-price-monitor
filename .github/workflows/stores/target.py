import requests
import re
from bs4 import BeautifulSoup


def search(query, product):

    url = (
        "https://www.target.com/s?searchTerm="
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


        text = soup.get_text(
            " ",
            strip=True
        ).lower()


        if not all(
            term in text
            for term in product["required_terms"]
        ):
            return None


        if any(
            term in text
            for term in product["excluded_terms"]
        ):
            return None



        prices = re.findall(
            r"\$(\d+\.\d{2})",
            text
        )


        links = []


        for a in soup.find_all(
            "a",
            href=True
        ):

            if "/p/" in a["href"]:

                link = a["href"]

                if link.startswith("/"):
                    link = (
                        "https://www.target.com"
                        + link
                    )

                links.append(link)



        valid_prices = [
            float(p)
            for p in prices
            if float(p)
            <= product["target_price"] * 1.5
        ]



        if valid_prices and links:

            return {
                "price": min(valid_prices),
                "url": links[0]
            }


    except Exception as e:

        print(
            "Target error:",
            e
        )


    return None
