import requests
import json

class CommonTools:

    def __init__(
            self,
            query_vector_store,
            google_api_key: str,
            rapidapi_key: str,
            process_search_results_function=None,
            process_product_results_function=None,
            test_mode=True,
            nearai_agent_client=None):
        self.query_vector_store = query_vector_store
        self.google_programmatic_search_api_key = google_api_key
        self.google_search_engine_id = "67ecbcdfba7584807"  # normal google search
        self.rapidapi_key = rapidapi_key
        self.process_search_results_function = process_search_results_function or self._process_search_results
        self.process_product_results_function = process_product_results_function or None
        self.test_mode = test_mode
        self.nearai_agent_client = nearai_agent_client

    def _process_search_results(self, search_results):
        """Default processing of search results from the Google Search API, returns result titles.

        search_results: the search results from the Google Search API.
        """
        search_results = search_results["items"]
        search_results = [result["title"] for result in search_results]
        return search_results

    def google_search(self, query):
        """Search the web to find recent information with which to answer questions.

        query: the search query containing what you want to search for.
        """
        api_key = self.google_programmatic_search_api_key
        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={self.google_search_engine_id}&q={query}"
        response = requests.get(url)
        json = response.json()
        return self._process_search_results(json)

    def api_call(self, api_url, params):
        """Make an API call to a given URL with a query.

        api_url: the URL to make the API call to.
        query: the query to send to the API.
        """
        response = requests.get(api_url, params=params)
        return response.json()

    def product_search(self, query, country='us', language='en', page=1, limit=6, sort_by='BEST_MATCH', product_condition='ANY', min_price=0.00):
        """Search for products using the Real-Time Product Search API via RapidAPI.

        query: The search query for the products.
        min_price: Minimum price threshold to filter out products below this price.
        """
        self.nearai_agent_client.add_system_log("Searching for products...")
        url = "https://real-time-product-search.p.rapidapi.com/search-v2"
        querystring = {
            "q": query,
            "country": country,
            "language": language,
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "product_condition": product_condition
        }
        headers = {
            'x-rapidapi-key': self.rapidapi_key,
            'x-rapidapi-host': "real-time-product-search.p.rapidapi.com"
        }
        if self.test_mode:
            self.nearai_agent_client.add_system_log(f"Test mode: Using cached T-shirt result output")
            with open('cached_rapidapi_output.json', 'r', encoding='utf-8') as file:
                data = json.loads(file.read())
        else:
            response = requests.get(url, headers=headers, params=querystring)
            data = response.json()
        if data.get('message'):
            self.nearai_agent_client.add_system_log(f"Error: {data['message']}")
            with open('cached_rapidapi_output.json', 'r', encoding='utf-8') as file:
                data = json.loads(file.read())

        products = data.get('data', {}).get('products', [])
        self.nearai_agent_client.add_system_log (f"Found {len(products)} products")

        # disabling until agent makes use of it
        # self.nearai_agent_client.write_file("last_search_results.json", json.dumps(products))

        with open('shirt-data.json', 'r', encoding='utf-8') as file:
            shirt_data = json.loads(file.read())
            for shirt in shirt_data:
                products.insert(0, shirt)

        formatted_products = CommonTools.format_products(min_price, products)

        if self.process_product_results_function:
            self.process_product_results_function(formatted_products)

        return formatted_products

    @staticmethod
    def format_products(min_price, products):
        formatted_products = []
        for product in products:
            title = product.get('product_title', '')
            description = product.get('product_description', '')
            if description is None:
                description = ""

            # Handle cases where 'offer' might be None
            offer = product.get('offer', {}) or {}
            price = offer.get('price', 'Price not available')

            # Parse price if available and skip if it is below min_price
            try:
                price_value = float(price.replace('$', '').replace(',', ''))
                if price_value < min_price:
                    continue
            except ValueError:
                # If price parsing fails, skip this product
                price_value = 'Price not available'

            id = product.get('product_id', '')
            product_url = offer.get('offer_page_url', '') or product.get('product_page_url', '')
            images = product.get('product_photos', [])
            image = images[0] if images else ''

            # Store the actual values in the mapping
            formatted_product = {
                "id": id,
                "title": title,
                "description": description,
                "price": price,
                "url": product_url,
                "image": image,
                "payment_methods": product.get('offer', {}).get('payment_methods', "")
            }
            formatted_products.append(formatted_product)

        return formatted_products