import requests
import os

import urllib.parse



def amazon_products(keyword, page):

        results = []
    # while True:

        url = f"https://api.axesso.de/amz/amazon-search-by-keyword-asin?domainCode=com&keyword={keyword}&page={page}"

        headers = {
            'axesso-api-key': os.getenv('axesso-api-key'),
            'Cache-Control': 'no-cache'
        }

        response = requests.get(url, headers=headers)


        if response.status_code != 200:
            print("API call failed:", {response.status_code , response.text})

            return None

        data = response.json()

        keyword = keyword.strip().lower()

        decoded_url = urllib.parse.unquote(keyword)
        product_list = data.get("searchProductDetails", [])

        for product in product_list:
            title = product.get("productDescription", "")

            if decoded_url in title.lower():
                product_info = {
                    "title": title,
                    "asin": product.get("asin"),
                    "price": product.get("price", 0.0),
                    "rating": product.get("productRating", "No rating"),
                    "image_url": product.get("imgUrl"),
                    "product_url": f"https://www.amazon.com{product.get('dpUrl', '')}",
                    "prime": product.get("prime", False),
                    "delivery": product.get("deliveryMessage", ""),
                    "matched_keyword": keyword  # explicitly store matched keyword
                }

                results.append(product_info)

        # if page >= data.get("lastPage", page):  # Stop if current page is the last
        #     break

        # page += 1

        return results


def connect_to_market_recon(competitor, shopify):
    url = "https://inspireedgeml.onrender.com/market-recon/recommend"

    headers = {
        "Content-Type": "application/json"
        # Add Authorization if needed: "Authorization": "Bearer YOUR_TOKEN"
    }

    # print(shopify["id"])
    data = [
        {
            "business_id": str(shopify["variants"][0]["id"]),
            "product_id": str(shopify["id"]),
            "product_name": shopify["title"],
            "product_price": shopify["variants"][0]["price"],
            "product_name": shopify["title"],
            "competitors": [
                {
                    "competitor_id": competitor[0]["asin"],
                    "competitor_name": "john",
                    "competitor_price": competitor[0]["price"],
                    "competitor_product_title": competitor[0]["title"],
                    "competitor_product_description": "shoe",
                    "event_type": "shoe"
                }
            ]
        }
    ]


    # Use json= instead of data= to automatically convert dict to JSON
    response = requests.post(url, json=data, headers=headers)

    # Debugging: print response status and body
    print(response.status_code)
    print(response.text)

    return response.text





