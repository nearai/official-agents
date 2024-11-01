import requests

ACCESS_TOKEN = 'NzlAd6J01NRaLllAe4TXUA7XoSpaox70gNNPgcZs'  # Replace with your actual access token

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

response = requests.get('https://api.printful.com/stores', headers=headers)

if response.status_code == 200:
    stores = response.json()['result']
    for store in stores:
        print(f"Store ID: {store['id']}, Store Name: {store['name']}")
else:
    print('Failed to retrieve stores.')
    print('Status Code:', response.status_code)
    print('Response:', response.text)