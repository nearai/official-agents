request_decision = {
    "$schema": "https://aitp.dev/v1/requests.schema.json",
    "request_decision": {
        "id": "request_decision_1",
        "type": "products",
        "options": [
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
    }
}

decision = {
    "$schema": "https://aitp.dev/v1/decision/schema.json",
    "decision": {
        "request_decision_id": "f71e151f-1d24-4659-99d1-66fe5ccffc8d",
        "options": [
            {
                "id": "product_4",
                "name": "Soundcore by Anker, Cream",
                "quantity": 1
            }
        ]
    }
}

request_data = {
    "$schema": "https://aitp.dev/v1/data/schema.json",
    "request_data": {
        "id": "c00d9f0c-89a7-4a74-8c57-0b9aa16be348",
        "title": "Shipping Info (International)",
        "description": "Great! Let's start with your shipping info.",
        "fillButtonLabel": "Fill out shipping info",
        "form": {
            "json_url": "https://app.near.ai/api/v1/aitp/data/forms/shipping_address_international.json"
        }
    }
}

data = {
    "$schema": "https://aitp.dev/v1/data/schema.json",
    "data": {
        "request_data_id": "1ecdf8cd-5187-4460-ae79-ca1191cf68c9",
        "fields": [
            {
                "id": "favorite_color",
                "label": "Favorite Color",
                "value": "Blue"
            },
            {
                "id": "favorite_number",
                "label": "Favorite Number",
                "value": "7"
            }
        ]
    }
}

quote_with_shipping = {
    "$schema": "https://aitp.dev/v1/payments/schema.json",
    "quote": {
        "type": "Quote",
        "payee_id": "foobar",
        "quote_id": "foobar",
        "payment_plans": [
            {
                "amount": 74.99,
                "currency": "USD",
                "plan_id": "amazon",
                "plan_type": "one-time"
            },
            {
                "amount": 0.00,
                "currency": "USD",
                "plan_id": "free_shipping",
                "plan_type": "one-time"
            }
        ],
        "valid_until": "2050-01-01T00:00:00Z"
    }
}

payment_authorization= {
    "$schema": "https://aitp.dev/v1/payments.schema.json",
    "payment_authorization": {
        "quote_id": "quote_1234",
        "payer_id": "flatirons.near",
        "product_id": "product_4",
        "details": [
            {
                "network": "NEAR",
                "token_type": "USDC",
                "amount": 100.84,
                "wallet_address": "demo-shopper.near",
                "signature": "jfjw3rfg7atr93s8r903ifij9jf93fa93u;f989a839ufa38jid"
            }
        ],
        "authorization_timestamp": "2025-03-01T12:00:00Z"
    }
}

payment_result = {
    "$schema": "https://aitp.dev/v1/payments.schema.json",
    "payment_result": {
        "transaction_id": "jfu9u439fr9ua3w9fja8fua9fu39ruaiesfh8efuap39",
        "quote_id": "4qpQXbm7p5bgjuy1QKzi",
        "result": "success",
        "message": "JBL Tune 510BT - Bluetooth headphones purchased successfully",
        "timestamp": "2025-03-01T12:01:00Z",
        "details": []
    }
}