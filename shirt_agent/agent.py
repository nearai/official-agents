from create_order import create_order
import json 

shirt_sizes = ["S", "M", "L", "XL"]
shirt_colors = ["Blue", "Yellow", "Green"]

# Initialize collected information
size = None
color = None
address = {
    "name": "",
    "address1": "",
    "city": "",
    "state_code": "",
    "country_code": "",
    "zip": ""
}

def validate_size(size_candidate):
    return size_candidate in shirt_sizes

def validate_color(color_candidate):
    return color_candidate in shirt_colors

def get_missing_info(size, color, address):
    missing_items = []
    if not size:
        missing_items.append("shirt size")
    if not color:
        missing_items.append("shirt color")
    required_address_fields = ["name", "address1", "city", "state_code", "country_code", "zip"]
    missing_address_fields = [field for field in required_address_fields if not address.get(field)]
    if missing_address_fields:
        missing_items.append("address (" + ", ".join(missing_address_fields) + ")")
    return missing_items

def address_complete(address):
    return all(address.values())

def prompt_user_with_message(message):      
    env.add_message("agent", message)
    env.request_user_input()

def process_user_response():
    global size, color, address

    # Add user's message to conversation history
    #env.add_message({"role": "user", "content": user_message})

    user_response_is_incomplete = True
    while(user_response_is_incomplete):
        # Use LLM to extract information
        extraction_prompt = {
            "role": "system",
            "content": """From the user's response, extract any information about shirt size, shirt color, and address fields. 
            Provide the extracted information in JSON format with keys 'size', 'color', and 'address'. 
            The 'address' should be a JSON object with keys 'name', 'address1', 'city', 'state_code', 'country_code', 'zip'.
            If any information is missing, omit that key in the JSON."""
        }
        #env.add_message(extraction_prompt)
        extraction_response = env.completion(env.list_messages()+ [extraction_prompt])
        
        # Try to parse the JSON
        try:
            extracted_info = json.loads(extraction_response)
        except json.JSONDecodeError:
            # Handle parsing error, ask the user again
            prompt_user_with_message("Sorry, I couldn't understand your response. Could you please provide the information again?")
            break
            #return
        
        # Update the collected information
        if 'size' in extracted_info:
            size_candidate = extracted_info['size']
            if validate_size(size_candidate):
                size = size_candidate
            else:
                # Inform the user that the size is not available
                #assistant_message = {"role": "agent", "content": f"Sorry, we do not have size '{size_candidate}'. Available sizes are {', '.join(shirt_sizes)}. Please select a size from the available options."}
                #env.add_message(assistant_message)
                process_user_response(f"Sorry, we do not have size '{size_candidate}'. Available sizes are {', '.join(shirt_sizes)}. Please select a size from the available options.")
                size = None
                break
        if 'color' in extracted_info:
            color_candidate = extracted_info['color']
            if validate_color(color_candidate):
                color = color_candidate
            else:
                # Inform the user that the color is not available
                process_user_response(f"Sorry, we do not have color '{color_candidate}'. Available colors are {', '.join(shirt_colors)}. Please select a color from the available options.")
                color = None
                break
        if 'address' in extracted_info:
            for field in extracted_info['address']:
                address[field] = extracted_info['address'][field]
        
        # Check if all required information is collected
        missing_info = get_missing_info(size, color, address)
        if missing_info:
            # Ask for missing information
            if len(missing_info) == 1:
                agent_message = f"Please provide your {missing_info[0]}."
            else:
                agent_message = f"Please provide your {', '.join(missing_info[:-1])}, and {missing_info[-1]}."
            prompt_user_with_message(agent_message)
            break
        else:
            # All information collected, proceed to create order
            #Confirm with the user all the information that has been collected so far
            #assistant_prompt = f"Please confirm that the following information is correct: Shirt size: {size}, Shirt color: {color}, Shipping address: {address}."
            #assistant_message = {"role": "agent", "content": assistant_prompt}
            #env.add_message(assistant_message)
            #env.completion(env.list_messages()+ [assistant_message])
            #env.request_user_input()
            #if user confirms, then create order
            user_response_is_incomplete = False

            #check to see that the output to confirm that the order has been created
            create_order(address, size, color)
            agent_message = f"Thank you! Your order for a {color} shirt of size {size} has been placed and will be shipped to your address."
            env.add_message("agent", agent_message)


# Main flow
prompt = {"role": "system", "content": "You are a general purpose assistant agent"}
result = env.completion([prompt] + env.list_messages())
env.add_message("agent", result)
env.request_user_input()

question_for_llm =  {"role": "system", "content": "Did the user ask to purchase a shirt just now? Answer with only yes or no"}
did_user_ask_to_buy_shirt = env.completion(env.list_messages() + [question_for_llm]).replace("\n", " ")

if "yes" in did_user_ask_to_buy_shirt.lower():
    #print(">>>>>>> Right inside if block")
    agent_message = "Great! To complete your order, please provide your shirt size, shirt color, and shipping address."
    env.add_message("agent", agent_message)
    process_user_response()
else:
    # Handle other cases
    agent_message = "How can I assist you today?"
    env.add_message("agent", agent_message)
