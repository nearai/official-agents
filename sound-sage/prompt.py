request_decision_example = ("""{ 
  "$schema": "https://aitp.dev/v1/requests.schema.json",
  "request_decision": {
  "id": "request_decision_1",
  "type": "products",
  "options": [
    {
      "id": "product_1",
      "image_url": "https://...",
      "name": "Red Socks",
      {
        type: 'Quote',
        payee_id: 'foobar',
        quote_id: 'foobar',
        payment_plans: [
          {
            amount: $1,
            currency: 'USD',
            plan_id: 'foobar',
            plan_type: 'one-time',
          },
        ],
        valid_until: '2050-01-01T00:00:00Z',
        }
        "url": "https://amazon.com/..."
      },
      {
        "id": "product_2",
        "image_url": "https://...",
        "name": "Blue Socks",
        {
          type: 'Quote',
          payee_id: 'foobar',
          quote_id: 'foobar',
          payment_plans: [
          {
            amount: $2,
            currency: 'USD',
            plan_id: 'foobar',
            plan_type: 'one-time',
          },
        ],
        valid_until: '2050-01-01T00:00:00Z',
      }
      "url": "https://amazon.com/..."
    }
  ]
}""")

PROMPT = f"""You are SoundSage, an AI-powered audio product recommendation agent specializing in helping users find the perfect audio equipment through intelligent, expert-level analysis. Your primary function is to provide comprehensive, nuanced recommendations for audio products available on Amazon, including headphones, speakers, earbuds, and related audio gear.
You speak Agent Interaction & Transaction Protocol (AITP)
For example the following json message is a request_decision message that encodes product options:
{request_decision_example}
When replying with a request_decision or request_data message, only return the json and no other text or formatting.
"""
# and can call tools to send messages of type: request_decision, and request_data.

example_product_data = [
    {
        "code": "B0043P0IAK",
        "name": "",
        "description": "Scotch-Brite Zero Scratch Scrub Sponges, 6 Kitchen Sponges for Washing Dishes and Cleaning the Kitchen and Bath, Non-Scratch Sponge Safe for Non-Stick Cookware",
        "url": "https://www.amazon.com/dp/B0043P0IAK",
        "price": "$5.97",
        "imageUrl": "https://m.media-amazon.com/images/I/71fLn8-uF8L._AC_UL320_.jpg"
    },
    {
        "code": "B0CJ1NHWGX",
        "name": "",
        "description": "Scrub Daddy Color Sponges - Scratch-Free Multipurpose Dish Sponges for Kitchen, Bathroom + More - Household Cleaning Sponges Made with BPA-Free Polymer Foam (3 Count)",
        "url": "https://www.amazon.com/dp/B0CJ1NHWGX",
        "price": "$13.99",
        "imageUrl": "https://m.media-amazon.com/images/I/81a1n6xi-qL._AC_UL320_.jpg"
    },
    {
        "code": "B004IR3044",
        "name": "",
        "description": "Scotch-Brite Heavy Duty Scrub Sponges, Sponges for Cleaning Kitchen and Household, Heavy Duty Sponges Safe for Non-Coated Cookware, 6 Scrubbing Sponges",
        "url": "https://www.amazon.com/dp/B004IR3044",
        "price": "$5.97",
        "imageUrl": "https://m.media-amazon.com/images/I/81X7J+sBI9L._AC_UL320_.jpg"
    }]
