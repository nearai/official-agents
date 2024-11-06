# Shopping assistant agent

This research agent explores the capabilities needed in a good shopping assistant agent.
It uses the NearAI agentic framework.

## Configuration
Initially the agent runs in test mode and returns hardcoded
results (NEAR and crypto shirts). To change this behavior set the agent level secret `test_mode` to False.

The RapidApi Google product search API is used to find products. This requires a rapidapi api key 
with a rapidapi app configured to use the real time product search api. The api key should be set as an agent 
secret named `rapidapi_key`. 

Certain products known to the Agent can be automatically ordered by the agent through the Printful api with payment
handled through a smart contract. This requires a Printful access token set as an agent secret named `printful_access_token`.


## Functionality
This Agent can perform the following tasks:
 * Product search
 * Placing Orders with integrated Merchants (Printful)
 * Initiating payment with a NEAR compatible wallet

The user's initial message should generate both an LLM response message and rapidapi / google product search.
Retrieved products are then fed into a html template which is written to the output. Known products are then added
to the top of the search results. These known products may be purchased with $NEAR and are rendered with  
template_near_item.html. A button for those items submits an iframe post message to communicate back to the agent code
to place a draft Printful order. The template is re-rendered with the order information and an iframe post message
triggers the user transaction signing flow.