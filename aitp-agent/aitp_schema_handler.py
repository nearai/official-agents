import json
import requests
import traceback
import asyncio

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
    max_retries = 3
    retry_count = 0
    previous_errors = []

    while retry_count < max_retries:
        try:
            json_schema = None
            schema_url = None
            if schema.get("url"):
                schema_url = schema.get("url")
                self.env.add_system_log(f"Fetching schema from URL: {schema_url}")
                json_schema = self.fetch_schema_from_url(schema_url)
            elif schema.get("$schema"):
                json_schema = schema
            else:
                raise ValueError("No schema found")

            self.env.add_system_log(f"Schema: {json_schema}")

            if not json_schema:
                self.env.add_system_log("No schema found on the provided URL")
                return None

            error_guidance = ""
            if previous_errors:
                error_guidance = "\n\nPrevious attempts failed with these errors. Please avoid them:\n"
                for i, error in enumerate(previous_errors, 1):
                    error_guidance += f"{i}. {error}\n"

            messages = [{"role": "system", "content": f"""You are a developer. You are given a schema and a content. Your task is to fill the schema with the content provided by the user.
                        The output must be a code that returns a 'result' variable containing the final output. Do not include any other text since the code block will be executed programmatically.
                        - The $schema property must be respected. It should be the first line of the 'result' output and it should be '{schema_url}'.
                        - The code must be in Python.
                        - Do not use fake data, you have the information provided by the user
                        - Return the result in a 'result' variable pure dict, don't run json.loads or json.dumps on it
                        - The code must start with exactly '```python' and end with exactly '```'
                        - Make sure the result variable is properly defined before the code ends
                        - Do not use any try/except blocks in your generated code
                        - Keep the code simple and straightforward
                        - Make sure all dictionary keys are strings
                        - Ensure all values match the schema types

                        **The code runs in an isolated environment, make sure the code is self-contained and valid**
                        - DO NOT USE ANY EXTERNAL LIBRARIES AND BE CAREFUL WITH THE IMPORTS
                        - DO NOT TRY TO ACCESS VARIABLES OUTSIDE THE CODE BLOCK

                        Attempt #{retry_count + 1} of {max_retries}{error_guidance}
                        """},
                {"role": "user", "content": f"""
                ## Content: {str(data)}
                ## Schema: {json_schema}
                """}]

            if schema.get("prompt"):
                messages.append({"role": "system", "content": "Specific instructions for the code: " + schema.get("prompt")})

            code = self.env.completion(messages, temperature=max(0.1, 0.1 * retry_count))
            self.env.add_system_log(f"Completion in tool_calls (attempt {retry_count + 1}): {code}")

            if self.utils.is_code_block(code):
                code = code.replace("```python", "").replace("```", "")
                local_dict = {}
                exec(code, {}, local_dict)

                if 'result' not in local_dict:
                    raise ValueError("Code execution did not produce a 'result' variable")

                self.env.add_system_log(f"Local dict: {local_dict}")
                self.env.add_system_log(f"Local dict result: {local_dict.get('result')}")
                result = self.sanitize_schema_response(local_dict.get('result'))

                self.env.add_reply(json.dumps(result))
                return result
            else:
                raise ValueError("Invalid code block format")

        except Exception as e:
            error_msg = f"Error in attempt {retry_count + 1}: {str(e)}"
            previous_errors.append(error_msg)
            self.env.add_system_log(f"{error_msg}\n{traceback.format_exc()}")

            retry_count += 1
            if retry_count >= max_retries:
                self.env.add_reply(f"Failed after {max_retries} attempts. Last error: {error_msg}")
                return None

            await asyncio.sleep(1)
            continue