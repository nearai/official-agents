from unittest import TestCase

from shopper.agent.agent import Agent



class TestAgent(TestCase):

    def setUp(self):
        global env
        env = {"env_vars": {}}

    def test_text_is_not_order(self):
        test_user_message = "I would like to order a shirt"
        self.assertFalse(Agent.is_order(test_user_message))

    def test_json_order(self):
        test_user_message = (
            '{"order":{"size":"L","name":"Jane Smith","address1":"123 Main St","address2":"","city":"Anytown","state":"CA","zip":"90210","country":"US","color":"heather"}}'
            # '{"order": {"size": "M", "color": "aqua", "name": "John Doe", "address1": "123 Main St", "city": "Anytown", "state": "CA", "country": "USA", "zip": "90210"}}'
        )
        self.assertTrue(Agent.is_order(test_user_message))

