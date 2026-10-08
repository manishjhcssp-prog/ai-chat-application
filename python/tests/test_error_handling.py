import unittest
from python.error_handler import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMConnectionError,
    retry_with_backoff,
    classify_api_exception,
)


class TestErrorHandling(unittest.TestCase):
    def test_exception_classification(self):
        auth_err = classify_api_exception(Exception("401 Unauthorized: Invalid API key"))
        self.assertIsInstance(auth_err, LLMAuthenticationError)

        rate_err = classify_api_exception(Exception("429 Too Many Requests: Rate limit reached"))
        self.assertIsInstance(rate_err, LLMRateLimitError)

        conn_err = classify_api_exception(Exception("Connection timeout after 30000ms"))
        self.assertIsInstance(conn_err, LLMConnectionError)

    def test_retry_decorator_success_after_failure(self):
        attempts = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01, jitter=False)
        def flaky_service():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise LLMRateLimitError("Transient 429")
            return "SUCCESS"

        result = flaky_service()
        self.assertEqual(result, "SUCCESS")
        self.assertEqual(attempts, 2)

    def test_retry_exhaustion_raises(self):
        @retry_with_backoff(max_retries=2, initial_delay=0.01, jitter=False)
        def always_failing():
            raise LLMRateLimitError("Permanent 429")

        with self.assertRaises(LLMRateLimitError):
            always_failing()


if __name__ == "__main__":
    unittest.main()
