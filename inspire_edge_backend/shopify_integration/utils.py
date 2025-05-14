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
            print("API call failed:", response.status_code)

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
