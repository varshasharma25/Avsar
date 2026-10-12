"""
Avsar — Opportunity, decoded.
Premium Multi-Page Web Application.

Routes:
  GET  /               -> Landing page (visual editorial hero & overview)
  GET  /home           -> Application workspace dashboard
  GET  /opportunities  -> Category exploration & discovery guide
  GET  /analyze        -> Opportunity notice analysis workspace
  POST /analyze        -> Process notice via Gemini API & store in session
  GET  /results        -> Dedicated analysis results page
  POST /clear-results  -> Clear current session analysis
  GET  /about          -> About Avsar, methodology & verification disclaimer
  GET  /health         -> Health check endpoint
  POST /api/test-gemini-> Test endpoint for verifying Gemini API
"""

import os
import time
import uuid
import logging
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from gemini_service import test_gemini_connection, analyze_opportunity_notice
from validators import validate_analysis_request

# ---------------------------------------------------------------------------
# Configuration & Setup
# ---------------------------------------------------------------------------

load_dotenv()

app = Flask(__name__)

# Secret key for secure session handling
app.secret_key = os.getenv("SECRET_KEY", "avsar-session-secret-key-cachyos-2026")

# Maximum upload limit (10 MB)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# In-memory store for analysis results to avoid ~4KB Flask client cookie limits
# Structure: token -> {"analysis": dict, "language": str, "timestamp": float}
ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}

# Simple in-memory rate limiter for expensive endpoints (POST /analyze, POST /api/extract-text)
# Structure: client_ip -> list of epoch timestamps
RATE_LIMIT_STORE: Dict[str, list] = {}
RATE_LIMIT_WINDOW = 60.0  # 1 minute window
RATE_LIMIT_MAX_REQUESTS = 12  # Max 12 requests per minute per IP

