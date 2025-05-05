########### Python 3.2 #############
import urllib.request, json, os
from dotenv import load_dotenv

load_dotenv()

try:
    def amazon_products(keyword):
        url = f"https://api.axesso.de/amz/amazon-search-by-keyword-asin?domainCode=co.uk&keyword={keyword}&page=1"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'axesso-api-key': os.getenv('axesso-api-key'),
        }

        req = urllib.request.Request(url, headers=hdr)

        req.get_method = lambda: 'GET'
        response = urllib.request.urlopen(req)
        print(response.getcode())
        print(response.read())
        with open("read.json", "w") as file:
            json.dump(response.read(), file, indent= 4)

except Exception as e:
        print(e)


####################################