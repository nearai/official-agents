import requests
import json

STORE_ID = '14709021'  # Replace with your actual store ID
ACCESS_TOKEN = 'NzlAd6J01NRaLllAe4TXUA7XoSpaox70gNNPgcZs'  # Replace with your actual access token

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

# Define the payload with store_id
payload = {
    'store_id': STORE_ID
}

# Get the list of synced products, including store_id in the JSON payload
response = requests.get('https://api.printful.com/store/products', headers=headers, json=payload)

if response.status_code == 200:
    products = response.json()['result']
    for product in products:
        print(f"Product ID: {product['id']}, Name: {product['name']}")
        # Get details of the product to find sync variants
        product_id = product['id']
        product_details = requests.get('https://api.printful.com/store/products/{}'.format(product_id), headers=headers, json=payload)
        if product_details.status_code == 200:
            variants = product_details.json()['result']['sync_variants']
            for variant in variants:
                print(f"Sync Variant ID: {variant['id']}, Variant Name: {variant['name']}")
        else:
            print('Failed to retrieve product details.')
            print('Status Code:', product_details.status_code)
            print('Response:', product_details.text)
else:
    print('Failed to retrieve store products.')
    print('Status Code:', response.status_code)
    print('Response:', response.text)
