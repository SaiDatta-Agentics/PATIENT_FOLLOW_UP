"""
Response generator — returns clinic-approved messages per intent.
In production, call Azure OpenAI for dynamic personalisation.
"""
from app.models.models import Intent

RESPONSES = {
    Intent.TREATMENT_QUESTION: (
        "I'm glad your pain has improved. However, pain relief does not necessarily "
        "mean the underlying dental treatment is complete. Your dentist recommended a "
        "follow-up visit to continue your {treatment} treatment. Delaying may allow the "
        "problem to return or worsen. Would you like me to check available appointment times?"
    ),
    Intent.BOOK_APPOINTMENT: (
        "I'd be happy to help you book an appointment. Let me check the available slots for you."
    ),
    Intent.RESCHEDULE_APPOINTMENT: (
        "No problem — I can help you reschedule. Do you have a preferred date and time?"
    ),
    Intent.CONFIRM_APPOINTMENT: (
        "Thank you for confirming. We look forward to seeing you at your appointment."
    ),
    Intent.CANCEL_APPOINTMENT: (
        "I understand. Before I cancel, I want to mention that your dentist recommended "
        "completing your {treatment} treatment. Leaving it incomplete may allow the underlying "
        "problem to worsen. Would you like to reschedule instead?"
    ),
    Intent.PAIN_OR_SYMPTOM: (
        "I'm sorry to hear you're experiencing symptoms. I'm going to alert our clinical "
        "staff right away so they can follow up with you. If your symptoms are severe, "
        "please visit the clinic or your nearest emergency care."
    ),
    Intent.FEE_QUESTION: (
        "I understand cost is an important consideration. Let me connect you with our "
        "front-desk team who can discuss fees and payment options with you."
    ),
    Intent.PAYMENT_ISSUE: (
        "I'll pass your concern to our billing team so they can help resolve this. "
        "Someone will get back to you shortly."
    ),
    Intent.NOT_INTERESTED: (
        "I understand. We respect your decision. If you change your mind or have any "
        "concerns in the future, please don't hesitate to contact us."
    ),
    Intent.REQUEST_HUMAN: (
        "Of course — I'll have a staff member reach out to you shortly."
    ),
    Intent.NO_RESPONSE: "",
    Intent.OTHER: (
        "Thank you for your message. Let me make sure the right person at our clinic "
        "can help you with this."
    ),
}

def generate_response(intent: Intent, patient_context: dict) -> str:
    template = RESPONSES.get(intent, RESPONSES[Intent.OTHER])
    return template.format(**{k: v or "" for k, v in patient_context.items()})

def generate_initial_followup(patient_context: dict) -> str:
    return (
        f"Hello{', ' + patient_context.get('name', '') if patient_context.get('name') else ''}, "
        f"this is {patient_context.get('clinic_name', 'your dental clinic')} following up after "
        f"your recent visit. Your dentist recommended a follow-up for your "
        f"{patient_context.get('treatment', 'dental')} treatment. "
        f"Would you like to schedule your next appointment?"
    )
