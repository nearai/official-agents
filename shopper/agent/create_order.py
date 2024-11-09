from typing import Optional, Dict

import requests
import json
import os
import uuid

STORE_ID = '14709021'
API_URL = 'https://api.printful.com/orders'

class OrderFactory:

    def __init__(self, printful_access_token):
        self.printful_access_token = printful_access_token

    @staticmethod
    def find_variant_id(color, size):
        product_id = 365294931
        product_name = "Near Redacted Shirt"

        variants = {
            "aqua": {
                "S": 4600259102,
                "M": 4600259104,
                "L": 4600259105,
                "XL": 4600259106,
                "2XL": 4600259108,
                "3XL": 4600259109,
                "4XL": 4600259110
            },
            "heather": {
                "S": 4600259112,
                "M": 4600259113,
                "L": 4600259114,
                "XL": 4600259116,
                "2XL": 4600259117,
                "3XL": 4600259118,
                "4XL": 4600259120
            },
            "gold": {
                "S": 4600259121,
                "M": 4600259122,
                "L": 4600259124,
                "XL": 4600259125,
                "2XL": 4600259127,
                "3XL": 4600259128,
                "4XL": 4600259129
            }
        }
        variants_for_color = variants.get(color.lower())
        if variants_for_color is None:
            raise ValueError(f"Color {color} is not available for product {product_name}")
        variant_id = variants_for_color.get(size)
        if variant_id is None:
            raise ValueError(f"Size {size} is not available for product {product_name} in color {color}")
        return variant_id

    def create_order(self, color, size, name, address1, address2, city, state, country, zip, print_response=False) -> Optional[Dict[str, str]]:

        variant_id = OrderFactory.find_variant_id(color, size)

        # Set up headers with Bearer token
        headers = {
            'Authorization': f'Bearer {self.printful_access_token}',
            'Content-Type': 'application/json'
        }

        # Generate a 10 digit unique order ID
        agent_order_id = str(uuid.uuid4().int)[:10]

        #Define the order data
        order_data = {
            "recipient": {
                "name": name,
                "address1": address1,
                "address2": address2,
                "city": city,
                "state_code": state,
                "country_code": country,
                "zip": zip
            },
            "store_id": STORE_ID,
            "items": [
                {
                    "sync_variant_id": variant_id, #  4600259112,  # Replace with the actual variant ID
                    "quantity": 1,
                }
            ],

            "shipping": "STANDARD",
            "external_id": f"{agent_order_id}"
        }

        # Send the POST request to create the order
        response = requests.post(API_URL, headers=headers, data=json.dumps(order_data))

        # Check if the request was successful
        if response.status_code == 200:
            if print_response:
                print("Order created successfully:")
                print(response.json())
            order_id = response.json()['result']['id']
            return {
                "order_id": order_id,
                "agent_order_id": agent_order_id
            }
        else:
            print(f"Failed to create order: {response.status_code}")
            print(response.text)
            return {
                "error": response.status_code,
                "message": response.text
            }


if __name__ == "__main__":
    printful_access_token = os.getenv("PRINTFUL_ACCESS_TOKEN")
    printful = OrderFactory(printful_access_token)
    name = "John Doe",
    address1 = "123 Main St",
    address2 = "",
    city = "Los Angeles",
    state = "CA",
    country = "US",
    zip = "90001"
    printful.create_order("S", "Aqua", name, address1, address2, city, state, country, zip, print_response=True)