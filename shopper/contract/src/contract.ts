// Find all our documentation at https://docs.near.org
import { NearBindgen, near, call, view, AccountId, NearPromise, initialize, assert } from "near-sdk-js";
import {signerAccountId} from "near-sdk-js/lib/api";

class Order {
  ordering_account: AccountId;
  order_deposit: bigint;
  order_id: string;
}

@NearBindgen({ requireInit: true })
class ShopContract {
  orders: Order[] = [];

  @initialize({ privateFunction: true })
  init() {
    this.orders = []
  }

  @call({ payableFunction: true })
  order({ order_id } : { order_id: string } ) {

    assert(order_id != null, "Order ID must be provided");
    assert(order_id.length > 0, "Order ID must be provided");
    assert(this.orders.length <= 10, "Maximum orders reached");

    // Current order
    const order_deposit = near.attachedDeposit();
    const ordering_account = near.signerAccountId();

    // Check if the deposit is sufficient
    const price = 0.01; // todo adjust
    assert(order_deposit > price, `You must attach a deposit of ${price}`);

    const order = {ordering_account, order_deposit, order_id};
    this.orders.push( order ); // Save the new order
  }

  @view({})
  get_orders(): Order[] {
    return this.orders;
  }

  @call({})
  clear_orders( ) {
    assert(near.signerAccountId() == near.currentAccountId(), "Only the owner can clear orders");
    this.orders = [];
  }


}