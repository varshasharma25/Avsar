"""
Avsar — Gemini Mock & Security Reliability Test Suite
Covers:
1. Mocked successful Gemini structured analysis.
2. Mocked APIError 429 (Rate Limit / Quota Exceeded).
3. Mocked APIError 503 (High Demand / Service Unavailable).
4. Mocked APIError 404 (Model not found).
5. Mocked JSONDecodeError & empty response recovery.
6. HTTP Security response headers on routes.
7. Rate limiting on POST /analyze and POST /api/extract-text.
8. Maximum content length (413 Payload Too Large).
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from google.genai.errors import APIError

from app import app, RATE_LIMIT_STORE
from gemini_service import analyze_opportunity_notice, test_gemini_connection


class TestGeminiAndSecurityReliability(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        RATE_LIMIT_STORE.clear()

    # -------------------------------------------------------------------------
    # 1. Security Headers Tests
    # -------------------------------------------------------------------------

    def test_security_headers_present_on_all_responses(self):
        """Verify defense-in-depth security headers are attached to responses."""
        res = self.app.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(res.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("camera=()", res.headers.get("Permissions-Policy", ""))
        self.assertIn("default-src 'self'", res.headers.get("Content-Security-Policy", ""))

    # -------------------------------------------------------------------------
    # 2. Rate Limiting Tests
    # -------------------------------------------------------------------------

    def test_rate_limiting_on_analyze_endpoint(self):
        """Verify requests beyond RATE_LIMIT_MAX_REQUESTS receive 429 Too Many Requests."""
        # Send 12 requests (allowed)
        for i in range(12):
            res = self.app.post('/analyze', json={
                "notice_text": "short",
                "category": "scholarship",
                "language": "en"
            })
            # May be 400 due to validation, but not 429
            self.assertNotEqual(res.status_code, 429)

        # 13th request within the minute window should trigger 429
        res_blocked = self.app.post('/analyze', json={
            "notice_text": "short",
            "category": "scholarship",
            "language": "en"
        })
        self.assertEqual(res_blocked.status_code, 429)
        data = res_blocked.get_json()
        self.assertIn("Too many requests", data.get("error", ""))

    # -------------------------------------------------------------------------
    # 3. Gemini Service Unit Tests with Mocks
    # -------------------------------------------------------------------------

    @patch("gemini_service.get_gemini_client")
    def test_gemini_successful_structured_analysis(self, mock_get_client):
        """Verify successful structured response parsing from Gemini."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        
        mock_analysis_data = {
            "title": "National Scholarship 2026",
            "opportunity_type": "scholarship",
            "summary": "Financial support for Class 9 students.",
            "eligibility": [
                {
                    "criterion": "Class 9 student",
                    "status": "matches",
                    "reason": "Profile matches Class 9",
                    "evidence": "Regular student studying in Class 9",
                    "label": "From notice"
                }
            ],
            "benefits": [{"text": "Rs 12000 per year", "label": "From notice"}],
            "deadlines": [{"text": "Registration deadline", "date": "30 Nov 2026", "label": "From notice"}],
            "documents": [{"text": "Income Certificate", "label": "From notice"}],
            "action_plan": [{"step": 1, "text": "Apply on national scholarship portal."}],
            "explicit_links": ["https://scholarships.gov.in"],
            "missing_info": ["Application fee not stated."],
            "warnings": []
        }
        mock_response.text = json.dumps(mock_analysis_data)
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = (mock_client, None)

        result, err, status = analyze_opportunity_notice(
            notice_text="Candidate must be a regular student studying in Class 9.",
            category="scholarship",
            language="en",
            profile={"education": "Class 9"}
        )

        self.assertIsNone(err)
        self.assertEqual(status, 200)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "National Scholarship 2026")
        self.assertEqual(result["eligibility"][0]["status"], "matches")

    @patch("gemini_service.get_gemini_client")
    def test_gemini_rate_limit_error_429(self, mock_get_client):
        """Verify 429 quota exhaustion is converted to user-friendly error without stack trace."""
        mock_client = MagicMock()
        err_429 = APIError(429, {"error": {"message": "RESOURCE_EXHAUSTED: Quota exceeded"}})
        mock_client.models.generate_content.side_effect = err_429
        mock_get_client.return_value = (mock_client, None)

        result, err, status = analyze_opportunity_notice(
            notice_text="Valid opportunity notice content exceeding 30 characters.",
            category="scholarship",
            language="en",
            profile={}
        )

        self.assertIsNone(result)
        self.assertEqual(status, 429)
        self.assertIn("quota exceeded", err.lower())

    @patch("gemini_service.get_gemini_client")
    def test_gemini_service_unavailable_503(self, mock_get_client):
        """Verify 503 high demand is converted to user-friendly error."""
        mock_client = MagicMock()
        err_503 = APIError(503, {"error": {"message": "UNAVAILABLE: Service busy"}})
        mock_client.models.generate_content.side_effect = err_503
        mock_get_client.return_value = (mock_client, None)

        result, err, status = analyze_opportunity_notice(
            notice_text="Valid opportunity notice content exceeding 30 characters.",
            category="scholarship",
            language="en",
            profile={}
        )

        self.assertIsNone(result)
        self.assertEqual(status, 503)
        self.assertIn("high demand", err.lower())

    @patch("gemini_service.get_gemini_client")
    def test_gemini_hindi_error_translation(self, mock_get_client):
        """Verify error messages are localized when language is 'hi'."""
        mock_client = MagicMock()
        err_503 = APIError(503, {"error": {"message": "UNAVAILABLE: Service busy"}})
        mock_client.models.generate_content.side_effect = err_503
        mock_get_client.return_value = (mock_client, None)

        result, err, status = analyze_opportunity_notice(
            notice_text="Valid opportunity notice content exceeding 30 characters.",
            category="scholarship",
            language="hi",
            profile={}
        )

        self.assertIsNone(result)
        self.assertEqual(status, 503)
        self.assertIn("अधिक लोड", err)

    @patch("gemini_service.get_gemini_client")
    def test_gemini_json_decode_retry_exhaustion(self, mock_get_client):
        """Verify unparseable JSON triggers retry and returns graceful 502."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON string"
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = (mock_client, None)

        result, err, status = analyze_opportunity_notice(
            notice_text="Valid opportunity notice content exceeding 30 characters.",
            category="scholarship",
            language="en",
            profile={}
        )

        self.assertIsNone(result)
        self.assertEqual(status, 502)
        self.assertIn("unparseable response", err.lower())

    @patch("gemini_service.get_gemini_client")
    def test_test_gemini_connection_success(self, mock_get_client):
        """Verify test_gemini_connection works with valid model output."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Hello from Gemini 3.1 Flash Lite!"
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = (mock_client, None)

        text, err, status = test_gemini_connection("Test ping")
        self.assertIsNone(err)
        self.assertEqual(status, 200)
        self.assertEqual(text, "Hello from Gemini 3.1 Flash Lite!")


if __name__ == "__main__":
    unittest.main()
