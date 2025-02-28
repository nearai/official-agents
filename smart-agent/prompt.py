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
When replying with a request_decision, only return the json and no other text or formatting.
"""
# and can call tools to send messages of type: request_decision, and request_data.

# Note this data is in the request_decision format but the /amazon_search_products data will not be
example_product_data = [
    {
        "id": "product_1",
        "name": "JBL Tour One M2",
        "description": "A short, summarized description about the headphones",
        "five_star_rating": 4.2,
        "reviews_count": 132,
        "quote": {
            "type": "Quote",
            "payee_id": "foobar",
            "quote_id": "foobar",
            "payment_plans": [
                {
                    "amount": 199.5,
                    "currency": "USD",
                    "plan_id": "foobar",
                    "plan_type": "one-time"
                }
            ],
            "valid_until": "2050-01-01T00:00:00Z"
        },
        "image_url": "https://m.media-amazon.com/images/I/61rJmoiiYHL._AC_SX679_.jpg",
        "url": "https://www.amazon.com/JBL-Tour-One-Cancelling-Headphones/dp/B0C4JBTM5B"
    },
    {
        "id": "product_2",
        "name": "Soundcore by Anker, Space One",
        "short_variant_name": "Space One",
        "five_star_rating": 3.5,
        "quote": {
            "type": "Quote",
            "payee_id": "foobar",
            "quote_id": "foobar",
            "payment_plans": [
                {
                    "amount": 79.99,
                    "currency": "USD",
                    "plan_id": "foobar",
                    "plan_type": "one-time"
                }
            ],
            "valid_until": "2050-01-01T00:00:00Z"
        },
        "image_url": "https://m.media-amazon.com/images/I/51EXj4BRQaL._AC_SX679_.jpg",
        "url": "https://www.amazon.com/Soundcore-Cancelling-Headphones-Reduction-Comfortable/dp/B0C6KKQ7ND",
        "variants": [
            {
                "id": "product_3",
                "name": "Soundcore by Anker, Jet Black",
                "short_variant_name": "Jet Black",
                "five_star_rating": 3.75,
                "quote": {
                    "type": "Quote",
                    "payee_id": "foobar",
                    "quote_id": "foobar",
                    "payment_plans": [
                        {
                            "amount": 89.99,
                            "currency": "USD",
                            "plan_id": "foobar",
                            "plan_type": "one-time"
                        }
                    ],
                    "valid_until": "2050-01-01T00:00:00Z"
                },
                "image_url": "https://m.media-amazon.com/images/I/51l80KVua0L._AC_SX679_.jpg",
                "url": "https://www.amazon.com/Soundcore-Cancelling-Headphones-Reduction-Comfortable/dp/B0C6KFZC9Z"
            },
            {
                "id": "product_4",
                "name": "Soundcore by Anker, Cream",
                "short_variant_name": "Cream",
                "five_star_rating": 3.75,
                "quote": {
                    "type": "Quote",
                    "payee_id": "foobar",
                    "quote_id": "foobar",
                    "payment_plans": [
                        {
                            "amount": 74.99,
                            "currency": "USD",
                            "plan_id": "foobar",
                            "plan_type": "one-time"
                        }
                    ],
                    "valid_until": "2050-01-01T00:00:00Z"
                },
                "image_url": "https://m.media-amazon.com/images/I/51QVszp82CL._AC_SX679_.jpg",
                "url": "https://www.amazon.com/Soundcore-Cancelling-Headphones-Reduction-Comfortable/dp/B0C6KJ3R71"
            }
        ]
    },
    {
        "id": "product_5",
        "name": "Sony WH-1000XM5",
        "quote": {
            "type": "Quote",
            "payee_id": "foobar",
            "quote_id": "foobar",
            "payment_plans": [
                {
                    "amount": 399.99,
                    "currency": "USD",
                    "plan_id": "foobar",
                    "plan_type": "one-time"
                }
            ],
            "valid_until": "2050-01-01T00:00:00Z"
        },
        "image_url": "https://m.media-amazon.com/images/I/61eeHPRFQ9L._AC_SX679_.jpg",
        "url": "https://www.amazon.com/Sony-WH-1000XM5-Headphones-Hands-Free-WH1000XM5/dp/B0BXYCS74H"
    },
    {
        "id": "product_6",
        "name": "Edifier STAX Spirit S3",
        "quote": {
            "type": "Quote",
            "payee_id": "foobar",
            "quote_id": "foobar",
            "payment_plans": [
                {
                    "amount": 348,
                    "currency": "USD",
                    "plan_id": "foobar",
                    "plan_type": "one-time"
                }
            ],
            "valid_until": "2050-01-01T00:00:00Z"
        },
        "image_url": "https://m.media-amazon.com/images/I/61E4YsCrICL._AC_SX679_.jpg",
        "url": "https://www.amazon.com/Sony-WH-1000XM5-Headphones-Hands-Free-WH1000XM5/dp/B0BXYCS74H"
    }
]
