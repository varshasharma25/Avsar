"""
Avsar — Opportunity Analysis Schema
Defines the Pydantic and JSON Schema specification for Gemini structured responses,
including evidence-based safety warnings and missing information.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class BenefitItem(BaseModel):
    text: str = Field(description="Description of the benefit or assistance offered in the requested language")
    label: str = Field(default="from_notice", description="Trust label: 'from_notice' or 'inferred'")


class DeadlineItem(BaseModel):
    text: str = Field(description="Description of key date or deadline in the requested language")
    date: Optional[str] = Field(default=None, description="ISO date YYYY-MM-DD if explicitly present, else null")
    label: str = Field(default="from_notice", description="Trust label: 'from_notice'")


class EligibilityItem(BaseModel):
    criterion: str = Field(description="Stated requirement or criterion translated to requested language")
    evidence: str = Field(description="EXACT verbatim excerpt quoted from the original notice text in its original language, without translating the quote")
    status: str = Field(description="Standardized eligibility comparison value: MUST be exactly 'matches', 'does_not_match', or 'unknown'")
    reason: str = Field(description="Clear explanation in the requested language comparing candidate profile with criterion")
    label: str = Field(default="from_notice", description="Trust label: 'from_notice'")


class DocumentItem(BaseModel):
    text: str = Field(description="Name or description of certificate/document required in the requested language")
    label: str = Field(default="from_notice", description="Trust label: 'from_notice' or 'inferred'")


class ActionStepItem(BaseModel):
    step: int = Field(description="Sequential step number starting at 1")
    text: str = Field(description="Clear, actionable instruction for the applicant in the requested language")


class SafetyWarningItem(BaseModel):
    category: str = Field(
        description="Warning category: 'Payment Request' | 'Credential / OTP Request' | 'High Urgency Pressure' | 'Suspicious Link or Contact' | 'Sensitive Data Request' | 'General Precaution'"
    )
    evidence: str = Field(
        default="",
        description="Exact verbatim excerpt from the original notice text in its original language triggering this warning. If no specific quote exists, leave empty."
    )
    explanation: str = Field(
        description="Clear, objective explanation in the requested language explaining the reason for caution without unconditionally declaring fraud"
    )
    next_step: str = Field(
        description="Practical, safe verification recommendation for the candidate in the requested language"
    )


class OpportunityAnalysis(BaseModel):
    title: str = Field(description="Official or descriptive title of the opportunity in the requested language")
    opportunity_type: str = Field(description="Category: scholarship | government_scheme | job | internship | training")
    summary: str = Field(description="Plain-language explanation of what is offered and who it is for in the requested language")
    benefits: List[BenefitItem] = Field(default_factory=list, description="List of benefits and entitlements")
    deadlines: List[DeadlineItem] = Field(default_factory=list, description="List of deadlines and key event dates. If no deadline exists, return empty list or describe that it is unstated.")
    eligibility: List[EligibilityItem] = Field(default_factory=list, description="Detailed eligibility criteria breakdown with evidence quotes")
    documents: List[DocumentItem] = Field(default_factory=list, description="Required documents and certificates")
    action_plan: List[ActionStepItem] = Field(default_factory=list, description="Chronological checklist of application steps")
    missing_info: List[str] = Field(default_factory=list, description="Crucial facts omitted from the notice explained in requested language (e.g. unstated deadline, fee, syllabus, official URL)")
    explicit_links: List[str] = Field(default_factory=list, description="Only URLs explicitly found verbatim in the notice text. Never invent links.")
    warnings: List[SafetyWarningItem] = Field(default_factory=list, description="Evidence-based safety cautions for suspicious or payment-related wording")
    disclaimer: str = Field(
        default="Avsar provides informational guidance only and cannot verify authentic status or make official eligibility decisions. Confirm all details on official portals.",
        description="Standard guidance disclaimer in requested language"
    )
