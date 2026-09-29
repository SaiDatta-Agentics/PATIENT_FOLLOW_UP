from datetime import datetime, timedelta, timezone
from app.models.models import Patient, Conversation, Escalation, Appointment, FollowUpConfig, FollowUpTask, PatientStatus, Priority


def seed_data():
    now = datetime.now(timezone.utc)
    patients = [
        Patient(id=1, name="John Miller", phone="+1555100001", email="john@example.com", preferred_channel="SMS", treatment="Root Canal - Tooth #19", treatment_status="Emergency pain relief completed", last_visit=now-timedelta(days=3), follow_up_date=now-timedelta(minutes=1), follow_up_status=PatientStatus.OVERDUE.value, priority=Priority.HIGH.value, source="DEMO", notes="Pain improved after emergency access. Completion visit still required."),
        Patient(id=2, name="Maria Garcia", phone="+1555100002", email="maria@example.com", preferred_channel="SMS", treatment="Root Canal - Tooth #14", treatment_status="First stage completed", last_visit=now-timedelta(days=1), follow_up_date=now+timedelta(minutes=2), follow_up_status=PatientStatus.DUE.value, priority=Priority.MEDIUM.value, source="DEMO"),
        Patient(id=3, name="David Chen", phone="+1555100003", email="david@example.com", preferred_channel="VOICE", treatment="Crown - Tooth #8", treatment_status="Temporary crown placed", last_visit=now-timedelta(days=7), follow_up_date=now+timedelta(days=2), follow_up_status=PatientStatus.BOOKED.value, priority=Priority.LOW.value, source="DEMO"),
        Patient(id=4, name="Sarah Williams", phone="+1555100004", email="sarah@example.com", preferred_channel="SMS", treatment="Root Canal - Tooth #30", treatment_status="Emergency pulpotomy", last_visit=now-timedelta(days=5), follow_up_date=now-timedelta(days=2), follow_up_status=PatientStatus.ESCALATED.value, priority=Priority.URGENT.value, source="DEMO"),
        Patient(id=5, name="Priya Raman", phone="+1555100005", email="priya@example.com", preferred_channel="SMS", treatment="Root Canal - Tooth #3", treatment_status="Canal cleaning completed", last_visit=now-timedelta(days=2), follow_up_date=now+timedelta(hours=4), follow_up_status=PatientStatus.RESPONDED.value, priority=Priority.MEDIUM.value, source="DEMO"),
        Patient(id=6, name="Michael Brown", phone="+1555100006", email="michael@example.com", preferred_channel="SMS", treatment="Extraction follow-up - Tooth #18", treatment_status="Extraction completed", last_visit=now-timedelta(days=4), follow_up_date=now-timedelta(hours=5), follow_up_status=PatientStatus.CONTACTED.value, priority=Priority.MEDIUM.value, source="DEMO"),
        Patient(id=7, name="Aisha Patel", phone="+1555100007", email="aisha@example.com", preferred_channel="VOICE", treatment="Dental Implant - Stage 1", treatment_status="Implant placed", last_visit=now-timedelta(days=14), follow_up_date=now+timedelta(days=1), follow_up_status=PatientStatus.DUE.value, priority=Priority.MEDIUM.value, source="DEMO"),
        Patient(id=8, name="Robert Wilson", phone="+1555100008", email="robert@example.com", preferred_channel="SMS", treatment="Root Canal - Tooth #10", treatment_status="Temporary filling placed", last_visit=now-timedelta(days=9), follow_up_date=now-timedelta(days=1), follow_up_status=PatientStatus.NO_RESPONSE.value, priority=Priority.HIGH.value, source="DEMO"),
        Patient(id=9, name="Sofia Martinez", phone="+1555100009", email="sofia@example.com", preferred_channel="SMS", treatment="Deep Filling - Tooth #12", treatment_status="Restoration completed", last_visit=now-timedelta(days=6), follow_up_date=now+timedelta(days=3), follow_up_status=PatientStatus.COMPLETED.value, priority=Priority.LOW.value, source="DEMO"),
        Patient(id=10, name="James Lee", phone="+1555100010", email="james@example.com", preferred_channel="SMS", treatment="Root Canal - Tooth #21", treatment_status="Emergency dressing placed", last_visit=now-timedelta(days=2), follow_up_date=now+timedelta(hours=1), follow_up_status=PatientStatus.DUE.value, priority=Priority.HIGH.value, source="DEMO"),
        Patient(id=11, name="Emma Thompson", phone="+1555100011", email="emma@example.com", preferred_channel="VOICE", treatment="Crown - Tooth #5", treatment_status="Preparation completed", last_visit=now-timedelta(days=8), follow_up_date=now+timedelta(days=4), follow_up_status=PatientStatus.RESCHEDULED.value, priority=Priority.LOW.value, source="DEMO"),
        Patient(id=12, name="Noah Davis", phone="+1555100012", email="noah@example.com", preferred_channel="SMS", treatment="Root Canal - Tooth #28", treatment_status="Access opening completed", last_visit=now-timedelta(days=4), follow_up_date=now-timedelta(hours=2), follow_up_status=PatientStatus.OVERDUE.value, priority=Priority.HIGH.value, source="DEMO"),
    ]

    conversations = [
        Conversation(patient_id=1, channel="SMS", direction="OUTBOUND", message="Hello John, this is SaiDatta Dental Clinic. Your dentist recommended completing your root canal treatment. Would you like help scheduling the next visit?", intent="INITIAL_FOLLOWUP", agent_action="SEND_FOLLOWUP", delivery_status="SIMULATED", created_at=now-timedelta(days=2)),
        Conversation(patient_id=1, channel="SMS", direction="INBOUND", message="My tooth doesn't hurt anymore. Do I still need to come?", intent="TREATMENT_QUESTION", agent_action="EXPLAIN_TREATMENT", delivery_status="RECEIVED", created_at=now-timedelta(days=2)+timedelta(hours=1)),
        Conversation(patient_id=1, channel="SMS", direction="OUTBOUND", message="I'm glad your pain has improved. Pain relief does not necessarily mean the root canal is complete. Your dentist still recommends the completion visit to reduce the risk of reinfection. I can help you book it.", intent="TREATMENT_QUESTION", agent_action="EXPLAIN_TREATMENT", delivery_status="RECORDED", created_at=now-timedelta(days=2)+timedelta(hours=1, minutes=1)),
        Conversation(patient_id=2, channel="SMS", direction="OUTBOUND", message="Hi Maria, your follow-up is coming up. Would you like me to check appointment times?", intent="INITIAL_FOLLOWUP", agent_action="SEND_FOLLOWUP", delivery_status="SIMULATED", created_at=now-timedelta(hours=6)),
        Conversation(patient_id=5, channel="WEB", direction="INBOUND", message="Can I come tomorrow afternoon?", intent="BOOK_APPOINTMENT", agent_action="OFFER_SLOTS", delivery_status="RECEIVED", created_at=now-timedelta(hours=3)),
        Conversation(patient_id=5, channel="WEB", direction="OUTBOUND", message="I'd be happy to help you book an appointment. I can show the available times for tomorrow.", intent="BOOK_APPOINTMENT", agent_action="OFFER_SLOTS", delivery_status="WEB_REPLY", created_at=now-timedelta(hours=3)+timedelta(seconds=1)),
        Conversation(patient_id=4, channel="SMS", direction="INBOUND", message="I have severe swelling and the pain is getting worse.", intent="PAIN_OR_SYMPTOM", agent_action="ESCALATE_CLINICAL", delivery_status="RECEIVED", created_at=now-timedelta(hours=6)),
        Conversation(patient_id=8, channel="SMS", direction="OUTBOUND", message="Hello Robert, we're checking in about the temporary filling and completion of your root canal. Reply here if you'd like help scheduling.", intent="INITIAL_FOLLOWUP", agent_action="AUTO_FOLLOWUP", delivery_status="SIMULATED", created_at=now-timedelta(days=1)),
        Conversation(patient_id=10, channel="SMS", direction="INBOUND", message="How much will the next visit cost?", intent="FEE_QUESTION", agent_action="ESCALATE_FINANCIAL", delivery_status="RECEIVED", created_at=now-timedelta(minutes=40)),
        Conversation(patient_id=10, channel="SMS", direction="OUTBOUND", message="I understand cost is important. I've sent your question to the clinic team so they can give you the correct fee and payment information.", intent="FEE_QUESTION", agent_action="ESCALATE_FINANCIAL", delivery_status="RECORDED", created_at=now-timedelta(minutes=39)),
    ]

    escalations = [
        Escalation(patient_id=4, type="CLINICAL", priority="URGENT", reason="Patient reports worsening pain and swelling", patient_message="I have severe swelling and the pain is getting worse.", detected_intent="PAIN_OR_SYMPTOM", staff_summary="Sarah Williams reported severe swelling and worsening pain after emergency pulpotomy. Clinical review required.", status="OPEN", created_at=now-timedelta(hours=6)),
        Escalation(patient_id=10, type="FINANCIAL", priority="HIGH", reason="Patient asked for treatment fee", patient_message="How much will the next visit cost?", detected_intent="FEE_QUESTION", staff_summary="James Lee is due to complete root canal treatment and asked for the fee. Staff should provide verified pricing/payment options.", status="OPEN", created_at=now-timedelta(minutes=40)),
    ]

    appointments = [
        Appointment(patient_id=3, date=now+timedelta(days=2), treatment_type="Permanent Crown Placement", status="CONFIRMED"),
        Appointment(patient_id=5, date=now+timedelta(days=1, hours=2), treatment_type="Root Canal Completion", status="CONFIRMED"),
        Appointment(patient_id=11, date=now+timedelta(days=4), treatment_type="Crown Delivery", status="CONFIRMED"),
    ]

    configs = [
        FollowUpConfig(day_offset=1, action="INITIAL_FOLLOWUP", message_template="Initial post-treatment follow-up", is_active=True),
        FollowUpConfig(day_offset=3, action="SECOND_REMINDER", message_template="Second reminder if no response", is_active=True),
    ]

    tasks = [
        FollowUpTask(patient_id=1, scheduled_at=now-timedelta(days=2), channel="SMS", action="INITIAL_FOLLOWUP", status="SENT", attempt_number=1),
        FollowUpTask(patient_id=2, scheduled_at=now+timedelta(minutes=2), channel="SMS", action="INITIAL_FOLLOWUP", status="SCHEDULED"),
        FollowUpTask(patient_id=6, scheduled_at=now-timedelta(hours=5), channel="SMS", action="POST_EXTRACTION_CHECK", status="SENT", attempt_number=1),
        FollowUpTask(patient_id=7, scheduled_at=now+timedelta(days=1), channel="VOICE", action="IMPLANT_REVIEW", status="SCHEDULED"),
        FollowUpTask(patient_id=8, scheduled_at=now-timedelta(days=1), channel="SMS", action="SECOND_REMINDER", status="SENT", attempt_number=2),
        FollowUpTask(patient_id=10, scheduled_at=now+timedelta(hours=1), channel="SMS", action="INITIAL_FOLLOWUP", status="SCHEDULED"),
        FollowUpTask(patient_id=12, scheduled_at=now-timedelta(minutes=1), channel="SMS", action="INITIAL_FOLLOWUP", status="SCHEDULED"),
    ]
    return [], patients, conversations, escalations, appointments, configs, tasks
