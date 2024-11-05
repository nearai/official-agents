import requests

# Replace 'YOUR_ACCESS_TOKEN' with your actual OAuth 2.0 access token
ACCESS_TOKEN = 'NzlAd6J01NRaLllAe4TXUA7XoSpaox70gNNPgcZs'

# Set up headers with Bearer token
headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

# Get the list of product templates
response = requests.get('https://api.printful.com/product-templates', headers=headers)

if response.status_code == 200:
    templates = response.json()['result']['items']
    print(templates)
    for template in templates:
        print(f"Template Name: {template['title']}, Template ID: {template['id']}")
else:
    print('Failed to retrieve product templates.')
    print('Status Code:', response.status_code)
    print('Response:', response.json())


