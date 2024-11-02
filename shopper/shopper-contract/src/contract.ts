// Find all our documentation at https://docs.near.org
import { NearBindgen, near, call, view, AccountId, NearPromise, initialize, assert } from "near-sdk-js";

class Order {
  ordering_account: AccountId;
  order_deposit: bigint;
  order_token: string;
}

@NearBindgen({ requireInit: true })
class ShopContract {
  orders: Order[] = [];

  @initialize({ privateFunction: true })
  init() {
    this.orders = []
  }

  @call({ payableFunction: true })
  order({ order_token } : { order_token: string } ) {

    assert(order_token.length > 0, "Order Token must be provided");
    assert(this.orders.length <= 10, "Maximum orders reached");

    // Current order
    const order_deposit = near.attachedDeposit();
    const ordering_account = near.predecessorAccountId();

    // Check if the deposit is sufficient
    const price = 0.01;
    assert(order_deposit > price, `You must attach a deposit of ${price}`);

    const order = {ordering_account, order_deposit, order_token};
    this.orders.push( order ); // Save the new order
  }

  @view({})
  get_orders(): Order[] {
    return this.orders;
  }

  // todo disable after testing
  @call({})
  clear_orders( ) {
    this.orders = [];
  }


}