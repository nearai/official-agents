import json
import random, datetime
from typing import Optional

from merchant_config import merchant_id, payment_address


class ProductsAITP:
    def __init__(self, env):
        self.env = env

    def generate_id(self):
        return ''.join(random.choices('0123456789abcdef', k=32))

    @staticmethod
    def convert_usd_to_number(price) -> Optional[float]:
        if not price:
            return None
        try:
            return float(price.replace("$", "").strip() or 0)
        except:
            return None

    def generate_request_decision(self, product_data):
        quote_time = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        results = product_data[0]
        parsed_product_data = json.loads(results)
        body = parsed_product_data["body"]
        request_decision = {
            "$schema": "https://aitp.dev/v1/decision/schema.json",
            "request_decision": {
                "id": f"request_decision_{self.generate_id()}",
                "type": "products",
                "options": [
                    {
                        "id": product.get("code", ""),
                        "name": product.get("name", ""),
                        "description": product.get("description", ""),
                        "image_url": product.get("imageUrl", ""),
                        "url": product.get("url", ""),
                        "quote": {
                            "type": "Quote",
                            "payee_id": payment_address,
                            "quote_id": f"quote_{self.generate_id()}",
                            "payment_plans": [
                                {
                                    "amount": self.convert_usd_to_number(product.get("price", "0")),
                                    "currency": "USD",
                                    "plan_id": "nUSDC",
                                    "plan_type": "one-time"
                                }
                            ] if product.get("price") else [],
                            "valid_until": quote_time
                        },
                    } for product in (body or [])
                    if isinstance(product, dict)
                       and (lambda p: True if self.convert_usd_to_number(product.get("price", "")) is not None else False)(product)
                       and product.get("code") and product.get("name")
                ]
            }
        }
        # First 6 complete products makes two nice rows of three or three of two on many screen sizes
        request_decision["request_decision"]["options"] = request_decision["request_decision"]["options"][:6]
        return [json.dumps(request_decision)]

    def generate_decision(self, add_to_cart_data, request_decision_id):
        body = add_to_cart_data[0]
        parsed_product_data = json.loads(body)
        body = parsed_product_data["body"]

        request_decision = {
            "$schema": "https://aitp.dev/v1/decision/schema.json",
            "decision": {
                "request_decision_id": request_decision_id,
                "options": [
                    {
                        "cartId": body["cartId"],
                        "productName": body["productName"],
                        "productPrice": body["price"],
                        "totalPrice": body["totalPrice"],
                        "shippingPrice": body["shippingPrice"],
                        "shippingTaxes": body["shippingTaxes"],
                        "totalPrice": body["totalPrice"]
                    }
                ]
            }
        }
        return [json.dumps(request_decision)]


    def validate_aitp_message(self, message):
        pass

    def generate_quote_response(self, result):
        quote_time = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Extract costs from the result
        subtotal = result["body"]["cost"]["subtotal"]["value"] / 100  # Convert cents to dollars
        margin_price = result["body"]["cost"]["margin"]["value"]
        if margin_price:
            subtotal += (margin_price / 100)

        shipping = result["body"]["cost"]["shipping"]["value"] / 100

        quote_response = {
            "$schema": "https://aitp.dev/v1/payments.schema.json",
            "quote": {
                "type": "Quote",
                "payee_id": "sound-sage.near",
                "quote_id": result["body"]["id"],
                "payment_plans": [
                    {
                        "amount": subtotal,
                        "currency": result["body"]["cost"]["subtotal"]["currency"],
                        "plan_id": "amazon",
                        "plan_type": "one-time"
                    },
                    {
                        "amount": shipping,
                        "currency": result["body"]["cost"]["shipping"]["currency"],
                        "plan_id": "shipping",
                        "plan_type": "one-time"
                    }
                ],
                "valid_until": quote_time
            }
        }
        return [json.dumps(quote_response)]
