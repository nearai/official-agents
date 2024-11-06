# Basic Auction Contract

This directory contains a JavaScript contract that is for the `shopper` NearAI agent demo.

The contract is a simple auction where you can place an order and view the orders.

It is deployed to demo-shopper.testnet

---

## How to Build Locally?

Install the [NEAR CLI](https://docs.near.org/tools/near-cli#installation) and run:

Install the dependencies:

```bash
npm install
```

Build the contract:

```bash
npm run build
```

## How to Test Locally?

```bash
npm run test
```

## How to Deploy?

Install the [NEAR CLI](https://docs.near.org/tools/near-cli#installation) and run:

```bash
# Create a new testnet account
near create <contractId> --useFaucet

# Deploy the contract
near deploy <contractId> ./build/auction-contract.wasm

# Initialize the contract
near call <contractId> init '{"key": "value"}' --accountId <contractId>
```