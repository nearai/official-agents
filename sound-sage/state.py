from pydantic import BaseModel
from typing import List, Dict, Optional

class State(BaseModel):
    cart_ids: List[str] = []
    total_amount: float = 0.0
    shipping_address: Dict[str, str] = {}

    def add_to_cart(self, product_id: str, price: float):
        self.cart_ids.append(product_id)
        self.total_amount += price

    def update_shipping_address(self, shipping_address: Dict[str, str]):
        self.shipping_address = {k: v if v is not None else "" for k, v in shipping_address.items()}

    def clear_cart(self):
        self.cart_ids = []
        self.total_amount = 0.0