def is_rate_limited(client_ip: str) -> bool:
    """Checks whether the client IP has exceeded the allowed request frequency."""
    now = time.time()
    timestamps = RATE_LIMIT_STORE.get(client_ip, [])
    # Filter out requests older than the rolling window
    valid_timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(valid_timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        RATE_LIMIT_STORE[client_ip] = valid_timestamps
        return True
    valid_timestamps.append(now)
    RATE_LIMIT_STORE[client_ip] = valid_timestamps
    return False

# Gemini config fallback
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    app.logger.warning(
        "GEMINI_API_KEY is not set. Copy .env.example to .env and configure your key for analysis features."
    )

@app.after_request
def apply_security_headers(response):
    """Enforce defense-in-depth HTTP security response headers."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self';"
    )
    return response


# Category alias normalization mapping
CATEGORY_ALIASES = {
    "scholarship": "scholarship",
    "scholarships": "scholarship",
    "government_scheme": "government_scheme",
    "government-scheme": "government_scheme",
    "government-schemes": "government_scheme",
    "schemes": "government_scheme",
    "internship": "internship",
    "internships": "internship",
    "job": "job",
    "jobs": "job",
    "training": "training",
    "skill-development": "training",
    "skills": "training"
}


# ---------------------------------------------------------------------------
# Session Helper Utilities
# ---------------------------------------------------------------------------

def get_session_token() -> str:
    """Returns or generates a unique session token stored in client session cookie."""
    if "session_token" not in session:
        session["session_token"] = str(uuid.uuid4())
    return session["session_token"]


def set_session_analysis(analysis_data: Dict[str, Any], language: str = "en") -> None:
    """Safely stores analysis data in the server-side memory cache keyed by session token."""
    token = get_session_token()
    session["language"] = language
    ANALYSIS_CACHE[token] = {
        "analysis": analysis_data,
        "language": language,
        "timestamp": time.time()
    }


def get_session_analysis() -> Optional[Dict[str, Any]]:
    """Retrieves the analysis data associated with the current user session."""
    token = session.get("session_token")
    if token and token in ANALYSIS_CACHE:
        return ANALYSIS_CACHE[token].get("analysis")
    return None


def get_session_language() -> str:
    """Retrieves the active language preference (en or hi)."""
    token = session.get("session_token")
    if token and token in ANALYSIS_CACHE:
        return ANALYSIS_CACHE[token].get("language", session.get("language", "en"))
    return session.get("language", "en")


# ---------------------------------------------------------------------------
# Multi-Page Routes
# ---------------------------------------------------------------------------

@app.route("/")
def landing():
    """Page 1: Visual editorial landing page."""
    has_results = bool(get_session_analysis())
    return render_template(
        "landing.html",
        active_page="landing",
        has_active_results=has_results
    )


@app.route("/home")
def home_dashboard():
    """Page 2: Application dashboard and workspace."""
    has_results = bool(get_session_analysis())
    return render_template(
        "home.html",
        active_page="home",
        has_active_results=has_results
    )


@app.route("/opportunities")
def opportunities_page():
    """Page 3: Opportunity categories & discovery guide."""
    raw_category = request.args.get("category", "").strip().lower()
    selected_category = CATEGORY_ALIASES.get(raw_category, raw_category)
    has_results = bool(get_session_analysis())
    return render_template(
        "opportunities.html",
        active_page="opportunities",
        selected_category=selected_category,
        has_active_results=has_results
    )


@app.route("/analyze")
def analyze_page():
    """Page 4: Dedicated notice analysis form."""
    raw_category = request.args.get("category", "").strip().lower()
    selected_category = CATEGORY_ALIASES.get(raw_category, raw_category)
    has_results = bool(get_session_analysis())
    return render_template(
        "analyze.html",
        active_page="analyze",
        selected_category=selected_category,
        has_active_results=has_results
    )


@app.route("/results")
def results_page():
    """Page 5: Actual analysis results presentation."""
    analysis = get_session_analysis()
    lang = get_session_language()
    return render_template(
        "results.html",
        active_page="results",
        analysis=analysis,
        analysis_lang=lang,
        has_active_results=bool(analysis)
    )


@app.route("/about")
def about_page():
    """Page 6: About Avsar, methodology, and verification disclaimer."""
    has_results = bool(get_session_analysis())
    return render_template(
        "about.html",
        active_page="about",
        has_active_results=has_results
    )


@app.route("/clear-results", methods=["POST"])
def clear_results():
    """Clears the session analysis and redirects to the analyze page."""
    token = session.get("session_token")
    if token and token in ANALYSIS_CACHE:
        del ANALYSIS_CACHE[token]
    return redirect(url_for("analyze_page"))


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.route("/analyze", methods=["POST"])
def analyze_endpoint():
    """
    Core analysis endpoint: Accepts JSON notice payload, analyzes using Gemini,
    stores result in server session cache, and returns redirect directive.
    """
    client_ip = request.remote_addr or "127.0.0.1"
    if is_rate_limited(client_ip):
        return jsonify({
            "error": "Too many requests. Please wait a moment before submitting another notice."
        }), 429

    if not request.is_json:
        return jsonify({"error": "Request body must be valid JSON with 'Content-Type: application/json'."}), 400

    raw_data = request.get_json(silent=True)
    is_valid, validation_error, sanitized = validate_analysis_request(raw_data)
    if not is_valid:
        return jsonify({"error": validation_error}), 400

    # Call Gemini opportunity analyzer
    result, err, status_code = analyze_opportunity_notice(
        notice_text=sanitized["notice_text"],
        category=sanitized["category"],
        language=sanitized["language"],
        profile=sanitized["profile"]
    )

    if err:
        return jsonify({"error": err}), status_code

    # Store analysis in session-backed cache for the /results page
    set_session_analysis(result, language=sanitized["language"])

    return jsonify({
        "success": True,
        "redirect": url_for("results_page"),
        "data": result
    }), 200


@app.route("/api/extract-text", methods=["POST"])
def extract_text_endpoint():
    """
    Extracts text from an uploaded notice file (.txt, .md, .pdf) ephemerally in-memory.
    Privacy Guarantee: File is never written to disk or database; processed in memory and discarded.
    """
    client_ip = request.remote_addr or "127.0.0.1"
    if is_rate_limited(client_ip):
        return jsonify({
            "error": "Too many requests. Please wait a moment before uploading another file."
        }), 429

    if "file" not in request.files:
        return jsonify({"error": "No file was attached in the request."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Selected file has an empty filename."}), 400

    filename = file.filename.lower()
    file_bytes = file.read()

    # Limit to 10 MB
    if len(file_bytes) > 10 * 1024 * 1024:
        return jsonify({"error": "File exceeds the 10 MB size limit."}), 400

    if filename.endswith(".pdf"):
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            extracted = "\n\n".join(text_parts).strip()
            if not extracted:
                return jsonify({
                    "error": "Could not extract readable text from this PDF. It may consist of scanned images rather than selectable text."
                }), 400
            return jsonify({
                "success": True,
                "text": extracted[:20000],
                "filename": file.filename,
                "character_count": len(extracted)
            }), 200
        except Exception as e:
            app.logger.warning("PDF extraction failed: %s", str(e))
            return jsonify({"error": "Could not parse PDF. The file may be corrupt or encrypted."}), 400

    elif filename.endswith((".txt", ".md", ".csv", ".json", ".rtf")):
        try:
            text = file_bytes.decode("utf-8", errors="replace").strip()
            if not text:
                return jsonify({"error": "The selected text file is empty."}), 400
            return jsonify({
                "success": True,
                "text": text[:20000],
                "filename": file.filename,
                "character_count": len(text)
            }), 200
        except Exception as e:
            app.logger.warning("Text file decoding failed: %s", str(e))
            return jsonify({"error": "Failed to decode text file."}), 400
    else:
        return jsonify({"error": "Unsupported file format. Please choose a .pdf, .txt, or .md file."}), 400


@app.route("/health", methods=["GET"])
def health_check():
    """Confirm Flask server and environment status."""
    return jsonify({
        "status": "healthy",
        "service": "avsar-backend",
        "configured_model": os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        "api_key_configured": bool(os.getenv("GEMINI_API_KEY"))
    }), 200


@app.route("/api/test-gemini", methods=["POST"])
def test_gemini_endpoint():
    """Test endpoint for verifying Gemini API connectivity."""
    if not request.is_json:
        return jsonify({"error": "Request body must be valid JSON with 'Content-Type: application/json'."}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON format. Expected an object."}), 400

    message = data.get("message")
    if message is None or not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Field 'message' is required and must be a non-empty string."}), 400

    if len(message) > 500:
        return jsonify({"error": "Test message exceeds maximum length of 500 characters."}), 400

    output_text, error_message, status_code = test_gemini_connection(message)

    if error_message:
        return jsonify({"error": error_message}), status_code

    return jsonify({
        "response": output_text
    }), 200


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle uploads exceeding MAX_CONTENT_LENGTH."""
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({"error": "The uploaded payload exceeds the maximum 10 MB limit."}), 413
    return render_template("500.html", error_message="Uploaded payload is too large."), 413


@app.errorhandler(404)
def not_found_error(error):
    """Custom accessible 404 page."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Custom accessible 500 page."""
    return render_template("500.html"), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=debug_mode, port=port)
