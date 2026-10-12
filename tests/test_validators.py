"""
Unit tests for Avsar input validators.
Tests edge cases, boundary lengths, language errors, and payload structures.
"""

import unittest
from validators import validate_analysis_request


class TestValidators(unittest.TestCase):

    def test_empty_payload(self):
        is_valid, err, sanitized = validate_analysis_request({})
        self.assertFalse(is_valid)
        self.assertIn("Notice text is required", err)
        self.assertIsNone(sanitized)

    def test_non_dict_payload(self):
        is_valid, err, sanitized = validate_analysis_request("string_payload")
        self.assertFalse(is_valid)
        self.assertIn("Expected a JSON object", err)

    def test_too_short_notice_english(self):
        is_valid, err, _ = validate_analysis_request({
            "notice_text": "Short notice",
            "category": "scholarship",
            "language": "en"
        })
        self.assertFalse(is_valid)
        self.assertIn("too short or incomplete", err)

    def test_too_short_notice_hindi(self):
        is_valid, err, _ = validate_analysis_request({
            "notice_text": "छोटा नोटिस",
            "category": "scholarship",
            "language": "hi"
        })
        self.assertFalse(is_valid)
        self.assertIn("बहुत छोटा या अधूरा है", err)

    def test_oversized_notice(self):
        is_valid, err, _ = validate_analysis_request({
            "notice_text": "A" * 20005,
            "category": "scholarship"
        })
        self.assertFalse(is_valid)
        self.assertIn("exceeds the maximum limit", err)

    def test_missing_category(self):
        is_valid, err, _ = validate_analysis_request({
            "notice_text": "This is a valid length notice announcing merit scholarships for class 10 students."
        })
        self.assertFalse(is_valid)
        self.assertIn("category is required", err)

    def test_invalid_category(self):
        is_valid, err, _ = validate_analysis_request({
            "notice_text": "This is a valid length notice announcing merit scholarships for class 10 students.",
            "category": "unknown_category"
        })
        self.assertFalse(is_valid)
        self.assertIn("Invalid category", err)

    def test_valid_payload_sanitization(self):
        payload = {
            "notice_text": "  National Scholarship Portal announces merit grant of Rs 10000 for secondary education.  ",
            "category": "scholarship",
            "language": "hi",
            "profile": {
                "education": "Class 10",
                "state": "Rajasthan"
            }
        }
        is_valid, err, sanitized = validate_analysis_request(payload)
        self.assertTrue(is_valid)
        self.assertIsNone(err)
        self.assertEqual(sanitized["notice_text"], payload["notice_text"].strip())
        self.assertEqual(sanitized["category"], "scholarship")
        self.assertEqual(sanitized["language"], "hi")
        self.assertEqual(sanitized["profile"]["education"], "Class 10")


if __name__ == '__main__':
    unittest.main()
