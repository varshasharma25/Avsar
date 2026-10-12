"""
Route and page integration tests for Avsar multi-page architecture.
Tests landing (/), home (/home), analyze (/analyze), results (/results),
error handlers (404), and session data flow.
"""

import unittest
from app import app, ANALYSIS_CACHE


class TestAvsarRoutes(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_endpoint(self):
        """GET /health returns 200 with service status."""
        res = self.app.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "healthy")

    def test_landing_page(self):
        """GET / serves the dedicated landing page with required headline & features."""
        res = self.app.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        # Check headline from requirements
        self.assertIn("Big opportunities. Clear next steps.", html)
        self.assertIn("Explore Opportunities", html)
        self.assertIn("How Avsar Works", html)
        self.assertIn("Supported Categories", html)
        self.assertIn("Built For Trust", html)
        self.assertIn("Privacy First", html)

    def test_home_dashboard(self):
        """GET /home serves the distinct home workspace dashboard."""
        res = self.app.get('/home')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Find your next opportunity", html)
        self.assertIn("Analyze a Notice Now", html)
        self.assertIn("Safety Tips for Opportunity Seekers", html)
        self.assertIn("Scholarship", html)
        self.assertIn("Government Scheme", html)

    def test_analyze_page(self):
        """GET /analyze serves the dedicated opportunity notice input workspace."""
        res = self.app.get('/analyze')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Decode Opportunity Notice", html)
        self.assertIn("Opportunity Notice Text", html)
        self.assertIn("0 / 20,000 chars", html)
        self.assertIn("Load Sample Notice", html)
        self.assertIn("Add Your Profile", html)

    def test_analyze_page_with_preselected_category(self):
        """GET /analyze?category=scholarship pre-selects the requested category."""
        res = self.app.get('/analyze?category=scholarship')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('value="scholarship" selected', html)

    def test_results_page_empty_state(self):
        """GET /results without active session analysis renders friendly empty state."""
        res = self.app.get('/results')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("No Active Opportunity Analyzed Yet", html)
        self.assertIn("Start a New Analysis", html)

    def test_results_page_with_session_data(self):
        """GET /results with analysis data in session renders full analysis UI."""
        with self.app as client:
            with client.session_transaction() as sess:
                sess["session_token"] = "test-token-123"
            
            # Populate mock analysis in the session store
            mock_analysis = {
                "title": "National Merit Scholarship 2026",
                "opportunity_type": "scholarship",
                "summary": "Financial grant of Rs 12000 per annum for class 9 students.",
                "eligibility": [
                    {
                        "criterion": "Regular student of Class 9",
                        "status": "matches",
                        "reason": "Profile states student is enrolled in Class 9.",
                        "evidence": "Candidate must be a regular student studying in Class 9.",
                        "label": "From notice"
                    }
                ],
                "benefits": [{"text": "Rs 12000 per annum", "label": "From notice"}],
                "deadlines": [{"text": "Registration closes", "date": "30 November 2026", "label": "From notice"}],
                "documents": [{"text": "Class 8 marksheet", "label": "From notice"}],
                "action_plan": [{"step": 1, "text": "Visit scholarships.gov.in and register online."}],
                "explicit_links": ["https://scholarships.gov.in"],
                "missing_info": ["Application fee details are not stated in notice."],
                "warnings": []
            }
            ANALYSIS_CACHE["test-token-123"] = {
                "analysis": mock_analysis,
                "language": "en",
                "timestamp": 123456789.0
            }

            res = client.get('/results')
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn("National Merit Scholarship 2026", html)
            self.assertIn("Regular student of Class 9", html)
            self.assertIn("Matches", html)
            self.assertIn("Candidate must be a regular student studying in Class 9.", html)
            self.assertIn("https://scholarships.gov.in", html)
            self.assertIn("Action Plan Checklist", html)

    def test_clear_results_redirects(self):
        """POST /clear-results clears session analysis and redirects to /analyze."""
        res = self.app.post('/clear-results')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/analyze', res.headers.get("Location", ""))

    def test_opportunities_page_and_category_filter(self):
        """GET /opportunities renders dedicated category guide with tabs and no form."""
        res = self.app.get('/opportunities?category=scholarship')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Explore Opportunity Categories", html)
        self.assertIn("Scholarships (छात्रवृत्ति)", html)
        self.assertIn("Government Schemes (सरकारी योजना)", html)
        # Verify analyze form is NOT present on opportunities page
        self.assertNotIn("textarea id=\"notice_text\"", html)

    def test_about_page_and_methodology(self):
        """GET /about renders dedicated mission, methodology, and verification disclaimer."""
        res = self.app.get('/about')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Making Opportunities Understandable for Everyone", html)
        self.assertIn("Why Do People Miss Legitimate Opportunities?", html)
        self.assertIn("How Evidence-Based Eligibility Works", html)
        self.assertIn("AI Limitations & Official Verification Notice", html)
        # Verify analyze form or full dashboard cards are NOT embedded here
        self.assertNotIn('id="notice-text"', html)

    def test_strict_page_isolation(self):
        """Verify each route renders only its dedicated view and does NOT merge other pages."""
        # 1. Landing (/) should NOT contain dashboard workspace banner or notice textarea
        res_landing = self.app.get('/')
        self.assertEqual(res_landing.status_code, 200)
        landing_html = res_landing.get_data(as_text=True)
        self.assertIn("Big opportunities. Clear next steps.", landing_html)
        self.assertNotIn("Opportunity Workspace", landing_html)
        self.assertNotIn('id="notice-text"', landing_html)

        # 2. Home (/home) should contain workspace dashboard but NOT landing hero title
        res_home = self.app.get('/home')
        self.assertEqual(res_home.status_code, 200)
        home_html = res_home.get_data(as_text=True)
        self.assertIn("Find your next opportunity", home_html)
        self.assertNotIn("Big opportunities.<br>Clear next steps.", home_html)
        self.assertNotIn('id="notice-text"', home_html)

        # 3. Analyze (/analyze) should contain notice input form but NOT category guide headers
        res_analyze = self.app.get('/analyze')
        self.assertEqual(res_analyze.status_code, 200)
        analyze_html = res_analyze.get_data(as_text=True)
        self.assertIn("Decode Opportunity Notice", analyze_html)
        self.assertIn('id="notice-text"', analyze_html)
        self.assertNotIn("Opportunity Discovery Guide", analyze_html)

    def test_contact_details_on_about_page(self):
        """GET /about renders professional contact details with Varsha Sharma and email."""
        res = self.app.get('/about')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Questions or Feedback?", html)
        self.assertIn("Have a question, suggestion, or feedback about Avsar? We'd love to hear from you.", html)
        self.assertIn("Varsha Sharma", html)
        self.assertIn("varsharma2710@gmail.com", html)
        self.assertIn('href="mailto:varsharma2710@gmail.com"', html)
        self.assertIn("Contact Us", html)

    def test_contact_link_in_footer(self):
        """Verify footer across pages includes compact Contact link."""
        res = self.app.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('/about#contact', html)
        self.assertIn('>Contact<', html)

    def test_landing_page_no_mock_floating_stage(self):
        """Verify the mock floating cards have been removed from the landing page hero."""
        res = self.app.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertNotIn('hero-visual-stage', html)
        self.assertNotIn('hero-float-card', html)

    def test_analyze_page_device_documents_and_upload_options(self):
        """GET /analyze includes clean documents section and notice file upload options."""
        res = self.app.get('/analyze')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Documents", html)
        self.assertIn("Add Documents", html)
        self.assertIn("Upload Notice (.pdf, .txt)", html)
        self.assertNotIn("Device-Only Privacy Guarantee", html)

    def test_extract_text_missing_file(self):
        """POST /api/extract-text without file returns 400."""
        res = self.app.post('/api/extract-text')
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("No file was attached", data.get("error", ""))

    def test_extract_text_from_txt_file(self):
        """POST /api/extract-text with valid text file extracts content in memory."""
        import io
        test_content = b"Scholarship announcement for Class 9 students. Benefit Rs 12000 per year."
        data = {
            'file': (io.BytesIO(test_content), 'test_notice.txt')
        }
        res = self.app.post('/api/extract-text', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        res_data = res.get_json()
        self.assertTrue(res_data.get("success"))
        self.assertIn("Scholarship announcement", res_data.get("text", ""))
        self.assertEqual(res_data.get("filename"), "test_notice.txt")


if __name__ == '__main__':
    unittest.main()

