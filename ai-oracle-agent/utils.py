import json
import re

import requests
from bs4 import BeautifulSoup
from nearai.agents.environment import Environment

MODEL = "fireworks::accounts/fireworks/models/llama-v3p1-70b-instruct"
TEMPERATURE = 0
MAX_TOKENS = 8192


def fetch_page_content(url):
    """Fetches the content of a web page."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_relevant_text(html_content):
    """Extracts visible text from the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove scripts and styles
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    return soup.get_text(separator=' ', strip=True)


def determine_name(env: Environment, text, prompt):
    """Uses an LLM to determine the name of the current US President."""
    return env.signed_completion([
        {
            "role": "system",
            "content": "You are an assistant that extracts answer for the user's query from the provided text only. "
                       "Use strictly the provided text and nothing else for your response."
        },
        {
            "role": "user",
            "content": f"""
        Extract the first name and last name of {prompt}. 
        Respond with only the first name and last name of the person mentioned, avoiding middle names, initials, titles, or suffixes. 
        Use only the following text to find the answer. Do not use any prior knowledge or external information.
        === BEGIN TEXT ===
        {text}
        === END TEXT ===
        Reply with only the first name and last name, and nothing else.
        """
        }], model=MODEL, temperature=TEMPERATURE, max_tokens=MAX_TOKENS
    )


def check_consistency_with_llm(env: Environment, responses, prompt):
    """Uses an LLM to check if all responses are consistent."""
    response_texts = "\n".join([f"Response {i + 1}: {response}" for i, response in enumerate(responses)])
    prompt = f"""Given the following responses about {prompt},  determine if they all refer to the same individual.
{response_texts}

Instructions:
- If names are similar, such as "Albert Einstein" and "Einstein", treat them as referring to the same individual.
- If more than half agree, return the consistent response. {{"result_found": true, "value": "..."}}
- If not, return the {{"result_found": false}}

Only respond with valid JSON. Do not include any other text.

Example 1:
Response 1: Albert Einstein
Response 2: Einstein
Response 3: Prof. Albert Einstein
Response 4: Marie Curie 
Output: {{"result_found": true, "value": "Albert Einstein"}}

Example 2:
Response 1: John Doe
Response 2: Albert Einstein
Response 3: Isaac Newton
Output: {{"result_found": false}}"""

    messages = [{
        "role": "system",
        "content": prompt
    }, {
        "role": "user",
        "content": "Always reply with valid JSON ONLY. Do not include anything else in your response"
    }]

    response = env.signed_completion(messages, model=MODEL, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)

    return response, messages


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
            print("Parsing response", response)
            parsed_response = json.loads(response)
            return parsed_response
        except json.JSONDecodeError:
            try:
                response = response.replace(";", "")
                print("Parsing response", response)
                parsed_response = json.loads(response)
                return parsed_response
            except json.JSONDecodeError:
                try:
                    response = response.replace("json{", "{")
                    print("Parsing response", response)
                    parsed_response = json.loads(response)
                    return parsed_response
                except json.JSONDecodeError:
                    print(f"JSON decode error: {response}")
                    return {"message": "JSON decode error"}


def get_oracle_name(env: Environment):
    return f"{env.get_primary_agent().name}/{env.get_primary_agent().version}"


def prepare_app_html(env: Environment, prompt, value, responses, messages, completion, signature, public_key):
    html = env.read_file("publish.html")
    html = html.replace("{{%prompt%}}", prompt)
    html = html.replace("{{%value%}}", value)
    html = html.replace("{{%responses%}}", json.dumps(responses))

    html = html.replace("{{%agent_name%}}", get_oracle_name(env))
    html = html.replace("{{%agent_id%}}", env.get_primary_agent().get_full_name())

    html = html.replace("{{%signature%}}", signature)
    html = html.replace("{{%public_key%}}", public_key)
    html = html.replace("{{%model%}}", MODEL)
    html = html.replace("{{%messages%}}", json.dumps(messages))
    html = html.replace("{{%temperature%}}", str(TEMPERATURE))
    html = html.replace("{{%max_tokens%}}", str(MAX_TOKENS))
    html = html.replace("{{%completion%}}", json.dumps(completion))

    env.write_file("index.html", html)
