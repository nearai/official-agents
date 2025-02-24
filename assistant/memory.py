from nearai.agents.environment import Environment

REMEMBER_PROMPT = """
You are an expert at deciding if parts of a message should be remembered in the user's memory.

**Instructions:**

- If parts of the message are relevant, respond with **ONLY** the parts that should be remembered.
- If none of the message is relevant, respond with an empty string.
- **Do not** include any additional text, explanations, or greetings.

**Example Responses:**

- If relevant parts: 
    - ["The meeting is at 3 PM."]
    - ["User's preference for email communication", "User likes bikes"]
    - ["Important deadline mentioned"]
    - ["Request for follow-up meeting"]
    - ["Interest in specific product"]
    - ["Feedback on service quality"]
    - ["User's prefers the color red", "User's dog is called Rex"]

- If no relevant parts: []
"""


def to_remember(message: str, env: Environment):
    """Determines if parts of the message should be remembered."""
    res = env.completion(
        [
            {"role": "system", "content": REMEMBER_PROMPT},
            {"role": "user", "content": message},
        ]
    ).strip()
    print("res in to_remember", res)
    if res == "" or res == '""' or res == "[]":
        return None
    return res


