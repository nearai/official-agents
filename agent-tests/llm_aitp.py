import json

def dynamic_request_decision_test(env):

    prompt = """You are an agent that speaks Agent Interaction & Transaction Protocol (AITP)
            and calls tools to send messages of type: request_decision, and request_data.
            For example the following json message is a request_decision message that encodes product options:

            { "$schema": "https://aitp.dev/v1/requests.schema.json",
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
              }
              
              When replying with a request_decision or request_data message, only return the json and no other text or formatting.
              """

    product_data = [
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

    # Real usage would check client capabilities to decide whether to register the tool
    tool_registry = env.get_tool_registry(True)
    # tool_registry.register_tool(self.request_decision)
    # tools = tool_registry.get_all_tool_definitions()
    # print(f"Tools: {tools}")


    result = env.completion(
        [{"role": "system", "content": prompt},
         {"role": "system", "content": json.dumps(product_data)},
         {"role": "user", "content": "what product choices do I have?"}],
        response_format={"type": "json_object"}
    )
    # tools=tools,

    env.add_reply(result)
