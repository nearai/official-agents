import requests
import json
import os
ACCESS_TOKEN = os.environ.get('PRINTFUL_ACCESS_TOKEN', None)

def create_order(address, size, color, print_response=False) -> bool:
    global ACCESS_TOKEN
    STORE_ID = '14709021'          
    API_URL = 'https://api.printful.com/orders'

    # Set up headers with Bearer token
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    #Define the order data
    order_data = {
        "recipient": {
            "name": address['name'],
            "address1": address['address1'],
            "address2": address['address2'],
            "city": address['city'],
            "state_code": address['state_code'],
            "country_code": address['country_code'],
            "zip": address['zip']
        },
        "store_id": STORE_ID,
        "items": [
            {
                "sync_variant_id": 4600259112,  # Replace with the actual variant ID
                "quantity": 1,
            }
        ],
    
        "shipping": "STANDARD",
        "external_id": "order_1231"
    }

    # Send the POST request to create the order
    response = requests.post(API_URL, headers=headers, data=json.dumps(order_data))

    # Check if the request was successful
    if response.status_code == 200:
        if print_response:
            print("Order created successfully:")
            print(response.json())
        return True
    else:
        print(f"Failed to create order: {response.status_code}")
        print(response.text)
        return False