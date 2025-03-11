import json
import requests
import traceback

from nearai.agents.environment import Environment
from utils import Utils

class AitpSchemaHandler(object):
  def __init__(self, _env: Environment):
    self.env = _env
    self.utils = Utils()

  def fetch_schema_from_url(self, schema_url):
      """Fetch JSON schema from URL."""
      try:
          response = requests.get(schema_url)
          response.raise_for_status()
          return response.json()
      except Exception as e:
          print(f"Error fetching schema from {schema_url}: {e}")
          return None

  def sanitize_schema_response(self, schema_response):
    return self.utils.remove_null_values(schema_response)

  async def handle_schema_llm_call(self, schema, data):
    schema_url = schema.get("url")
    self.env.add_system_log(f"Fetching schema from URL: {schema_url}")
    json_schema = self.fetch_schema_from_url(schema_url)

    self.env.add_system_log(f"Schema Fetched: {json_schema}")

    if not json_schema:
      self.env.add_system_log("No schema found on the provided URL")
      return None

    messages = [{"role": "system", "content": f"""You are a developer. You are given a schema and a content. Your task is to fill the schema with the content provided by the user.
                  The output must be a code that returns a 'result' variable containing the final output. Do not include any other text since the code block will be executed programmatically.
                  - The $schema property must be respected. It should be the first line of the 'result' output and it should be '{schema_url}'.
                  - The code must be in Python.
                  - Do not use fake data, you have the information provided by the user
                  - DO NOT USE ANY EXTERNAL LIBRARIES AND BE CAREFUL WITH THE IMPORTS - the code runs in an isolated environment
                  - Return the result in a 'result' variable pure dict, don't run json.loads or json.dumps on it
                  - The code must start with exactly '```python' and end with exactly '```'
                  """},
        {"role": "user", "content": f"""
        ## Content: {str(data)}
        ## Schema: {json_schema}
        """}]

    if schema.get("prompt"):
        messages.append({"role": "system", "content": "Specific instructions for the code: " + schema.get("prompt")})

    code = self.env.completion(messages, temperature=0.1)
    self.env.add_system_log(f"Completion in tool_calls: {code}")

    try:
        if self.utils.is_code_block(code):
            code = code.replace("```python", "").replace("```", "")
            # Create a local dictionary to capture variables from exec
            local_dict = {}
            # Execute the code with the local dictionary
            exec(code, {}, local_dict)
            self.env.add_system_log(f"Local dict: {local_dict}")
            self.env.add_system_log(f"Local dict result: {local_dict.get('result')}")
            result = self.sanitize_schema_response(local_dict.get('result'))
            # Return the result - assuming the code creates a 'result' variable
            self.env.add_reply(json.dumps(result))
            return result
        else:
            raise ValueError("Invalid code")
    except Exception as e:
        print(f"Error executing code: {e}")
        self.env.add_reply(traceback.format_exc())
        return None