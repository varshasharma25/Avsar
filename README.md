# Avsar (अवसर) — Opportunity, decoded.

Avsar transforms long, confusing opportunity notices (scholarships, government schemes, internships, jobs, and training programs) into plain-language explanations and step-by-step application plans in English or Hindi.

---

## 📌 Architecture & Multi-Page Experience

Avsar is built as a multi-page web application:

1. **Landing Page (`/`)**:
   - Public-facing first impression with the headline *"Big opportunities. Clear next steps."*
   - Supported opportunity categories and feature cards.
   - Interactive 3-step *"How Avsar Works"* process walkthrough.
   - Transparent notice processing and educational guidance notes.

2. **Home Dashboard (`/home`)**:
   - Central application workspace (*"Find your next opportunity"*).
   - Opportunity category shortcuts for Scholarships, Government Schemes, Internships, Jobs, and Training.
   - Quick guidance on getting started and essential safety tips against scams.
   - Session-aware indicator for active analysis results.

3. **Notice Analyzer (`/analyze`)**:
   - Dedicated analysis workspace with 20,000-character input validation and live counter.
   - Category selector and English / Hindi language toggle.
   - Optional profile fields for personalized eligibility evaluation.
   - Sample notice loader for testing and accessible error handling.

4. **Analysis Results (`/results`)**:
   - Dedicated results view rendering structured title, summary, and category badge.
   - Evidence-based eligibility comparison with verbatim quoted excerpts from the notice.
   - Benefits, deadlines, required documents, and interactive action checklist.
   - Explicit links found in the notice and practical scam warnings.
   - Friendly empty state when no analysis is active in the current session.

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, Jinja2 Templates, CSS3 (Modular Tokens), Vanilla JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons
- **Backend**: Python 3.10+, Flask (Multi-Page Routing & Secure Session Handling)
- **AI / LLM**: Google Gemini API via official `google-genai` SDK (`gemini-3.1-flash-lite`)
- **Validation & Environment**: `python-dotenv`, Pydantic Schema, custom bilingual validators

---

## 📁 Project Structure

```
avsar/
├── app.py                      # Flask multi-page routing, session cache & error handlers
├── gemini_service.py           # Google Gemini API integration (google-genai SDK)
├── prompt_builder.py           # Bilingual structured prompt engineering
├── schema.py                   # Pydantic schema for structured output
├── validators.py               # Input validation & localized error messages
├── requirements.txt            # Python dependencies
├── .env                        # Private environment variables (excluded from Git)
├── .env.example                # Configuration template
├── templates/
│   ├── base.html               # Shared skeleton layout (landmarks, skip link, nav, footer)
│   ├── landing.html            # Public landing page (/)
│   ├── home.html               # Home dashboard (/home)
│   ├── analyze.html            # Notice input workspace (/analyze)
│   ├── results.html            # Dedicated analysis results (/results)
│   ├── 404.html                # Custom accessible 404 error page
│   ├── 500.html                # Custom accessible 500 error page
│   └── components/
│       ├── navbar.html         # Reusable navigation bar
│       ├── footer.html         # Reusable footer with disclaimer
│       ├── flash_messages.html # Flash alert notifications
│       ├── opportunity_card.html# Reusable category card macro
│       ├── eligibility_item.html# Reusable eligibility & evidence macro
│       └── safety_warning.html # Reusable safety alert macro
├── static/
│   ├── css/
│   │   ├── design-system.css   # Color palette tokens, sage & lime gradients, typography
│   │   ├── base.css            # Resets, navbar, footer, buttons
│   │   ├── components.css      # Badges, trust labels, quotes, checklists
│   │   ├── landing.css         # Hero diagram & landing styles
│   │   ├── home.css            # Dashboard banners & card layouts
│   │   ├── analyze.css         # Form controls, char counter, profile accordion
│   │   ├── results.css         # Results view & print media queries
│   │   └── responsive.css      # Mobile (320px–430px) & tablet breakpoints
│   └── js/
│       ├── base.js             # Global utilities & mobile navigation
│       ├── landing.js          # Smooth anchor scrolling
│       ├── home.js             # Dashboard category shortcuts
│       ├── analyze.js          # Form validation, device documents locker, in-memory PDF extractor
│       └── results.js          # Interactive checklist & copy-to-clipboard
└── tests/
    ├── __init__.py
    ├── test_routes.py          # Route & page integration tests
    ├── test_validators.py      # Boundary & bilingual validator unit tests
    └── test_gemini_reliability.py # Mocked Gemini tests, rate limiting & security headers
```

---

## 🔒 Reliability & Security Features

- **Strict HTTP Security Headers**: Defense-in-depth headers applied to every response (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, `Content-Security-Policy`).
- **In-Memory Rate Limiting**: Built-in sliding-window limiter on heavy POST endpoints (`/analyze`, `/api/extract-text`) preventing quota exhaustion and abusive rapid-fire requests.
- **Privacy by Architecture**: Zero database footprint. Notice circulars and profiles are processed strictly in-memory during request execution and discarded. Personal documents in the Documents Locker reside 100% inside client-side `localStorage`.
- **Server Upload Safeguards**: Hard `MAX_CONTENT_LENGTH` enforcement (10 MB) returning graceful 413 responses.
- **Resilient AI Error Mapping**: Structured error handling for Gemini API rate limits (429), server load (503), model missing (404), and corrupted JSON with automatic retries and localized Hindi translations without exposing tracebacks.

---

## 🚀 Getting Started on CachyOS / Linux

### 1. Set Up Environment

```bash
cd /home/varsha/Desktop/avsar
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy `.env.example` to `.env` and configure your Gemini API key:
```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
SECRET_KEY=your_session_secret_key
FLASK_DEBUG=false
```

### 3. Run Automated Tests

The test suite runs 100% offline using mock objects for Gemini:
```bash
.venv/bin/python -m unittest discover tests
```

### 4. Start the Application

```bash
.venv/bin/python app.py
```

Access Avsar at `http://127.0.0.1:5000` in any web browser.
