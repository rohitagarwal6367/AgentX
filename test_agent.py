"""
test_agent.py
--------------
Run with: python -m unittest test_agent.py  (or just: python test_agent.py)
"""

import unittest
from agent import run_agent, clear_tool_log, get_tool_log


class TestAgent(unittest.TestCase):

    def setUp(self):
        clear_tool_log()

    def test_valid_order_status(self):
        reply = run_agent("Where is order ORD-1002?")
        self.assertIn("Out for Delivery", reply)
        self.assertIn("ORD-1002", reply)

    def test_invalid_order(self):
        reply = run_agent("What is the status of ORD-9999?")
        self.assertIn("couldn't find", reply.lower())

    def test_cheaper_alternative_chaining(self):
        reply = run_agent("Is there a cheaper alternative to the shoes in ORD-1001?")
        self.assertIn("cheaper", reply.lower())
        self.assertIn("Lite Sprint", reply)
        # confirm chaining actually happened: get_order -> get_product -> search_products
        tools_called = [entry["tool"] for entry in get_tool_log()]
        self.assertIn("get_order", tools_called)
        self.assertIn("search_products", tools_called)

    def test_valid_product_lookup(self):
        reply = run_agent("Tell me about PROD-201")
        self.assertIn("Wireless Bluetooth Headphones", reply)
        self.assertIn("2499", reply)

    def test_invalid_product_lookup(self):
        reply = run_agent("Tell me about PROD-999")
        self.assertIn("couldn't find", reply.lower())

    def test_general_search_with_results(self):
        reply = run_agent("Do you have any running shoes?")
        self.assertIn("Air Max", reply)

    def test_general_search_no_results_does_not_fabricate(self):
        reply = run_agent("Do you have any laptops?")
        self.assertIn("couldn't find", reply.lower())

    def test_empty_question(self):
        reply = run_agent("")
        self.assertTrue(len(reply) > 0)


if __name__ == "__main__":
    unittest.main()
