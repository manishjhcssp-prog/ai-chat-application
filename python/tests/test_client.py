import unittest
from python.config import AppConfig
from python.cost_manager import CostManager
from python.client import UnifiedLLMClient
from python.error_handler import LLMRateLimitError


class TestClient(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig(
            default_model="mock-llm",
            session_budget_usd=1.0,
        )
        self.cost_manager = CostManager(budget_usd=1.0)
        self.client = UnifiedLLMClient(config=self.config, cost_manager=self.cost_manager)

    def test_mock_client_response_generation(self):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how do tokens work?"},
        ]
        resp = self.client.call_api(messages)
        self.assertTrue(len(resp.content) > 10)
        self.assertGreater(resp.prompt_tokens, 0)
        self.assertGreater(resp.completion_tokens, 0)
        self.assertEqual(resp.model, "mock-llm")
        self.assertEqual(len(self.cost_manager.records), 1)

    def test_budget_exceeded_blocking(self):
        tiny_cost = CostManager(budget_usd=0.000001)
        tiny_cost.record_usage("gpt-4o", 1000, 1000)
        client = UnifiedLLMClient(config=self.config, cost_manager=tiny_cost)

        with self.assertRaises(LLMRateLimitError):
            client.call_api([{"role": "user", "content": "Test"}])


if __name__ == "__main__":
    unittest.main()
