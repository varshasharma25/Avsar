"""
Avsar — Input Validation Module
Validates incoming payload size, required parameters, and types.
Provides bilingual error messages and safeguards against unreadable or underspecified inputs.
"""

from typing import Tuple, Optional, Dict, Any

VALID_CATEGORIES = {
    "scholarship",
    "government_scheme",
    "job",
    "internship",
    "training"
}

VALID_LANGUAGES = {"en", "hi"}
MIN_NOTICE_LENGTH = 30     # Notices shorter than ~6 words are too short/unreadable
MAX_NOTICE_LENGTH = 20000  # ~3,000 words


def validate_analysis_request(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates the POST /analyze JSON payload.
    Returns (is_valid, error_message, sanitized_data).
    """
    if not isinstance(data, dict):
        return False, "Invalid payload. Expected a JSON object.", None

    language = data.get("language", "en")
    if not isinstance(language, str) or language.strip().lower() not in VALID_LANGUAGES:
        language = "en"
    else:
        language = language.strip().lower()

    is_hindi = (language == "hi")

    notice_text = data.get("notice_text")
    if not notice_text or not isinstance(notice_text, str) or not notice_text.strip():
        msg = "सूचना का विवरण आवश्यक है और यह खाली नहीं हो सकता।" if is_hindi else "Notice text is required and cannot be empty."
        return False, msg, None

    cleaned_text = notice_text.strip()
    if len(cleaned_text) < MIN_NOTICE_LENGTH:
        msg = (
            "प्रदान किया गया नोटिस विवरण बहुत छोटा या अधूरा है। सटीक विश्लेषण के लिए कृपया पात्रता, लाभ या प्रक्रिया का अधिक विवरण साझा करें।"
            if is_hindi else
            "The provided notice text is too short or incomplete to analyze reliably. Please provide more complete details including eligibility or benefits."
        )
        return False, msg, None

    if len(cleaned_text) > MAX_NOTICE_LENGTH:
        msg = (
            f"सूचना का पाठ अधिकतम सीमा {MAX_NOTICE_LENGTH:,} अक्षरों से अधिक है।"
            if is_hindi else
            f"Notice text exceeds the maximum limit of {MAX_NOTICE_LENGTH:,} characters."
        )
        return False, msg, None

    category = data.get("category", "")
    if not isinstance(category, str) or not category.strip():
        msg = "अवसर की श्रेणी चुनना अनिवार्य है।" if is_hindi else "Opportunity category is required."
        return False, msg, None

    category = category.strip().lower()
    if category not in VALID_CATEGORIES:
        allowed = ", ".join(sorted(VALID_CATEGORIES))
        msg = (
            f"अमान्य श्रेणी '{category}'। कृपया इनमें से चुनें: {allowed}।"
            if is_hindi else
            f"Invalid category '{category}'. Must be one of: {allowed}."
        )
        return False, msg, None

    raw_profile = data.get("profile", {})
    sanitized_profile = {}
    if isinstance(raw_profile, dict):
        for k, v in raw_profile.items():
            if isinstance(v, str):
                # Clean and cap profile field lengths
                sanitized_profile[k] = v.strip()[:300]

    return True, None, {
        "notice_text": cleaned_text,
        "category": category,
        "language": language,
        "profile": sanitized_profile
    }
