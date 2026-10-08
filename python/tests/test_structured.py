import unittest
from python.structured_outputs import (
    StructuredOutputParser,
    CodeReviewSchema,
    ActionPlanSchema,
)


class TestStructuredOutputs(unittest.TestCase):
    def test_extract_json_from_markdown_fences(self):
        fenced_payload = """
Here is your requested analysis:
```json
{
  "language": "python",
  "quality_score": 95,
  "summary": "Clean code",
  "issues_found": [],
  "optimizations": ["Add docstring"]
}
```
Hope this helps!
"""
        extracted = StructuredOutputParser.extract_json_string(fenced_payload)
        self.assertTrue(extracted.startswith("{"))
        self.assertTrue(extracted.endswith("}"))

    def test_validate_code_review_schema(self):
        sample = """
        {
          "language": "javascript",
          "quality_score": 88,
          "summary": "Solid async implementation",
          "issues_found": [
            {
              "severity": "Medium",
              "description": "Missing try/catch in fetch",
              "fix_suggestion": "Wrap in try-catch block"
            }
          ],
          "optimizations": ["Use const instead of let"]
        }
        """
        model = StructuredOutputParser.validate_schema(sample, CodeReviewSchema)
        self.assertEqual(model.language, "javascript")
        self.assertEqual(model.quality_score, 88)
        self.assertEqual(len(model.issues_found), 1)

    def test_self_healing_trailing_commas(self):
        malformed_json = '{"language": "python", "quality_score": 90, "summary": "Test", "issues_found": [], "optimizations": [], }'
        parsed = StructuredOutputParser.parse_json(malformed_json)
        self.assertEqual(parsed["language"], "python")


if __name__ == "__main__":
    unittest.main()
