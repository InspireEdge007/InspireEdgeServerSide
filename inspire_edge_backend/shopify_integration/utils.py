
import requests
import os

import urllib.parse

from .models import LocalProduct


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

def connect_to_risk_delta_forecast(shopify,period):

    url = "https://inspireedgeml.onrender.com//risk-delta/forecast"

    headers = {
        "Content-Type": "application/json"
        # Add Authorization if needed: "Authorization": "Bearer YOUR_TOKEN"
    }

    data ={
                "product_id": str(shopify["id"]),
                "target": "product_price",
                "periods": period,
                "current_price": shopify["variants"][0]["price"],
                "store_id": str(shopify["variants"][0]["id"]),
                "price_history": [
                    {
                    "date": "2025-05-29",
                    "value": 0
                    }
                ]
        }


    # Use json= instead of data= to automatically convert dict to JSON
    response = requests.post(url, json=data, headers=headers)

    # Debugging: print response status and body
    # print(response.status_code)
    # print(response.text)

    return response.text, response.status_code


def connect_to_risk_delta_anomaly(shopify,period):

    url = "https://inspireedgeml.onrender.com/risk-delta/anomaly"

    headers = {
        "Content-Type": "application/json"
        # Add Authorization if needed: "Authorization": "Bearer YOUR_TOKEN"
    }

    data = {
                "product_id": str(shopify["id"]),
                "target": "product_price",
                "periods": period,
                "current_price": shopify["variants"][0]["price"],
                "store_id": str(shopify["variants"][0]["id"]),
                "price_history": [
                    {
                    "date": "2025-05-29",
                    "value": 0
                    }
                ]
        }


    # Use json= instead of data= to automatically convert dict to JSON
    response = requests.post(url, json=data, headers=headers)

    # Debugging: print response status and body
    print(response.status_code)
    print(response.text)

    return response.text, response.status_code


def connect_to_strike_detect(shopify, limit):

    url = "https://inspireedgeml.onrender.com//strike/detect"

    headers = {
        "Content-Type": "application/json"
        # Add Authorization if needed: "Authorization": "Bearer YOUR_TOKEN"
    }

    data = {
            "business_id": str(shopify["variants"][0]["id"]),

            "limit": limit
            }



    # Use json= instead of data= to automatically convert dict to JSON
    response = requests.post(url, json=data, headers=headers)

    # Debugging: print response status and body
    print(response.status_code)
    print(response.text)

    return response.text , response.status_code


def connect_to_engagex_recommend(shopify, limit):

    url = "https://inspireedgeml.onrender.com/engagex/recommend"

    headers = {
        "Content-Type": "application/json"
        # Add Authorization if needed: "Authorization": "Bearer YOUR_TOKEN"
    }

    data = {
            "business_id":  str(shopify["variants"][0]["id"]),
            "limit": limit
            }



    # Use json= instead of data= to automatically convert dict to JSON
    response = requests.post(url, json=data, headers=headers)

    # Debugging: print response status and body
    print(response.status_code)
    print(response.text)

    return response.text , response.status_code


def connect_to_vooice_analyze_feedback(shopify):

    url = "https://inspireedgeml.onrender.com/vooice/analyze-feedback"

    headers = {
        "Content-Type": "application/json"
        # Add Authorization if needed: "Authorization": "Bearer YOUR_TOKEN"
    }

    data = {
            "business_id": str(shopify["variants"][0]["id"]),
            "product_id": str(shopify["id"]),
            "reviews": [
                {
                "text": "string",
                "label": "string",
                "timestamp": "2025-05-29",
                }
            ]
            }




    # Use json= instead of data= to automatically convert dict to JSON
    response = requests.post(url, json=data, headers=headers)

    # Debugging: print response status and body
    print(response.status_code)
    print(response.text)

    return response.text , response.status_code


def connect_to_abandonment_freemium(shopify):

    url = "https://inspireedgeml.onrender.com/abandonment/freemium"

    headers = {
        "Content-Type": "application/json"
        # Add Authorization if needed: "Authorization": "Bearer YOUR_TOKEN"
    }

    data = [

                {
                "session_duration_secs": 0,
                "pages_viewed": 0,
                "products_viewed": 0,
                "cart_items_count": 0,
                "cart_value_usd": 0,
                "discount_applied": 0,
                "session_hour": 0,
                "returning_user": 0,
                "total_dwell_time": 0,
                "account_age_days": 0,
                "total_sessions": 0,
                "total_cart_abandons": 0,
                "total_orders": 0,
                "avg_session_duration_secs": 0,
                "avg_cart_value_usd": 0,
                "is_subscribed_email": 0,
                "dwell_time_per_page": 0,
                "cart_value_per_product": 0,
                "abandonment_rate_user": 0,
                "interaction_cart_time": 0,
                "interaction_returning_abandon": 0,
                "location_country": "unknown",
                "weather": "clear",
                "device_type": "unknown"
                }

    ]


    # Use json= instead of data= to automatically convert dict to JSON
    response = requests.post(url, json=data, headers=headers)

    # Debugging: print response status and body
    print(response.status_code)
    print(response.text)

    return response.text


def connect_to_abandonment_premium(shopify):

    url = "https://inspireedgeml.onrender.com/abandonment/premium"

    headers = {
        "Content-Type": "application/json"
        # Add Authorization if needed: "Authorization": "Bearer YOUR_TOKEN"
    }

    data = [

        {
            "session_duration_secs": 0,
            "pages_viewed": 0,
            "products_viewed": 0,
            "cart_items_count": 0,
            "cart_value_usd": 0,
            "discount_applied": 0,
            "session_hour": 0,
            "returning_user": 0,
            "total_dwell_time": 0,
            "account_age_days": 0,
            "total_sessions": 0,
            "total_cart_abandons": 0,
            "total_orders": 0,
            "avg_session_duration_secs": 0,
            "avg_cart_value_usd": 0,
            "is_subscribed_email": 0,
            "dwell_time_per_page": 0,
            "cart_value_per_product": 0,
            "abandonment_rate_user": 0,
            "interaction_cart_time": 0,
            "interaction_returning_abandon": 0,
            "location_country": "unknown",
            "weather": "clear",
            "device_type": "unknown"
            }

    ]


    # Use json= instead of data= to automatically convert dict to JSON
    response = requests.post(url, json=data, headers=headers)

    # Debugging: print response status and body
    print(response.status_code)
    print(response.text)

    return response.text