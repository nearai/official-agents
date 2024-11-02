# mock user preferences
def get_preferences(account_id: str):
    return {
        "account_id": account_id,
        "preferences": {
            "language": "British English",
            "timezone": "America/Los_Angeles",
            "favorite_color": "dark purple",
            "activities": ["reading", "windsurfing", "baking"],
            "favorite_food": "sushi",
            "things_i_love": ["anime", "cats", "coffee"],
        },
        "personal_information":
            """I always find it hard to shop for birthday gifts. In particular:
            - I like to buy gifts that the recipient will find useful.
            My uncle Juan's birthday is November 28th, he's like 50 or so.
            My niece Amelie's birthday is December 3rd, she's 10 I think.
            """
    }