import unittest
from python.config import AppConfig


class TestAppConfig(unittest.TestCase):
    def test_default_config_validation(self):
        config = AppConfig()
        config.validate()
        self.assertEqual(config.default_model, "gpt-4o-mini")
        self.assertEqual(config.default_temperature, 0.7)
        self.assertEqual(config.default_max_tokens, 1024)

    def test_invalid_temperature_raises(self):
        config = AppConfig(default_temperature=2.5)
        with self.assertRaises(ValueError):
            config.validate()

    def test_invalid_max_tokens_raises(self):
        config = AppConfig(default_max_tokens=-10)
        with self.assertRaises(ValueError):
            config.validate()

    def test_provider_resolution(self):
        sim_config = AppConfig()
        self.assertEqual(sim_config.get_active_provider(), "simulation")

        openai_config = AppConfig(openai_api_key="sk-test-key", default_model="gpt-4o")
        self.assertEqual(openai_config.get_active_provider(), "openai")

        gemini_config = AppConfig(gemini_api_key="AIzaSyTest", default_model="gemini-1.5-flash")
        self.assertEqual(gemini_config.get_active_provider(), "gemini")


if __name__ == "__main__":
    unittest.main()
