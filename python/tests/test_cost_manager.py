import unittest
from python.cost_manager import CostManager, MODEL_PRICING_TABLE


class TestCostManager(unittest.TestCase):
    def setUp(self):
        self.cm = CostManager(budget_usd=0.10)

    def test_token_estimation(self):
        empty_count = self.cm.estimate_tokens("")
        self.assertEqual(empty_count, 0)

        short_count = self.cm.estimate_tokens("Hello world")
        self.assertGreaterEqual(short_count, 2)

    def test_cost_calculation(self):
        # 1,000 prompt tokens and 1,000 completion tokens on gpt-4o-mini
        # prompt: (1000 / 1M) * 0.15 = 0.00015
        # comp: (1000 / 1M) * 0.60 = 0.00060
        # total: 0.00075
        cost = self.cm.calculate_turn_cost("gpt-4o-mini", 1000, 1000)
        self.assertAlmostEqual(cost, 0.00075, places=5)

    def test_budget_threshold_detection(self):
        self.assertFalse(self.cm.is_budget_exceeded())

        # Simulate massive usage that exceeds $0.10 budget
        self.cm.record_usage("gpt-4o", 50000, 50000)
        self.assertTrue(self.cm.is_budget_exceeded())

        report = self.cm.get_summary_report()
        self.assertTrue(report["budget_exceeded"])
        self.assertEqual(report["total_turns"], 1)


if __name__ == "__main__":
    unittest.main()
