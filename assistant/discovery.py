import json
import re
import time
from typing import List, Dict, Any


# functions adapted from discovery agent
def chat_with_vector_store(env, vs_id, user_message):
    max_attempts = 10
    attempts = 0
    vector_results = None


    while attempts < max_attempts:
        vector_results = env.query_vector_store(vs_id, user_message)
        if vector_results:
            break

        attempts += 1
        time.sleep(1)

    if not vector_results:
        print("vector store not ready.")

    processed_results = process_vector_results([vector_results])

    response_message = generate_llm_response(env, env.list_messages(), processed_results)

    response = parse_response(response_message)

    return response

def generate_llm_response(env, messages, processed_results):
    system_prompt = """
    You're an AI assistant that finds the one and only one best AI Agent to serve the user's request. 
    Another agent will read your reply and execute the agent you found.
    You can search a vector store for information relevant to the user's query.        
    Use the provided vector store results to inform your response, but don't mention the vector store directly.
    
    If you find an agent that can help the user, provide the the following response:
    ```
    {
        "agent_url": "user.near/agent/1.0",
        "message": "..."
    }
    ```
    
    You will find `agent_url` in the vector store. 
    `message` is the portion of the user's previous message that should be passed to the found agent. 
    Do not ask follow up questions because another agent will forward the initial user's message to the found agent.
    Found agents must exist in the vector store. Never invent agents.
    
    If you don't find an agent that can help the user, provide the the following response:
    ```
    {
        "agent_url": null
        "message": null
    }
    ```
    Always return a valid JSON string. Always return maximum 1 agent.
    """

    vs_results = "\n=========\n".join(
        [f"{result.get('chunk_text', 'No text available')}" for result in processed_results or []]
    )
    messages = [
        {"role": "system", "content": system_prompt},
        *messages,
        {
            "role": "system",
            "content": f"User query: {messages[-1]['content']}\n\nRelevant information:\n{vs_results}",
        },
    ]
    return env.completion(messages, response_format={"type": "json_object"})


def process_vector_results(results) -> List[Dict[str, Any]]:
    flattened_results = [item for sublist in results for item in sublist]
    return flattened_results[:20]


def parse_response(response):
    try:
        print("Parsing response", response)
        parsed_response = json.loads(response)
        return parsed_response

    except Exception:
        markdown_json_match = re.match(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if markdown_json_match:
            response = markdown_json_match.group(1)

        else:
            markdown_match = re.search(r'```(.*?)```', response, re.DOTALL)
            if markdown_match:
                response = markdown_match.group(1).replace('\n', '').strip()
            else:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    response = json_match.group(0).replace('\n', '').strip()
        try:
            parsed_response = json.loads(response)
            return parsed_response
        except json.JSONDecodeError:
            try:
                response = response.replace(";", "")
                parsed_response = json.loads(response)
                return parsed_response
            except json.JSONDecodeError:
                try:
                    response = response.replace("json{", "{")
                    parsed_response = json.loads(response)
                    return parsed_response
                except json.JSONDecodeError:
                    print(f"JSON decode error: {response}")
                    return {"message": "JSON decode error"}